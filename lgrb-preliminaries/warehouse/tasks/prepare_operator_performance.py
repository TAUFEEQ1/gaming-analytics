"""
Prepare operator-level performance data for real-time querying.

This task creates a parquet file with:
- Granularity: Operator × Day × Game Category
- Raw metrics (not pre-computed aggregations)
- Operator tier assignments from DBSCAN clustering (based on movement_wager_amt)

Enables queries like:
- Top/bottom performers by GGR in any timeframe
- Category performance analysis
- Peer comparisons within operator tiers
"""
import luigi
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


class PrepareOperatorPerformance(luigi.Task):
    """
    Prepare operator-level performance data at day × category granularity.
    Performs DBSCAN tier assignments based on movement_wager_amt for fair peer comparison.
    """
    
    def output(self):
        return {
            'operator_performance': luigi.LocalTarget('warehouse/data/operator_performance.parquet'),
            'summary': luigi.LocalTarget('warehouse/data/operator_performance_summary.txt')
        }
    
    def run(self):
        # Load raw dataset
        df = pd.read_csv('lotterries_plain_dataset.csv')
        
        print(f"\n{'='*80}")
        print("PREPARING OPERATOR PERFORMANCE DATA")
        print(f"{'='*80}")
        print(f"Total records: {len(df):,}")
        
        # Filter for gameSummary entries only
        df = df[df['source_type'] == 'gameSummary'].copy()
        print(f"GameSummary records: {len(df):,}")
        
        # Convert timestamp_end to datetime and extract date
        df['timestamp_end'] = pd.to_datetime(df['timestamp_end'])
        df['date'] = df['timestamp_end'].dt.date
        df['date'] = pd.to_datetime(df['date'])
        
        # Use existing GGR column (already calculated in data)
        # GGR = stake_real_money - payout_base_win
        
        # Aggregate by operator + date + game_category
        print("\nAggregating by operator × date × game_category...")
        operator_perf = df.groupby(['operator', 'date', 'game_category'], as_index=False).agg({
            'GGR': 'sum',
            'stake_real_money': 'sum',
            'payout_base_win': 'sum',
            'no_of_bets': 'sum'
        })
        
        # Rename for clarity
        operator_perf.rename(columns={
            'stake_real_money': 'total_stake',
            'payout_base_win': 'total_payout',
            'no_of_bets': 'total_bets'
        }, inplace=True)
        
        print(f"Aggregated records: {len(operator_perf):,}")
        print(f"Unique operators: {operator_perf['operator'].nunique()}")
        print(f"Unique dates: {operator_perf['date'].nunique()}")
        print(f"Unique categories: {operator_perf['game_category'].nunique()}")
        
        # Calculate operator-level statistics for tier assignment using movement_wager_amt
        print("\nCalculating operator tiers using DBSCAN on movement_wager_amt...")
        
        # Aggregate movement fields by operator from raw data
        operator_stats = df.groupby('operator', as_index=False).agg({
            'movement_wager_amt': ['mean', 'median', 'std', 'sum'],
            'movement_win_amt': ['mean', 'median'],
            'stake_real_money': ['mean', 'sum']
        })
        
        operator_stats.columns = ['operator', 
                                   'movement_wager_mean', 'movement_wager_median', 'movement_wager_std', 'movement_wager_sum',
                                   'movement_win_mean', 'movement_win_median',
                                   'stake_mean', 'stake_sum']
        
        print(f"Operators for clustering: {len(operator_stats)}")
        
        # Use log-transformed movement amounts for clustering (handles wide range)
        operator_stats['log_movement_wager_mean'] = np.log10(operator_stats['movement_wager_mean'] + 1)
        operator_stats['log_movement_win_mean'] = np.log10(operator_stats['movement_win_mean'] + 1)
        
        # Prepare features for clustering
        clustering_features = operator_stats[['log_movement_wager_mean', 'log_movement_win_mean']].values
        
        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(clustering_features)
        
        # Apply DBSCAN with tighter eps for more granular clusters
        dbscan = DBSCAN(eps=0.3, min_samples=2)
        clusters = dbscan.fit_predict(features_scaled)
        operator_stats['cluster'] = clusters
        
        # Analyze clusters
        n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
        n_noise = list(clusters).count(-1)
        
        print(f"  Clusters found: {n_clusters}")
        print(f"  Noise points: {n_noise}")
        
        # Sort clusters by mean movement_wager_amt and assign tier names
        if n_clusters > 0:
            cluster_means = operator_stats[operator_stats['cluster'] != -1].groupby('cluster')['movement_wager_mean'].mean().sort_values()
            cluster_mapping = {old_label: new_label for new_label, old_label in enumerate(cluster_means.index)}
            cluster_mapping[-1] = -1  # Keep noise as -1
            operator_stats['cluster'] = operator_stats['cluster'].map(cluster_mapping)
            
            # Assign tier names based on both DBSCAN clusters and percentiles
            def assign_tier_name(row):
                cluster_id = row['cluster']
                wager = row['movement_wager_mean']
                
                # Use percentiles for more granular tiers
                p95 = operator_stats['movement_wager_mean'].quantile(0.95)
                p85 = operator_stats['movement_wager_mean'].quantile(0.85)
                p70 = operator_stats['movement_wager_mean'].quantile(0.70)
                p50 = operator_stats['movement_wager_mean'].quantile(0.50)
                p30 = operator_stats['movement_wager_mean'].quantile(0.30)
                p15 = operator_stats['movement_wager_mean'].quantile(0.15)
                
                # Assign tiers based on wager size (regardless of DBSCAN cluster)
                if wager >= p95:
                    return 'Top Tier'
                elif wager >= p85:
                    return 'Large+'
                elif wager >= p70:
                    return 'Large'
                elif wager >= p50:
                    return 'Medium+'
                elif wager >= p30:
                    return 'Medium'
                elif wager >= p15:
                    return 'Small'
                else:
                    return 'Micro'
            
            operator_stats['operator_tier'] = operator_stats.apply(assign_tier_name, axis=1)
        else:
            # Fallback if DBSCAN doesn't find clusters - use percentiles
            print("  DBSCAN found no clusters, using percentile-based tiers...")
            p75 = operator_stats['movement_wager_mean'].quantile(0.75)
            p25 = operator_stats['movement_wager_mean'].quantile(0.25)
            
            def assign_tier_by_percentile(wager):
                if wager >= p75:
                    return 'Large'
                elif wager >= p25:
                    return 'Medium'
                else:
                    return 'Small'
            
            operator_stats['operator_tier'] = operator_stats['movement_wager_mean'].apply(assign_tier_by_percentile)
        
        # Print tier distribution
        print(f"\nTier assignments based on movement_wager_amt:")
        for tier, count in operator_stats['operator_tier'].value_counts().items():
            tier_data = operator_stats[operator_stats['operator_tier'] == tier]
            print(f"  {tier}: {count} operators (wager range: {tier_data['movement_wager_mean'].min():,.0f} - {tier_data['movement_wager_mean'].max():,.0f})")
        
        # Merge tier assignments to performance data
        tier_mapping = operator_stats[['operator', 'operator_tier', 'movement_wager_mean']].copy()
        operator_perf = operator_perf.merge(tier_mapping, on='operator', how='left')
        
        # Fill missing tiers as Unclassified
        operator_perf['operator_tier'].fillna('Unclassified', inplace=True)
        
        # Sort by date and operator for efficient querying
        operator_perf = operator_perf.sort_values(['date', 'operator', 'game_category'])
        
        # Save as parquet for efficient columnar queries
        output_path = Path(self.output()['operator_performance'].path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        operator_perf.to_parquet(output_path, index=False, compression='snappy')
        
        # Generate summary statistics
        summary_lines = []
        summary_lines.append("="*80)
        summary_lines.append("OPERATOR PERFORMANCE DATA SUMMARY")
        summary_lines.append("="*80)
        summary_lines.append(f"\nData Structure:")
        summary_lines.append(f"  Granularity: Operator × Day × Game Category")
        summary_lines.append(f"  Total records: {len(operator_perf):,}")
        summary_lines.append(f"  File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        summary_lines.append(f"\nDimensions:")
        summary_lines.append(f"  Unique operators: {operator_perf['operator'].nunique()}")
        summary_lines.append(f"  Date range: {operator_perf['date'].min()} to {operator_perf['date'].max()}")
        summary_lines.append(f"  Days covered: {operator_perf['date'].nunique()}")
        summary_lines.append(f"  Game categories: {sorted(operator_perf['game_category'].unique())}")
        
        summary_lines.append(f"\nOperator Tiers:")
        tier_counts = operator_perf.groupby('operator_tier')['operator'].nunique()
        for tier, count in tier_counts.items():
            summary_lines.append(f"  {tier}: {count} operators")
        
        summary_lines.append(f"\nMetrics Available:")
        summary_lines.append(f"  • GGR (primary performance metric)")
        summary_lines.append(f"  • total_stake (betting volume)")
        summary_lines.append(f"  • total_payout (payout amount)")
        summary_lines.append(f"  • total_bets (transaction count)")
        summary_lines.append(f"  • operator_tier (for peer comparison)")
        
        summary_lines.append(f"\nGGR Statistics:")
        summary_lines.append(f"  Total GGR: UGX {operator_perf['GGR'].sum():,.0f}")
        summary_lines.append(f"  Average daily GGR per operator: UGX {operator_perf.groupby(['operator', 'date'])['GGR'].sum().mean():,.0f}")
        summary_lines.append(f"  Median GGR (operator-day-category): UGX {operator_perf['GGR'].median():,.0f}")
        
        summary_lines.append(f"\nTop 5 Operators by Total GGR:")
        top_operators = operator_perf.groupby('operator').agg({
            'GGR': 'sum',
            'operator_tier': 'first',
            'movement_wager_mean': 'first'
        }).nlargest(5, 'GGR')
        for i, (op, row) in enumerate(top_operators.iterrows(), 1):
            summary_lines.append(f"  {i}. {op} ({row['operator_tier']}, Wager: {row['movement_wager_mean']:,.0f}): GGR UGX {row['GGR']:,.0f}")
        
        summary_lines.append(f"\nTop 5 Game Categories by Total GGR:")
        top_categories = operator_perf.groupby('game_category')['GGR'].sum().nlargest(5)
        for i, (cat, ggr) in enumerate(top_categories.items(), 1):
            summary_lines.append(f"  {i}. {cat}: UGX {ggr:,.0f}")
        
        summary_lines.append(f"\nQuery Examples:")
        summary_lines.append(f"  # Load data")
        summary_lines.append(f"  df = pd.read_parquet('warehouse/data/operator_performance.parquet')")
        summary_lines.append(f"  ")
        summary_lines.append(f"  # Top 10 operators in Q4 2025")
        summary_lines.append(f"  q4 = df[(df['date'] >= '2025-10-01') & (df['date'] <= '2025-12-31')]")
        summary_lines.append(f"  top10 = q4.groupby('operator')['GGR'].sum().nlargest(10)")
        summary_lines.append(f"  ")
        summary_lines.append(f"  # Compare within tier (peer comparison)")
        summary_lines.append(f"  medium_tier = df[df['operator_tier'] == 'Medium']")
        summary_lines.append(f"  medium_perf = medium_tier.groupby('operator')['GGR'].agg(['sum', 'mean', 'median'])")
        summary_lines.append(f"  medium_perf['z_score'] = (medium_perf['sum'] - medium_perf['sum'].mean()) / medium_perf['sum'].std()")
        summary_lines.append(f"  ")
        summary_lines.append(f"  # Top categories by operator")
        summary_lines.append(f"  operator_x = df[df['operator'] == 'OperatorX']")
        summary_lines.append(f"  top_cats = operator_x.groupby('game_category')['GGR'].sum().nlargest(3)")
        
        summary_lines.append("\n" + "="*80)
        
        # Write summary
        with open(self.output()['summary'].path, 'w') as f:
            f.write('\n'.join(summary_lines))
        
        print("\n" + '\n'.join(summary_lines))
        print(f"\n✅ Operator performance data saved to: {output_path}")


if __name__ == '__main__':
    luigi.build([PrepareOperatorPerformance()], local_scheduler=True)
