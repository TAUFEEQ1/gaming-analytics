"""
Detect anomalies using trained hybrid models with statistical outlier detection.
"""
import luigi
import pandas as pd
import numpy as np
import joblib


class DetectAnomalies(luigi.Task):
    """
    Detect anomalies using hybrid approach:
    - Regression operators: Statistical outlier detection (90th percentile of prediction errors)
    - Anomaly operators: Isolation Forest with stake contribution analysis
    """
    
    deviation_threshold = luigi.FloatParameter(default=0.75)
    
    def requires(self):
        from warehouse.tasks.train_hybrid_models import TrainHybridModels
        from warehouse.tasks.filter_by_sample_size import FilterBySampleSize
        return {
            'models': TrainHybridModels(),
            'data': FilterBySampleSize()
        }
    
    def output(self):
        return {
            'regression_anomalies': luigi.LocalTarget('warehouse/data/regression_anomalies.csv'),
            'isolation_anomalies': luigi.LocalTarget('warehouse/data/isolation_anomalies.csv'),
            'all_anomalies': luigi.LocalTarget('warehouse/data/all_anomalies.csv'),
            'anomaly_summary': luigi.LocalTarget('warehouse/data/anomaly_summary.csv')
        }
    
    def run(self):
        # Load data
        df = pd.read_csv(self.requires()['data'].output()['filtered_data'].path)
        
        # Load models
        regression_models = joblib.load(self.requires()['models'].output()['regression_models'].path)
        anomaly_models = joblib.load(self.requires()['models'].output()['anomaly_models'].path)
        
        # Load operator classification
        classification_df = pd.read_csv(self.requires()['models'].output()['operator_classification'].path)
        regression_ops = classification_df[classification_df['model_type'] == 'regression']['operator'].tolist()
        anomaly_ops = classification_df[classification_df['model_type'] == 'anomaly_detection']['operator'].tolist()
        
        # Get tier mapping
        operator_to_tier = dict(zip(classification_df['operator'], classification_df['tier']))
        df['tier'] = df['operator'].map(operator_to_tier)
        
        print(f"\n{'='*80}")
        print("ANOMALY DETECTION")
        print(f"{'='*80}")
        print(f"Total records: {len(df):,}")
        print(f"Regression operators: {len(regression_ops)}")
        print(f"Anomaly detection operators: {len(anomaly_ops)}")
        
        # Detect regression anomalies
        print(f"\n--- Detecting Regression Anomalies ---")
        regression_anomalies = self._detect_regression_anomalies(
            df, regression_ops, regression_models, operator_to_tier
        )
        
        # Detect isolation forest anomalies
        print(f"\n--- Detecting Isolation Forest Anomalies ---")
        isolation_anomalies = self._detect_isolation_anomalies(
            df, anomaly_ops, anomaly_models
        )
        
        # Save results
        regression_anomalies.to_csv(self.output()['regression_anomalies'].path, index=False)
        isolation_anomalies.to_csv(self.output()['isolation_anomalies'].path, index=False)
        
        # Combine all anomalies
        all_anomalies = pd.concat([
            regression_anomalies[['operator', 'stake_real_money', 'anomaly_type', 'anomaly_score', 
                                  'predicted_stake', 'deviation_pct', 'stake_z_score']],
            isolation_anomalies[['operator', 'stake_real_money', 'anomaly_type', 'anomaly_score', 
                                'predicted_stake', 'deviation_pct', 'stake_z_score']]
        ], ignore_index=True)
        all_anomalies.to_csv(self.output()['all_anomalies'].path, index=False)
        
        # Create summary
        summary = self._create_summary(regression_anomalies, isolation_anomalies, df)
        summary.to_csv(self.output()['anomaly_summary'].path, index=False)
        
        print(f"\n{'='*80}")
        print("ANOMALY DETECTION COMPLETE")
        print(f"{'='*80}")
        print(f"Regression anomalies: {len(regression_anomalies):,} ({len(regression_anomalies)/len(df[df['operator'].isin(regression_ops)])*100:.1f}%)")
        print(f"Isolation anomalies: {len(isolation_anomalies):,} ({len(isolation_anomalies)/len(df[df['operator'].isin(anomaly_ops)])*100:.1f}%)")
        print(f"Total anomalies: {len(all_anomalies):,} ({len(all_anomalies)/len(df)*100:.1f}%)")
        print(f"\n✓ Results saved to: warehouse/data/all_anomalies.csv")
    
    def _detect_regression_anomalies(self, df, regression_ops, regression_models, operator_to_tier):
        """Detect anomalies in regression operators using statistical outlier detection"""
        df_reg = df[df['operator'].isin(regression_ops)].copy()
        df_encoded = pd.get_dummies(df_reg, columns=['operator', 'game_type'], drop_first=False)
        
        # Load operator R² scores
        classification = pd.read_csv('warehouse/data/operator_classification.csv')
        r2_scores = dict(zip(classification['operator'], classification['r2_score']))
        
        anomalies = []
        
        for operator in regression_ops:
            tier = operator_to_tier[operator]
            
            if tier not in regression_models:
                continue
            
            model_info = regression_models[tier]
            model = model_info['model']
            feature_cols = model_info['feature_cols']
            
            op_data = df_encoded[df_encoded[f'operator_{operator}'] == 1].copy()
            
            if len(op_data) == 0:
                continue
            
            X = op_data[feature_cols]
            y_true = op_data['stake_real_money']
            y_pred = model.predict(X)
            
            # Calculate deviations
            deviations = np.abs((y_true - y_pred) / y_pred)
            
            # Statistical outlier detection: Flag top 10% worst predictions
            # Adapts to each operator's actual error distribution
            percentile_threshold = np.percentile(deviations, 90)
            adaptive_threshold = max(self.deviation_threshold, percentile_threshold)
            
            # Flag anomalies
            anomaly_mask = deviations > adaptive_threshold
            
            r2 = r2_scores.get(operator, 0.75)
            
            for idx in op_data[anomaly_mask].index:
                anomalies.append({
                    'operator': operator,
                    'tier': tier,
                    'stake_real_money': y_true.loc[idx],
                    'predicted_stake': y_pred[op_data.index.get_loc(idx)],
                    'deviation_pct': deviations.loc[idx],
                    'deviation_threshold_used': adaptive_threshold,
                    'r2_score': r2,
                    'anomaly_type': 'regression_deviation',
                    'anomaly_score': -deviations.loc[idx],  # Negative for consistency
                    'stake_z_score': None
                })
        
        print(f"  Found {len(anomalies)} regression anomalies")
        return pd.DataFrame(anomalies)
    
    def _detect_isolation_anomalies(self, df, anomaly_ops, anomaly_models):
        """Detect anomalies using Isolation Forest and calculate stake contribution"""
        df_anom = df[df['operator'].isin(anomaly_ops)].copy()
        df_encoded = pd.get_dummies(df_anom, columns=['game_type'], drop_first=False)
        
        anomalies = []
        
        for operator in anomaly_ops:
            if operator not in anomaly_models:
                continue
            
            model_info = anomaly_models[operator]
            model = model_info['model']
            scaler = model_info['scaler']
            feature_cols = model_info['feature_cols']
            
            op_data = df_encoded[df_encoded['operator'] == operator].copy()
            
            if len(op_data) == 0:
                continue
            
            X = op_data[feature_cols].fillna(0)
            X_scaled = scaler.transform(X)
            
            # Predict anomalies
            predictions = model.predict(X_scaled)
            scores = model.score_samples(X_scaled)
            
            # Get anomalies
            anomaly_mask = predictions == -1
            
            if anomaly_mask.sum() == 0:
                continue
            
            # Calculate stake z-scores for anomalies
            normal_mask = predictions == 1
            if normal_mask.sum() > 0:
                normal_stakes = op_data.loc[normal_mask, 'stake_real_money']
                normal_mean = normal_stakes.mean()
                normal_std = normal_stakes.std()
                
                for idx in op_data[anomaly_mask].index:
                    stake_val = op_data.loc[idx, 'stake_real_money']
                    stake_z_score = (stake_val - normal_mean) / normal_std if normal_std > 0 else 0
                    
                    anomalies.append({
                        'operator': operator,
                        'tier': df.loc[df['operator'] == operator, 'tier'].iloc[0],
                        'stake_real_money': stake_val,
                        'predicted_stake': normal_mean,
                        'deviation_pct': abs((stake_val - normal_mean) / normal_mean) if normal_mean > 0 else 0,
                        'anomaly_type': 'isolation_forest',
                        'anomaly_score': scores[op_data.index.get_loc(idx)],
                        'stake_z_score': stake_z_score
                    })
        
        print(f"  Found {len(anomalies)} isolation forest anomalies")
        return pd.DataFrame(anomalies)
    
    def _create_summary(self, regression_anomalies, isolation_anomalies, df):
        """Create summary statistics by operator"""
        summary_data = []
        
        for operator in df['operator'].unique():
            reg_anom = regression_anomalies[regression_anomalies['operator'] == operator]
            iso_anom = isolation_anomalies[isolation_anomalies['operator'] == operator]
            
            total_records = len(df[df['operator'] == operator])
            total_anomalies = len(reg_anom) + len(iso_anom)
            
            summary_data.append({
                'operator': operator,
                'total_records': total_records,
                'regression_anomalies': len(reg_anom),
                'isolation_anomalies': len(iso_anom),
                'total_anomalies': total_anomalies,
                'anomaly_rate': total_anomalies / total_records if total_records > 0 else 0
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('anomaly_rate', ascending=False)
        
        return summary_df
