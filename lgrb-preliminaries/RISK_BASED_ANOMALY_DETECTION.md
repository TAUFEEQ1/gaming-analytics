# Risk-Based Anomaly Detection System

## Overview

This system implements a **dual-model architecture** that uses both regression and Isolation Forest for anomaly detection, with **risk-based contamination rates** that automatically apply more scrutiny to smaller betting houses.

## Architecture

### 1. Dual-Model Approach

**All 21 operators** get both models:

- **Regression Model** (Context): Provides expected stake baseline and deviation
- **Isolation Forest** (Detection): Primary anomaly detection with tier-specific sensitivity

### 2. Tier-Based Regression

6 shared models based on operator size (DBSCAN clustering on movement amounts):

- `very_high`: Largest operators (R²=0.99)
- `high`: Large operators (R²=0.87)
- `mid`: Medium operators (R²=0.45)
- `low`: Smaller operators (R²=0.65)
- `zero`: New/smallest operators (R²=0.97)
- `noise`: Outlier movement patterns (R²=0.99)

### 3. Per-Operator Isolation Forest

21 independent models, each trained on operator-specific data with **risk-based contamination rates**:

| Tier | Contamination | Risk Profile | Operators |
|------|---------------|--------------|-----------|
| very_high | 5% | Established, predictable | 2 |
| high | 8% | Large, stable | 6 |
| mid | 10% | Medium risk | 2 |
| low | 15% | Smaller, higher variance | 3 |
| **zero** | **20%** | **Highest risk - new/small** | **3** |
| noise | 15% | Irregular patterns | 5 |

## Results

### Actual Performance (5,461 records, 21 operators)

```env
Tier         | Total Records | Anomalies | Actual Rate | Target Rate
-------------|---------------|-----------|-------------|-------------
very_high    |           527 |        27 |        5.1% |          5%
high         |          1664 |       135 |        8.1% |          8%
mid          |           410 |        42 |       10.2% |         10%
low          |           660 |        99 |       15.0% |         15%
zero         |           736 |       148 |       20.1% |         20%
noise        |          1464 |       222 |       15.2% |         15%
-------------|---------------|-----------|-------------|-------------
TOTAL        |          5461 |       673 |       12.3% |        N/A
```

## ✓ Actual rates match target rates within 0.5%**

## Key Benefits

### 1. Risk Alignment

- Small betting houses (zero tier) get 4x more scrutiny than large operators
- Contamination rates automatically reflect business risk
- No manual threshold tuning required

### 2. Contextual Reporting

Each flagged record includes:

- **expected_stake_regression**: What the tier model predicted
- **regression_r2**: Model confidence (0.36-0.997)
- **deviation_pct**: How far from expected (as proportion)
- **anomaly_score_if**: Isolation Forest score (more negative = more anomalous)
- **stake_z_score**: Standard deviations from operator normal
- **anomaly_flagged_by**: `isolation_forest` or `none`

### 3. Decision Support

Decision maker gets full context without binary classification:

- Regression baseline shows "expected" behavior
- Deviation shows magnitude of difference
- IF score confirms statistical outlier status
- Z-score shows how unusual for that operator
- Human judgment on whether to investigate

## Example Anomalies

### OP_0005 (very_high tier, 5% contamination)

```env
Stake: 129,703,405.57
Expected: 132,108,800
Deviation: 1.8%
IF Score: -0.676 (flagged)
Z-Score: 4.08σ (highly unusual)
```

**Interpretation**: Very large stake (~4σ above normal) but close to regression prediction. IF flagged due to unusual feature combination.

### OP_0009 (zero tier, 20% contamination)

```env
67 anomalies / 333 records (20.1%)
```

**Interpretation**: Small/new operator with high variance. 20% contamination ensures thorough scrutiny of risky behavior.

## Scalability

### Current: 21 Operators

- 6 tier models (O(1) - shared)
- 21 IF models (O(n) - per operator)
- Training time: <1 minute

### Future: 500+ Operators

- Still 6 tier models (no growth)
- 500 IF models (linear growth)
- Each IF trained on ~100-1000 samples
- Estimated training time: <10 minutes

**Architecture scales linearly** with operator count.

## Implementation Notes

### Training (`train_hybrid_models.py`)

```python
tier_contamination = {
    'very_high': 0.05,  # Large operators: 5%
    'high': 0.08,       # 8%
    'mid': 0.10,        # 10%
    'low': 0.15,        # 15%
    'zero': 0.20,       # Small operators: 20%
    'noise': 0.15       # 15%
}
```

### Detection (`detect_anomalies.py`)

- All 5,461 records saved to `anomalies_with_context.csv`
- `anomaly_flagged_by='none'` for normal records
- `anomaly_flagged_by='isolation_forest'` for anomalies
- Regression context included for ALL records

## Philosophy

**Regression provides context, Isolation Forest provides detection.**

- Regression R² doesn't predict absolute error magnitude
- High R² doesn't guarantee small errors on outliers
- IF specialized for outlier detection in multivariate space
- Both signals together give decision maker complete picture

**Risk-based contamination aligns detection with business reality.**

- Small betting houses ARE riskier (20% contamination)
- Large operators ARE more predictable (5% contamination)
- Model sensitivity automatically matches risk profile
- No manual threshold adjustment needed per operator

## Files

- `warehouse/tasks/train_hybrid_models.py`: Train dual models with tier-based contamination
- `warehouse/tasks/detect_anomalies.py`: Detect anomalies with context
- `warehouse/data/anomalies_with_context.csv`: All records with dual signals
- `warehouse/data/models/regression_models.pkl`: 6 tier models
- `warehouse/data/models/anomaly_models.pkl`: 21 IF models with contamination metadata

## Next Steps

1. **Reporting Dashboard**: Visualize tier-specific anomaly rates
2. **Zero-Shot Operators**: Handle <100 sample operators with K-NN similarity
3. **Temporal Analysis**: Track contamination rate effectiveness over time
4. **Feedback Loop**: Adjust contamination based on false positive rates
