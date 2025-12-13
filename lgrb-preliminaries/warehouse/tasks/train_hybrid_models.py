"""
Train dual models for all operators: Regression for context + Isolation Forest for anomaly detection.

Strategy:
- Regression models provide expected stake baseline (contextual information)
- Isolation Forest flags anomalies (multivariate outlier detection)
- Both outputs reported to decision maker - no automatic anomaly flagging by regression
"""
import luigi
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.cluster import DBSCAN
import joblib
from pathlib import Path


class TrainHybridModels(luigi.Task):
    """
    Train both regression and isolation forest for ALL operators:
    - Tier-based Linear Regression: Provides expected stake for context
    - Per-operator Isolation Forest: Flags multivariate anomalies
    """
    
    random_state = luigi.IntParameter(default=42)
    
    def requires(self):
        from warehouse.tasks.filter_by_sample_size import FilterBySampleSize
        return FilterBySampleSize()
    
    def output(self):
        return {
            'regression_models': luigi.LocalTarget('warehouse/data/models/regression_models.pkl'),
            'anomaly_models': luigi.LocalTarget('warehouse/data/models/anomaly_models.pkl'),
            'operator_classification': luigi.LocalTarget('warehouse/data/operator_classification.csv'),
            'model_performance': luigi.LocalTarget('warehouse/data/hybrid_model_performance.csv')
        }
    
    def run(self):
        # Load data
        df = pd.read_csv(self.requires().output()['filtered_data'].path)
        
        print(f"\n{'='*80}")
        print("HYBRID MODEL TRAINING")
        print(f"{'='*80}")
        print(f"Total records: {len(df):,}")
        print(f"Operators: {df['operator'].nunique()}")
        
        # Step 1: Assign operators to tiers using DBSCAN
        print(f"\n--- Step 1: Operator Tier Assignment ---")
        operator_to_tier = self._assign_tiers(df)
        df['tier'] = df['operator'].map(operator_to_tier)
        
        # Step 2: Evaluate R² for each operator (for reporting only)
        print(f"\n--- Step 2: Evaluate Operator Performance ---")
        operator_r2_scores = self._evaluate_operators(df)
        
        # Step 3: Train regression models for ALL operators (contextual information)
        print(f"\n--- Step 3: Train Tier-Based Regression Models (All Operators) ---")
        all_operators = list(df['operator'].unique())
        regression_models = self._train_regression_models(df, all_operators)
        
        # Step 4: Train Isolation Forest for ALL operators (anomaly detection)
        print(f"\n--- Step 4: Train Isolation Forest Models (All Operators) ---")
        anomaly_models = self._train_anomaly_models(df, all_operators)
        
        # Save models
        Path('warehouse/data/models').mkdir(parents=True, exist_ok=True)
        joblib.dump(regression_models, self.output()['regression_models'].path)
        joblib.dump(anomaly_models, self.output()['anomaly_models'].path)
        
        # Save operator info - all operators now have both models
        classification_df = pd.DataFrame([
            {
                'operator': op,
                'tier': operator_to_tier[op],
                'r2_score': operator_r2_scores[op],
                'has_regression': True,
                'has_isolation_forest': True
            }
            for op in all_operators
        ])
        classification_df = classification_df.sort_values('r2_score', ascending=False)
        classification_df.to_csv(self.output()['operator_classification'].path, index=False)
        
        # Save performance metrics
        performance_df = pd.DataFrame([
            {
                'operator': op,
                'tier': operator_to_tier[op],
                'r2_score': operator_r2_scores[op],
                'n_samples': len(df[df['operator'] == op])
            }
            for op in all_operators
        ])
        performance_df = performance_df.sort_values('r2_score', ascending=False)
        performance_df.to_csv(self.output()['model_performance'].path, index=False)
        
        print(f"\n{'='*80}")
        print("TRAINING COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Regression models: {len(regression_models)} tiers (all operators)")
        print(f"✓ Isolation Forest models: {len(anomaly_models)} operators")
        print(f"✓ All operators have both models for dual reporting")
        print(f"✓ Files saved to: warehouse/data/")
    
    def _assign_tiers(self, df):
        """Assign operators to tiers using DBSCAN on movement features"""
        operator_stats = df.groupby('operator').agg({
            'movement_wager_amt': 'mean',
            'movement_win_amt': 'mean'
        }).reset_index()
        
        operator_stats.columns = ['operator', 'movement_wager_mean', 'movement_win_mean']
        
        # Separate zero and non-zero
        zero_ops = operator_stats[
            (operator_stats['movement_wager_mean'] == 0) | 
            (operator_stats['movement_win_mean'] == 0)
        ]['operator'].tolist()
        
        non_zero_ops = operator_stats[
            (operator_stats['movement_wager_mean'] > 0) & 
            (operator_stats['movement_win_mean'] > 0)
        ].copy()
        
        # Cluster non-zero operators
        if len(non_zero_ops) > 0:
            non_zero_ops['log_wager'] = np.log10(non_zero_ops['movement_wager_mean'])
            non_zero_ops['log_win'] = np.log10(non_zero_ops['movement_win_mean'])
            
            clustering_features = non_zero_ops[['log_wager', 'log_win']].values
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(clustering_features)
            
            dbscan = DBSCAN(eps=0.3, min_samples=2)
            clusters = dbscan.fit_predict(features_scaled)
            non_zero_ops['cluster'] = clusters
            
            # Assign tier names
            cluster_means = non_zero_ops[non_zero_ops['cluster'] >= 0].groupby('cluster')['movement_wager_mean'].mean()
            cluster_order = cluster_means.sort_values().index.tolist()
            
            tier_names = ['low', 'mid', 'high', 'very_high']
            cluster_to_tier = {cluster_order[i]: tier_names[min(i, len(tier_names)-1)] 
                              for i in range(len(cluster_order))}
            cluster_to_tier[-1] = 'noise'
            
            non_zero_ops['tier'] = non_zero_ops['cluster'].map(cluster_to_tier)
            operator_to_tier = dict(zip(non_zero_ops['operator'], non_zero_ops['tier']))
        else:
            operator_to_tier = {}
        
        # Add zero operators
        for op in zero_ops:
            operator_to_tier[op] = 'zero'
        
        return operator_to_tier
    
    def _evaluate_operators(self, df):
        """Evaluate R² for each operator using tier-based regression"""
        df_encoded = pd.get_dummies(df, columns=['operator', 'game_type'], drop_first=False)
        feature_cols = [col for col in df_encoded.columns 
                       if col not in ['stake_real_money', 'tier', 'timestamp_end']]
        
        operator_r2_scores = {}
        
        for operator in df['operator'].unique():
            op_data = df_encoded[df_encoded[f'operator_{operator}'] == 1].copy()
            
            if len(op_data) < 20:
                operator_r2_scores[operator] = -999  # Insufficient data
                continue
            
            X = op_data[feature_cols]
            y = op_data['stake_real_money']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            
            operator_r2_scores[operator] = r2
        
        return operator_r2_scores
    
    def _train_regression_models(self, df, regression_ops):
        """Train tier-based regression models"""
        df_reg = df[df['operator'].isin(regression_ops)].copy()
        df_encoded = pd.get_dummies(df_reg, columns=['operator', 'game_type'], drop_first=False)
        
        feature_cols = [col for col in df_encoded.columns 
                       if col not in ['stake_real_money', 'tier', 'timestamp_end']]
        
        tier_models = {}
        
        for tier in df_reg['tier'].unique():
            tier_data = df_encoded[df_encoded['tier'] == tier].copy()
            
            if len(tier_data) < 10:
                continue
            
            X = tier_data[feature_cols]
            y = tier_data['stake_real_money']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=self.random_state
            )
            
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            test_r2 = r2_score(y_test, model.predict(X_test))
            
            tier_models[tier] = {
                'model': model,
                'feature_cols': feature_cols,
                'test_r2': test_r2
            }
            
            print(f"  {tier}: R²={test_r2:.4f}, n={len(tier_data)}")
        
        return tier_models
    
    def _train_anomaly_models(self, df, anomaly_ops):
        """Train per-operator Isolation Forest models"""
        df_anom = df[df['operator'].isin(anomaly_ops)].copy()
        df_encoded = pd.get_dummies(df_anom, columns=['game_type'], drop_first=False)
        
        feature_cols = [col for col in df_encoded.columns 
                       if col not in ['operator', 'tier', 'timestamp_end']]
        
        anomaly_models = {}
        
        for operator in anomaly_ops:
            op_data = df_encoded[df_encoded['operator'] == operator].copy()
            
            if len(op_data) < 20:
                continue
            
            X = op_data[feature_cols].fillna(0)
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            iso_forest = IsolationForest(
                contamination=0.1,
                random_state=self.random_state,
                n_estimators=100
            )
            iso_forest.fit(X_scaled)
            
            anomaly_models[operator] = {
                'model': iso_forest,
                'scaler': scaler,
                'feature_cols': feature_cols
            }
            
            print(f"  {operator}: n={len(op_data)}")
        
        return anomaly_models
