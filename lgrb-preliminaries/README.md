# Gaming Operator Stake Anomaly Detection

Hybrid anomaly detection system for gaming operators using tier-based linear regression and isolation forest models.

## Overview

This system detects unusual stake patterns in gaming operators by:
- **Regression models** for predictable operators (R² > 0.75)
- **Isolation forest** for volatile operators (R² ≤ 0.75)
- **Statistical outlier detection** using 90th percentile thresholds

## Quick Start

### Installation

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run Pipeline

```bash
python run_anomaly_detection.py
```

This executes the complete pipeline:

1. Filters data (operators with ≥100 records)
2. Trains hybrid models using DBSCAN operator clustering
3. Detects anomalies using statistical thresholds
4. Saves results to `warehouse/data/`

### Generate Report

```bash
python warehouse/tasks/generate_anomaly_report.py
```

Creates comprehensive Markdown report with:
- Per-operator anomaly rates
- Model performance metrics
- Top anomalies by stake magnitude
- Actionable recommendations

## Pipeline Structure

```
warehouse/
├── tasks/
│   ├── filter_and_extract.py      # Extract columns from raw data
│   ├── filter_by_sample_size.py   # Filter operators (≥100 records)
│   ├── cluster_operators.py       # DBSCAN clustering
│   ├── train_hybrid_models.py     # Train regression + isolation forest
│   ├── detect_anomalies.py        # Statistical outlier detection
│   └── generate_anomaly_report.py # Markdown report generation
├── data/                           # Output files
│   ├── all_anomalies.csv          # Combined anomalies
│   ├── regression_anomalies.csv   # Regression deviations
│   ├── isolation_anomalies.csv    # Isolation forest outliers
│   ├── anomaly_summary.csv        # Per-operator summary
│   └── anomaly_report.md          # Comprehensive report
└── models/                         # Trained models
    ├── regression_models.pkl      # Tier-based regression
    └── anomaly_models.pkl         # Per-operator isolation forest
```

## Key Features

### Operator Clustering
- **DBSCAN** (eps=0.3, min_samples=2) on movement features
- Creates tiers: low, mid, high, very_high, noise, zero
- Handles operators with zero movement amounts

### Hybrid Modeling
- **R² Threshold**: 0.75
  - Above: Tier-based linear regression
  - Below: Per-operator isolation forest
- Trains on 80% data, validates on 20%

### Anomaly Detection
- **Regression**: 90th percentile of prediction errors per operator
- **Isolation Forest**: Contamination=10%, includes stake z-score
- Adapts to each operator's error distribution

## Output Files

### all_anomalies.csv
Combined anomalies from both methods:
- `operator`: Operator ID
- `stake_real_money`: Actual stake amount
- `predicted_stake`: Model prediction (regression only)
- `deviation_pct`: % deviation from prediction
- `anomaly_type`: regression_deviation | isolation_forest
- `stake_z_score`: Stake contribution (isolation only)

### anomaly_report.md
Comprehensive report with:
- Operator classification (regression vs anomaly detection)
- Per-operator anomaly rates and thresholds
- Top anomalies by magnitude
- Actionable recommendations

## Typical Results

- **Total Anomaly Rate**: ~8-10%
- **Regression Operators**: 11 operators, ~7% anomaly rate
- **Anomaly Operators**: 10 operators, ~10% anomaly rate

## Configuration

### Adjust R² Threshold

```python
# warehouse/tasks/train_hybrid_models.py
r2_threshold = luigi.FloatParameter(default=0.75)  # Increase for stricter regression criteria
```

### Adjust Anomaly Sensitivity

```python
# warehouse/tasks/detect_anomalies.py
deviation_threshold = luigi.FloatParameter(default=0.75)  # Minimum deviation threshold

# For more/fewer anomalies, change percentile in _detect_regression_anomalies:
percentile_threshold = np.percentile(deviations, 90)  # 90 = ~10% anomalies, 95 = ~5%
```

### Adjust Isolation Forest

```python
# warehouse/tasks/train_hybrid_models.py
IsolationForest(
    contamination=0.1,  # Expected anomaly rate (10%)
    n_estimators=100    # Number of trees
)
```

## Interpretation Guide

### Regression Anomalies
**What**: Stake deviates significantly from tier-based prediction
**Action**: Investigate business context for large deviations (>90th percentile)
**Example**: OP_0003 predicted 1M, actual 2.5M (150% deviation)

### Isolation Forest Anomalies
**What**: Unusual combination of features (stake, bets, game type, movement)
**Stake Z-Score**:
- |z| > 2: Stake is major contributor → Focus here
- |z| > 1: Stake is moderate contributor
- |z| ≤ 1: Other features drive anomaly

## Troubleshooting

### High Anomaly Rates
If anomaly rate >15%, check:
1. Data quality (duplicates, outliers)
2. Percentile threshold (increase 90 → 95)
3. R² threshold (lower 0.75 → 0.70)

### Low Model Performance
If R² scores low across operators:
1. Check feature engineering
2. Verify movement features are calculated correctly
3. Consider additional features

### Missing Dependencies
```bash
pip install --upgrade luigi pandas scikit-learn numpy joblib
```

## Development

### Add New Features
1. Update `warehouse/tasks/filter_and_extract.py`
2. Modify feature_cols in `train_hybrid_models.py`
3. Re-run pipeline

### Add New Task
```python
import luigi
from warehouse.tasks.detect_anomalies import DetectAnomalies

class YourTask(luigi.Task):
    def requires(self):
        return DetectAnomalies()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/your_output.csv')
    
    def run(self):
        # Your logic here
        pass
```

## License

Internal use only - Gaming Analytics Team
