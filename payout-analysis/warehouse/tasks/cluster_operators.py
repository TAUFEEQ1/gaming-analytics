"""
Cluster operators using DBSCAN based on movement_wager_amt
"""
import luigi
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import joblib


class ClusterOperatorsDBSCAN(luigi.Task):
    """
    Cluster operators using DBSCAN based on movement_wager_amt characteristics.
    This provides data-driven operator segmentation without arbitrary boundaries.
    """
    
    eps = luigi.FloatParameter(default=0.5)  # DBSCAN epsilon parameter
    min_samples = luigi.IntParameter(default=2)  # Minimum samples per cluster
    
    def requires(self):
        from warehouse.tasks.filter_by_sample_size import FilterBySampleSize
        return FilterBySampleSize()
    
    def output(self):
        return {
            'operator_clusters': luigi.LocalTarget('warehouse/data/operator_clusters.csv'),
            'cluster_model': luigi.LocalTarget('warehouse/data/models/dbscan_operator_clusters.pkl')
        }
    
    def run(self):
        # Load filtered data
        df = pd.read_csv(self.requires().output()['filtered_data'].path)
        
        print(f"\n=== DBSCAN Operator Clustering ===")
        print(f"Dataset: {len(df)} records")
        
        # Calculate operator-level statistics for clustering
        operator_stats = df.groupby('operator').agg({
            'movement_wager_amt': ['mean', 'median', 'std', 'count'],
            'payout_base_win': ['mean', 'median', 'std'],
            'stake_real_money': ['mean', 'median'],
            'no_of_bets': ['mean', 'median']
        }).reset_index()
        
        operator_stats.columns = ['operator', 
                                   'movement_wager_mean', 'movement_wager_median', 'movement_wager_std', 'movement_wager_count',
                                   'movement_win_mean', 'movement_win_median', 'movement_win_std',
                                   'stake_mean', 'stake_median',
                                   'no_of_bets_mean', 'no_of_bets_median']
        
        print(f"\nOperators to cluster: {len(operator_stats)}")
        
        # Use log-transformed movement amounts for clustering (handles wide range)
        # Add small constant to avoid log(0)
        operator_stats['log_movement_wager_mean'] = np.log10(operator_stats['movement_wager_mean'] + 1)
        operator_stats['log_movement_win_mean'] = np.log10(operator_stats['movement_win_mean'] + 1)
        operator_stats['log_stake_mean'] = np.log10(operator_stats['stake_mean'] + 1)
        
        # Prepare features for clustering
        # Using both movement_wager and movement_win characteristics
        clustering_features = operator_stats[['log_movement_wager_mean', 'log_movement_win_mean']].values
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(clustering_features)
        
        print(f"\nClustering features:")
        print(f"  - log10(movement_wager_amt mean)")
        print(f"  - log10(payout_base_win mean)")
        print(f"  Wager range: {operator_stats['log_movement_wager_mean'].min():.2f} to {operator_stats['log_movement_wager_mean'].max():.2f}")
        print(f"  Win range: {operator_stats['log_movement_win_mean'].min():.2f} to {operator_stats['log_movement_win_mean'].max():.2f}")
        
        # Apply DBSCAN
        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        clusters = dbscan.fit_predict(features_scaled)
        
        operator_stats['cluster'] = clusters
        
        # Analyze clusters
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        print(f"\n=== Clustering Results ===")
        print(f"Number of clusters found: {n_clusters}")
        print(f"Noise points (cluster -1): {n_noise}")
        
        # Sort clusters by mean movement_wager_amt (relabel for clarity)
        cluster_means = operator_stats[operator_stats['cluster'] != -1].groupby('cluster')['movement_wager_mean'].mean().sort_values()
        cluster_mapping = {old_label: new_label for new_label, old_label in enumerate(cluster_means.index)}
        cluster_mapping[-1] = -1  # Keep noise as -1
        
        operator_stats['cluster'] = operator_stats['cluster'].map(cluster_mapping)
        
        # Create tier names
        def assign_tier_name(cluster_id):
            if cluster_id == -1:
                return 'noise'
            elif cluster_id == 0:
                return 'low'
            elif cluster_id == n_clusters - 1:
                return 'high'
            else:
                return 'mid'
        
        operator_stats['tier'] = operator_stats['cluster'].apply(assign_tier_name)
        
        # Print cluster statistics
        print(f"\n=== Cluster Statistics ===")
        for cluster_id in sorted(operator_stats['cluster'].unique()):
            cluster_data = operator_stats[operator_stats['cluster'] == cluster_id]
            tier_name = cluster_data['tier'].iloc[0]
            
            print(f"\nCluster {cluster_id} ({tier_name.upper()}):")
            print(f"  Operators: {len(cluster_data)}")
            print(f"  Operators: {cluster_data['operator'].tolist()}")
            print(f"  Movement wager range: {cluster_data['movement_wager_mean'].min():,.0f} - {cluster_data['movement_wager_mean'].max():,.0f} UGX")
            print(f"  Movement win range: {cluster_data['movement_win_mean'].min():,.0f} - {cluster_data['movement_win_mean'].max():,.0f} UGX")
            print(f"  Mean movement wager: {cluster_data['movement_wager_mean'].mean():,.0f} UGX")
            print(f"  Mean movement win: {cluster_data['movement_win_mean'].mean():,.0f} UGX")
            print(f"  Stake range: {cluster_data['stake_mean'].min():,.0f} - {cluster_data['stake_mean'].max():,.0f} UGX")
            print(f"  Total records: {cluster_data['movement_wager_count'].sum():.0f}")
        
        # Save operator cluster assignments
        operator_clusters = operator_stats[['operator', 'cluster', 'tier', 
                                           'movement_wager_mean', 'movement_win_mean', 'stake_mean']].copy()
        operator_clusters.to_csv(self.output()['operator_clusters'].path, index=False)
        
        # Save clustering model for potential future use
        cluster_info = {
            'scaler': scaler,
            'dbscan': dbscan,
            'cluster_mapping': cluster_mapping,
            'n_clusters': n_clusters
        }
        joblib.dump(cluster_info, self.output()['cluster_model'].path)
        
        print(f"\n=== Clustering Complete ===")
        print(f"Operator clusters saved to: {self.output()['operator_clusters'].path}")
