"""
Detect anomalies using Isolation Forest with regression predictions as context.

For all operators:
- Isolation Forest flags anomalies (primary detection method)
- Regression provides expected stake baseline (contextual information)
- Both outputs reported together for decision maker
"""
import luigi
import pandas as pd
import numpy as np
import joblib


class DetectAnomalies(luigi.Task):
    """
    Detect anomalies using Isolation Forest for ALL operators.
    Regression predictions included as contextual information only.
    """
    
    def requires(self):
        from warehouse.tasks.train_hybrid_models import TrainHybridModels
        from warehouse.tasks.filter_by_sample_size import FilterBySampleSize
        return {
            'models': TrainHybridModels(),
            'data': FilterBySampleSize()
        }
    
    def output(self):
        return {
            'anomalies_with_context': luigi.LocalTarget('warehouse/data/anomalies_with_context.csv'),
            'anomaly_summary': luigi.LocalTarget('warehouse/data/anomaly_summary.csv')
        }
    
    def run(self):
        # Load data
        df = pd.read_csv(self.requires()['data'].output()['filtered_data'].path)
        
        # Load models
        regression_models = joblib.load(self.requires()['models'].output()['regression_models'].path)
        anomaly_models = joblib.load(self.requires()['models'].output()['anomaly_models'].path)
        
        # Load operator info
        classification_df = pd.read_csv(self.requires()['models'].output()['operator_classification'].path)
        all_operators = classification_df['operator'].tolist()
        operator_to_tier = dict(zip(classification_df['operator'], classification_df['tier']))
        r2_scores = dict(zip(classification_df['operator'], classification_df['r2_score']))
        
        df['tier'] = df['operator'].map(operator_to_tier)
        
        print(f"\n{'='*80}")
        print("ANOMALY DETECTION WITH CONTEXTUAL REPORTING")
        print(f"{'='*80}")
        print(f"Total records: {len(df):,}")
        print(f"Operators: {len(all_operators)}")
        print(f"\nStrategy: Isolation Forest for anomaly detection")
        print(f"          Regression for contextual baseline")
        
        # Detect anomalies with full context
        print(f"\n--- Detecting Anomalies (All Operators) ---")
        anomalies_with_context = self._detect_anomalies_with_context(
            df, all_operators, regression_models, anomaly_models, operator_to_tier, r2_scores
        )
        
        # Save results
        anomalies_with_context.to_csv(self.output()['anomalies_with_context'].path, index=False)
        
        # Create summary
        summary = self._create_summary(anomalies_with_context, df, all_operators)
        summary.to_csv(self.output()['anomaly_summary'].path, index=False)
        
        print(f"\n{'='*80}")
        print("ANOMALY DETECTION COMPLETE")
        print(f"{'='*80}")
        print(f"Total anomalies flagged: {len(anomalies_with_context):,} ({len(anomalies_with_context)/len(df)*100:.1f}%)")
        print(f"Each record includes:")
        print(f"  - Isolation Forest anomaly flag (primary)")
        print(f"  - Regression baseline prediction (context)")
        print(f"  - Deviation from expected (context)")
        print(f"  - Stake z-score (contribution)")
        print(f"\n✓ Results saved to: warehouse/data/anomalies_with_context.csv")
    
    def _detect_anomalies_with_context(self, df, all_operators, regression_models, anomaly_models, operator_to_tier, r2_scores):
        """
        Detect anomalies using Isolation Forest, with regression predictions as context.
        
        Returns records flagged as anomalies with:
        - Anomaly flag (from Isolation Forest)
        - Expected stake (from regression)
        - Deviation from expected
        - Stake contribution (z-score)
        """
        anomalies = []
        
        for operator in all_operators:
            tier = operator_to_tier[operator]
            
            # Check if operator has both models
            if tier not in regression_models or operator not in anomaly_models:
                print(f"  Warning: {operator} missing models, skipping")
                continue
            
            # Get operator data
            op_data = df[df['operator'] == operator].copy()
            if len(op_data) == 0:
                continue
            
            # 1. Get regression predictions (context)
            df_reg_encoded = pd.get_dummies(op_data, columns=['operator', 'game_type'], drop_first=False)
            regression_info = regression_models[tier]
            regression_model = regression_info['model']
            feature_cols = regression_info['feature_cols']
            
            # Ensure all expected columns are present
            for col in feature_cols:
                if col not in df_reg_encoded.columns:
                    df_reg_encoded[col] = 0
            
            X_reg = df_reg_encoded[feature_cols]
            predicted_stakes = regression_model.predict(X_reg)
            
            # 2. Run Isolation Forest (anomaly detection)
            anomaly_info = anomaly_models[operator]
            iso_model = anomaly_info['model']
            scaler = anomaly_info['scaler']
            iso_feature_cols = anomaly_info['feature_cols']
            
            df_iso_encoded = pd.get_dummies(op_data, columns=['game_type'], drop_first=False)
            
            # Ensure all expected columns are present
            for col in iso_feature_cols:
                if col not in df_iso_encoded.columns:
                    df_iso_encoded[col] = 0
            
            X_iso = df_iso_encoded[iso_feature_cols].fillna(0)
            X_iso_scaled = scaler.transform(X_iso)
            
            predictions = iso_model.predict(X_iso_scaled)
            anomaly_scores = iso_model.score_samples(X_iso_scaled)
            
            # 3. Calculate stake z-scores
            normal_mask = predictions == 1
            if normal_mask.sum() > 0:
                normal_stakes = op_data.loc[normal_mask, 'stake_real_money']
                normal_mean = normal_stakes.mean()
                normal_std = normal_stakes.std()
            else:
                normal_mean = op_data['stake_real_money'].mean()
                normal_std = op_data['stake_real_money'].std()
            
            # 4. Build results for anomalies only
            anomaly_mask = predictions == -1
            for i, idx in enumerate(op_data.index):
                if not anomaly_mask[i]:
                    continue
                
                stake_val = op_data.loc[idx, 'stake_real_money']
                predicted_stake = predicted_stakes[i]
                deviation = abs((stake_val - predicted_stake) / predicted_stake) if predicted_stake > 0 else 0
                stake_z_score = (stake_val - normal_mean) / normal_std if normal_std > 0 else 0
                
                anomalies.append({
                    'operator': operator,
                    'tier': tier,
                    'stake_real_money': stake_val,
                    'expected_stake_regression': predicted_stake,
                    'regression_r2': r2_scores.get(operator, 0),
                    'deviation_pct': deviation,
                    'anomaly_score_if': anomaly_scores[i],
                    'stake_z_score': stake_z_score,
                    'anomaly_flagged_by': 'isolation_forest'
                })
            
            print(f"  {operator}: {anomaly_mask.sum()}/{len(op_data)} flagged ({anomaly_mask.sum()/len(op_data)*100:.1f}%)")
        
        print(f"\n  Total anomalies: {len(anomalies)}")
        return pd.DataFrame(anomalies)
    
    def _create_summary(self, anomalies_df, df, all_operators):
        """Create summary statistics by operator"""
        summary_data = []
        
        for operator in all_operators:
            op_anomalies = anomalies_df[anomalies_df['operator'] == operator]
            total_records = len(df[df['operator'] == operator])
            
            if total_records > 0:
                summary_data.append({
                    'operator': operator,
                    'total_records': total_records,
                    'anomalies_flagged': len(op_anomalies),
                    'anomaly_rate': len(op_anomalies) / total_records,
                    'median_deviation_pct': op_anomalies['deviation_pct'].median() if len(op_anomalies) > 0 else 0,
                    'median_stake_z_score': op_anomalies['stake_z_score'].median() if len(op_anomalies) > 0 else 0
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('anomaly_rate', ascending=False)
        
        return summary_df
