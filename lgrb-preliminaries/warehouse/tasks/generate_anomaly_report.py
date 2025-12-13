"""
Generate comprehensive anomaly detection summary report in Markdown format.
"""
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
        all_anomalies = pd.read_csv(self.requires().output()['all_anomalies'].path)
        summary = pd.read_csv(self.requires().output()['anomaly_summary'].path)
        classification = pd.read_csv('warehouse/data/operator_classification.csv')
        performance = pd.read_csv('warehouse/data/hybrid_model_performance.csv')
        
        # Generate report
        report = self._generate_report(all_anomalies, summary, classification, performance)
        
        with open(self.output().path, 'w') as f:
            f.write(report)
        
        print(f"\n✓ Report saved to: {self.output().path}")
    
    def _generate_report(self, all_anomalies, summary, classification, performance):
        """Generate markdown report"""
        
        regression_ops = classification[classification['model_type'] == 'regression']
        anomaly_ops = classification[classification['model_type'] == 'anomaly_detection']
        
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
| Regression Anomalies | {len(all_anomalies[all_anomalies['anomaly_type']=='regression_deviation']):,} |
| Isolation Forest Anomalies | {len(all_anomalies[all_anomalies['anomaly_type']=='isolation_forest']):,} |

---

### Per-Operator Anomaly Rates

"""
        
        for _, row in summary.head(10).iterrows():
            model_type = classification[classification['operator']==row['operator']]['model_type'].values[0]
            report += f"**{row['operator']}** ({model_type})\n"
            report += f"- Total Records: {row['total_records']}\n"
            report += f"- Anomalies: {row['total_anomalies']} ({row['anomaly_rate']*100:.1f}%)\n"
            if row['regression_anomalies'] > 0:
                report += f"  - Regression deviations: {row['regression_anomalies']}\n"
            if row['isolation_anomalies'] > 0:
                report += f"  - Isolation Forest: {row['isolation_anomalies']}\n"
            report += "\n"
        
        report += """---

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

## Top Anomalies by Stake Magnitude

"""
        
        top_anomalies = all_anomalies.nlargest(10, 'stake_real_money')
        
        for idx, row in top_anomalies.iterrows():
            report += f"**{row['operator']}**: {row['stake_real_money']:,.0f} UGX\n"
            report += f"- Type: {row['anomaly_type']}\n"
            report += f"- Expected: {row['predicted_stake']:,.0f} UGX\n"
            report += f"- Deviation: {row['deviation_pct']*100:.1f}%\n"
            if pd.notna(row['stake_z_score']):
                report += f"- Stake z-score: {row['stake_z_score']:.2f}\n"
            report += "\n"
        
        report += """---

## Recommendations

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

### When to Switch Models:
- If regression operator R² drops below 0.6 → switch to Isolation Forest
- If anomaly operator shows consistent patterns → try regression

---

## Technical Details

**Features Used:**
- `no_of_bets` - Number of bets placed
- `stake_free_money` - Promotional stake amount
- `movement_wager_amt` - Historical cumulative wager
- `movement_win_amt` - Historical cumulative win
- `is_weekend` - Weekend indicator
- `game_type` - One-hot encoded game categories
- `operator` - One-hot encoded operator (regression only)

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
