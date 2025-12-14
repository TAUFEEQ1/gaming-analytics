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
            'anomaly_summary': luigi.LocalTarget('warehouse/data/anomaly_summary.csv'),
            'operator_flags': luigi.LocalTarget('warehouse/data/anomaly_flags_by_operator.csv'),
            'game_type_flags': luigi.LocalTarget('warehouse/data/anomaly_flags_by_game_type.csv')
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
        
        # Create summary with operator and game type flags
        summary = self._create_summary(anomalies_with_context, df, all_operators)
        summary.to_csv(self.output()['anomaly_summary'].path, index=False)
        
        # Create anomaly flags by operator and game type
        operator_flags = self._create_operator_flags(anomalies_with_context, df)
        operator_flags.to_csv(self.output()['operator_flags'].path, index=False)
        
        game_type_flags = self._create_game_type_flags(anomalies_with_context, df)
        game_type_flags.to_csv(self.output()['game_type_flags'].path, index=False)
        
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
            
            # 3. Calculate payout z-scores
            normal_mask = predictions == 1
            if normal_mask.sum() > 0:
                normal_payouts = op_data.loc[normal_mask, 'payout_base_win']
                normal_mean = normal_payouts.mean()
                normal_std = normal_payouts.std()
            else:
                normal_mean = op_data['payout_base_win'].mean()
                normal_std = op_data['payout_base_win'].std()
            
            # 4. Build results for anomalies only
            anomaly_mask = predictions == -1
            for i, idx in enumerate(op_data.index):
                if not anomaly_mask[i]:
                    continue
                
                payout_val = op_data.loc[idx, 'payout_base_win']
                predicted_payout = predicted_stakes[i]
                deviation = abs((payout_val - predicted_payout) / predicted_payout) if predicted_payout > 0 else 0
                payout_z_score = (payout_val - normal_mean) / normal_std if normal_std > 0 else 0
                
                row_data = op_data.loc[idx]
                
                anomalies.append({
                    'operator': operator,
                    'tier': tier,
                    'payout_base_win': payout_val,
                    'predicted_payout': predicted_payout,
                    'regression_r2': r2_scores.get(operator, 0),
                    'deviation_pct': deviation,
                    'anomaly_score_if': anomaly_scores[i],
                    'payout_z_score': payout_z_score,
                    'no_of_bets': row_data['no_of_bets'],
                    # Core payout flow variables - actual money flow
                    'stake_real_money': row_data['stake_real_money'],
                    'stake_free_money': row_data['stake_free_money'],
                    'refund_total': row_data['refund_total'],
                    'adjustment_total': row_data['adjustment_total'],
                    'revenue_amt': row_data['revenue_amt'],
                    # Movement variables - aggregate payout flows
                    'movement_wager_amt': row_data['movement_wager_amt'],
                    'movement_win_amt': row_data['movement_win_amt'],
                    'movement_refund_amt': row_data['movement_refund_amt'],
                    'movement_adjustment_amt': row_data['movement_adjustment_amt'],
                    'game_type': row_data['game_type'],
                    'is_weekend': row_data.get('is_weekend', 0),
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
                    'median_stake_z_score': op_anomalies['payout_z_score'].median() if len(op_anomalies) > 0 else 0
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('anomaly_rate', ascending=False)
        
        return summary_df
    
    def _create_operator_flags(self, anomalies_df, df):
        """Create anomaly flags summary by operator"""
        operator_data = []
        
        for operator in anomalies_df['operator'].unique():
            op_anomalies = anomalies_df[anomalies_df['operator'] == operator]
            op_total = len(df[df['operator'] == operator])
            
            # Calculate anomaly metrics by operator
            total_anomalies = len(op_anomalies)
            anomaly_rate = total_anomalies / op_total if op_total > 0 else 0
            avg_anomaly_score = op_anomalies['anomaly_score_if'].mean()
            avg_deviation = op_anomalies['deviation_pct'].mean()
            avg_payout_zscore = op_anomalies['payout_z_score'].mean()
            
            # High-risk flags
            high_deviation_count = len(op_anomalies[op_anomalies['deviation_pct'] > 0.5])
            high_zscore_count = len(op_anomalies[abs(op_anomalies['payout_z_score']) > 2])
            
            operator_data.append({
                'operator': operator,
                'total_records': op_total,
                'anomalies_detected': total_anomalies,
                'anomaly_rate': anomaly_rate,
                'avg_anomaly_score': avg_anomaly_score,
                'avg_deviation_pct': avg_deviation,
                'avg_payout_zscore': avg_payout_zscore,
                'high_deviation_anomalies': high_deviation_count,
                'high_zscore_anomalies': high_zscore_count,
                'risk_level': self._calculate_risk_level(anomaly_rate, avg_deviation, avg_payout_zscore)
            })
        
        return pd.DataFrame(operator_data).sort_values('anomaly_rate', ascending=False)
    
    def _create_game_type_flags(self, anomalies_df, df):
        """Create anomaly flags summary by game type"""
        game_type_data = []
        
        for game_type in anomalies_df['game_type'].unique():
            gt_anomalies = anomalies_df[anomalies_df['game_type'] == game_type]
            gt_total = len(df[df['game_type'] == game_type])
            
            # Calculate anomaly metrics by game type
            total_anomalies = len(gt_anomalies)
            anomaly_rate = total_anomalies / gt_total if gt_total > 0 else 0
            avg_anomaly_score = gt_anomalies['anomaly_score_if'].mean()
            avg_deviation = gt_anomalies['deviation_pct'].mean()
            avg_payout_zscore = gt_anomalies['payout_z_score'].mean()
            
            # Operator diversity in anomalies
            unique_operators = gt_anomalies['operator'].nunique()
            
            # High-risk flags
            high_deviation_count = len(gt_anomalies[gt_anomalies['deviation_pct'] > 0.5])
            high_zscore_count = len(gt_anomalies[abs(gt_anomalies['payout_z_score']) > 2])
            
            game_type_data.append({
                'game_type': game_type,
                'total_records': gt_total,
                'anomalies_detected': total_anomalies,
                'anomaly_rate': anomaly_rate,
                'affected_operators': unique_operators,
                'avg_anomaly_score': avg_anomaly_score,
                'avg_deviation_pct': avg_deviation,
                'avg_payout_zscore': avg_payout_zscore,
                'high_deviation_anomalies': high_deviation_count,
                'high_zscore_anomalies': high_zscore_count,
                'risk_level': self._calculate_risk_level(anomaly_rate, avg_deviation, avg_payout_zscore)
            })
        
        return pd.DataFrame(game_type_data).sort_values('anomaly_rate', ascending=False)
    
    def _calculate_risk_level(self, anomaly_rate, avg_deviation, avg_payout_zscore):
        """Calculate risk level based on anomaly metrics"""
        if anomaly_rate > 0.15 or avg_deviation > 1.0 or abs(avg_payout_zscore) > 3:
            return 'HIGH'
        elif anomaly_rate > 0.08 or avg_deviation > 0.5 or abs(avg_payout_zscore) > 2:
            return 'MEDIUM'
        else:
            return 'LOW'
