import luigi
import pandas as pd
import sys
from pathlib import Path


class GenerateAnomalyReport(luigi.Task):
    """Generate comprehensive anomaly detection report with statistics and recommendations"""
    
    def requires(self):
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from warehouse.tasks.detect_anomalies import DetectAnomalies
        return DetectAnomalies()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/anomaly_report.md')
    
    def run(self):
        # Load data
        all_anomalies = pd.read_csv(self.requires().output()['anomalies_with_context'].path)
        summary = pd.read_csv(self.requires().output()['anomaly_summary'].path)
        operator_flags = pd.read_csv(self.requires().output()['operator_flags'].path)
        game_type_flags = pd.read_csv(self.requires().output()['game_type_flags'].path)
        classification = pd.read_csv('warehouse/data/operator_classification.csv')
        performance = pd.read_csv('warehouse/data/hybrid_model_performance.csv')
        
        # Generate report
        report = self._generate_report(all_anomalies, summary, operator_flags, game_type_flags, classification, performance)
        
        with open(self.output().path, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Report saved to: {self.output().path}")
    
    def _generate_report(self, all_anomalies, summary, operator_flags, game_type_flags, classification, performance):
        """Generate markdown report"""
        
        # All operators now use both models, classify by R² score for reporting
        regression_ops = classification[classification['r2_score'] > 0.6]
        anomaly_ops = classification[classification['r2_score'] <= 0.6]
        
        report = f"""# Gaming Operator Stake Anomaly Detection Report

## Executive Summary

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

**Approach:** Hybrid modeling strategy combining Linear Regression and Isolation Forest

**Total Anomalies Detected:** {len(all_anomalies):,}

---

## Model Classification

### Regression Operators (R² > 0.6)
**Count:** {len(regression_ops)} operators

These operators have predictable stake patterns and use tier-based linear regression models:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
"""
        
        for _, row in regression_ops.sort_values('r2_score', ascending=False).iterrows():
            report += f"| {row['operator']} | {row['tier']} | {row['r2_score']:.4f} | {performance[performance['operator']==row['operator']]['n_samples'].values[0]} | Linear Regression |\n"
        
        report += f"""
**Performance:**
- Mean R²: {regression_ops['r2_score'].mean():.4f}
- Median R²: {regression_ops['r2_score'].median():.4f}
- Best: {regression_ops.iloc[0]['operator']} (R²={regression_ops.iloc[0]['r2_score']:.4f})

---

### Anomaly Detection Operators (R² ≤ 0.6)
**Count:** {len(anomaly_ops)} operators

These operators have volatile stake patterns and use Isolation Forest for anomaly detection:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
"""
        
        for _, row in anomaly_ops.sort_values('r2_score', ascending=False).iterrows():
            report += f"| {row['operator']} | {row['tier']} | {row['r2_score']:.4f} | {performance[performance['operator']==row['operator']]['n_samples'].values[0]} | Isolation Forest |\n"
        
        report += f"""
**Rationale:**
These operators show unpredictable patterns that cannot be reliably modeled with regression. Focus is on detecting unusual stake amounts rather than prediction.

---

## Anomaly Detection Results

### Overall Statistics

| Metric | Value |
|--------|-------|
| Total Records | {summary['total_records'].sum():,} |
| Total Anomalies | {len(all_anomalies):,} |
| Overall Anomaly Rate | {len(all_anomalies)/summary['total_records'].sum()*100:.1f}% |
| Isolation Forest Anomalies | {len(all_anomalies[all_anomalies['anomaly_flagged_by']=='isolation_forest']):,} |

---

### Per-Operator Anomaly Rates

"""
        
        for _, row in summary.head(10).iterrows():
            # Classify by R² score for display
            op_r2 = classification[classification['operator']==row['operator']]['r2_score'].values
            model_type = "High R² (>0.6)" if len(op_r2) > 0 and op_r2[0] > 0.6 else "Low R² (≤0.6)"
            report += f"**{row['operator']}** ({model_type})\n"
            report += f"- Total Records: {row['total_records']}\n"
            report += f"- Anomalies: {row['anomalies_flagged']} ({row['anomaly_rate']*100:.1f}%)\n"
            report += f"- Median Deviation: {row['median_deviation_pct']*100:.1f}%\n"
            report += f"- Median Payout Z-Score: {row['median_stake_z_score']:.2f}\n"
            report += "\n"
        
        report += """---

## Anomaly Flags by Operator

### High-Risk Operators

"""
        
        high_risk_ops = operator_flags[operator_flags['risk_level'] == 'HIGH']
        if len(high_risk_ops) > 0:
            for _, row in high_risk_ops.iterrows():
                report += f"**{row['operator']}** - HIGH RISK\n"
                report += f"- Anomaly Rate: {row['anomaly_rate']*100:.1f}% ({row['anomalies_detected']}/{row['total_records']})\n"
                report += f"- Avg Deviation: {row['avg_deviation_pct']*100:.1f}%\n"
                report += f"- Avg Payout Z-Score: {row['avg_payout_zscore']:.2f}\n"
                report += f"- High Deviation Anomalies: {row['high_deviation_anomalies']}\n"
                report += f"- High Z-Score Anomalies: {row['high_zscore_anomalies']}\n"
                report += "\n"
        else:
            report += "No high-risk operators detected.\n\n"
        
        report += f"""### Medium Risk Operators

"""
        medium_risk_ops = operator_flags[operator_flags['risk_level'] == 'MEDIUM']
        if len(medium_risk_ops) > 0:
            for _, row in medium_risk_ops.head(5).iterrows():
                report += f"**{row['operator']}** - Medium Risk ({row['anomaly_rate']*100:.1f}% anomaly rate)\n"
        else:
            report += "No medium-risk operators detected.\n"
        
        report += f"""

---

## Anomaly Flags by Game Type

### High-Risk Game Types

"""
        
        high_risk_games = game_type_flags[game_type_flags['risk_level'] == 'HIGH']
        if len(high_risk_games) > 0:
            for _, row in high_risk_games.iterrows():
                report += f"**{row['game_type']}** - HIGH RISK\n"
                report += f"- Anomaly Rate: {row['anomaly_rate']*100:.1f}% ({row['anomalies_detected']}/{row['total_records']})\n"
                report += f"- Affected Operators: {row['affected_operators']}\n"
                report += f"- Avg Deviation: {row['avg_deviation_pct']*100:.1f}%\n"
                report += f"- Avg Payout Z-Score: {row['avg_payout_zscore']:.2f}\n"
                report += f"- High Deviation Anomalies: {row['high_deviation_anomalies']}\n"
                report += f"- High Z-Score Anomalies: {row['high_zscore_anomalies']}\n"
                report += "\n"
        else:
            report += "No high-risk game types detected.\n\n"
            
        report += f"""### Game Type Anomaly Summary

| Game Type | Anomaly Rate | Risk Level | Affected Operators |
|-----------|--------------|------------|-------------------|
"""
        
        for _, row in game_type_flags.head(10).iterrows():
            report += f"| {row['game_type']} | {row['anomaly_rate']*100:.1f}% | {row['risk_level']} | {row['affected_operators']} |\n"

        report += """

---

## Anomaly Types

### 1. Regression Deviation Anomalies
**Method:** Linear regression prediction with 20% deviation threshold

**Interpretation:**
- Stake deviates >20% from predicted value
- Indicates unusual stake given historical patterns
- **Action:** Investigate business context for large deviations

### 2. Isolation Forest Anomalies
**Method:** Multivariate outlier detection (contamination=10%)

**Interpretation:**
- Unusual combination of features (stake, bets, game type, movement amounts)
- **Stake z-score** shows stake's contribution:
  - |z| > 2: Stake is a major contributor
  - |z| > 1: Stake is a moderate contributor
  - |z| ≤ 1: Other features drive the anomaly

---

## Top Anomalies by Payout Magnitude

"""
        
        top_anomalies = all_anomalies.nlargest(10, 'payout_base_win')
        
        for idx, row in top_anomalies.iterrows():
            report += f"**{row['operator']}**: Payout {row['payout_base_win']:,.0f} UGX\n"
            report += f"- Type: {row['anomaly_flagged_by']}\n"
            report += f"- **Actual Payout**: {row['payout_base_win']:,.0f} UGX\n"
            report += f"- **Predicted Payout**: {row['predicted_payout']:,.0f} UGX\n"
            report += f"- **Deviation**: {row['deviation_pct']*100:.1f}%\n"
            report += f"- Stake (Real): {row['stake_real_money']:,.0f} UGX\n"
            report += f"- Stake (Free): {row['stake_free_money']:,.0f} UGX\n"
            report += f"- Refund: {row['refund_total']:,.0f} UGX\n"
            report += f"- Adjustment: {row['adjustment_total']:,.0f} UGX\n"
            report += f"- Revenue: {row['revenue_amt']:,.0f} UGX\n"
            report += f"- No. of Bets: {row['no_of_bets']}\n"
            report += f"- Game Type: {row['game_type']}\n"
            if pd.notna(row['payout_z_score']):
                report += f"- Payout z-score: {row['payout_z_score']:.2f}\n"
            report += "\n"
        
        report += """---

## Recommendations

### For High-Risk Operators:
1. **Immediate Investigation** - Review all HIGH risk operators flagged above
2. **Enhanced Monitoring** - Set up real-time alerts for anomaly rates >15%
3. **Deep Dive Analysis** - Examine transaction patterns and business logic
4. **Stakeholder Communication** - Notify relevant teams for business context

### For High-Risk Game Types:
1. **Cross-Operator Analysis** - Investigate if anomalies are game-specific or operator-specific
2. **Game Rules Review** - Verify if unusual patterns align with game mechanics
3. **Payout Configuration** - Check if game type settings are correctly configured

### For Regression Operators:
1. **Monitor prediction accuracy** - Track R² scores over time
2. **Alert on deviations** - Flag stakes >20% from predictions
3. **Investigate patterns** - Look for systematic deviations by game type or time
4. **Retrain monthly** - Update models with new data

### For Anomaly Detection Operators:
1. **Review flagged records** - Prioritize by anomaly score
2. **Check stake z-scores** - Focus on |z| > 2 for stake-driven anomalies
3. **Business context** - Verify if anomalies are legitimate or errors
4. **Trend monitoring** - Track if anomaly rate increases above 15%

### Risk Level Actions:
- **HIGH**: Immediate investigation required within 24 hours
- **MEDIUM**: Review within 48 hours, monitor trends
- **LOW**: Include in weekly monitoring reports

### When to Switch Models:
- If regression operator R² drops below 0.6 → switch to Isolation Forest
- If anomaly operator shows consistent patterns → try regression

---

## Technical Details

**Features Used:**
- `no_of_bets` - Number of bets placed
- `is_weekend` - Weekend indicator
- `game_type` - One-hot encoded game categories
- `operator` - One-hot encoded operator (regression only)

**Core Payout Flow Variables (Money Flow):**
- `stake_real_money` - Real money wagered (direct predictor of payout magnitude)
- `stake_free_money` - Free/bonus wagers (affects net payout differently)
- `payout_base_win` - Base payout before refunds/adjustments
- `refund_total` - Returned funds that reduce net payout
- `adjustment_total` - Bonus or system adjustments impacting payout
- `revenue_amt` - Net revenue relevant when modeling operator vs player payouts

**Movement Variables (Aggregate Payout Flows):**
- `movement_wager_amt` - Aggregate wager changes
- `movement_win_amt` - Aggregate win changes
- `movement_refund_amt` - Aggregate refund changes
- `movement_adjustment_amt` - Aggregate adjustment changes

**Thresholds:**
- R² threshold: 0.6 (regression vs anomaly classification)
- Deviation threshold: 20% (regression anomalies)
- Contamination: 10% (Isolation Forest)

**Data:**
- Training: 80% of data per operator
- Testing: 20% of data per operator

---

*This report was generated automatically by the hybrid anomaly detection pipeline.*
"""
        
        return report


if __name__ == '__main__':
    import luigi
    luigi.build([GenerateAnomalyReport()], local_scheduler=True, log_level='INFO')
