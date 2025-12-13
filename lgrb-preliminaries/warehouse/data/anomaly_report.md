# Gaming Operator Stake Anomaly Detection Report

## Executive Summary

**Date:** 2025-12-13 04:18

**Approach:** Hybrid modeling strategy combining Linear Regression and Isolation Forest

**Total Anomalies Detected:** 987

---

## Model Classification

### Regression Operators (R² > 0.6)

**Count:** 11 operators

These operators have predictable stake patterns and use tier-based linear regression models:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
| OP_0005 | very_high | 0.9972 | 378 | Linear Regression |
| OP_0016 | high | 0.9913 | 235 | Linear Regression |
| OP_0009 | zero | 0.9528 | 333 | Linear Regression |
| OP_0002 | high | 0.9490 | 338 | Linear Regression |
| OP_0003 | noise | 0.9445 | 390 | Linear Regression |
| OP_0006 | noise | 0.9270 | 342 | Linear Regression |
| OP_0004 | high | 0.9212 | 588 | Linear Regression |
| OP_0011 | noise | 0.8995 | 278 | Linear Regression |
| OP_0010 | high | 0.8686 | 131 | Linear Regression |
| OP_0007 | noise | 0.8618 | 335 | Linear Regression |
| OP_0023 | very_high | 0.8052 | 149 | Linear Regression |

**Performance:**

- Mean R²: 0.9198
- Median R²: 0.9270
- Best: OP_0005 (R²=0.9972)

---

### Anomaly Detection Operators (R² ≤ 0.6)

**Count:** 10 operators

These operators have volatile stake patterns and use Isolation Forest for anomaly detection:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
| OP_0024 | high | 0.7239 | 156 | Isolation Forest |
| OP_0001 | low | 0.6937 | 266 | Isolation Forest |
| OP_0022 | mid | 0.6475 | 163 | Isolation Forest |
| OP_0013 | mid | 0.6340 | 247 | Isolation Forest |
| OP_0028 | noise | 0.5537 | 119 | Isolation Forest |
| OP_0020 | high | 0.5228 | 216 | Isolation Forest |
| OP_0025 | low | 0.4618 | 147 | Isolation Forest |
| OP_0017 | zero | 0.4597 | 134 | Isolation Forest |
| OP_0015 | low | 0.4250 | 247 | Isolation Forest |
| OP_0012 | zero | 0.3630 | 269 | Isolation Forest |

**Rationale:**
These operators show unpredictable patterns that cannot be reliably modeled with regression. Focus is on detecting unusual stake amounts rather than prediction.

---

## Anomaly Detection Results

### Overall Statistics

| Metric | Value |
|--------|-------|
| Total Records | 5,461 |
| Total Anomalies | 987 |
| Overall Anomaly Rate | 18.1% |
| Regression Anomalies | 787 |
| Isolation Forest Anomalies | 200 |

---

### Per-Operator Anomaly Rates

**OP_0003** (regression)

- Total Records: 390
- Anomalies: 286 (73.3%)
  - Regression deviations: 286

**OP_0004** (regression)

- Total Records: 588
- Anomalies: 254 (43.2%)
  - Regression deviations: 254

**OP_0010** (regression)

- Total Records: 131
- Anomalies: 42 (32.1%)
  - Regression deviations: 42

**OP_0007** (regression)

- Total Records: 335
- Anomalies: 72 (21.5%)
  - Regression deviations: 72

**OP_0005** (regression)

- Total Records: 378
- Anomalies: 81 (21.4%)
  - Regression deviations: 81

**OP_0023** (regression)

- Total Records: 149
- Anomalies: 20 (13.4%)
  - Regression deviations: 20

**OP_0017** (anomaly_detection)

- Total Records: 134
- Anomalies: 14 (10.4%)
  - Isolation Forest: 14

**OP_0022** (anomaly_detection)

- Total Records: 163
- Anomalies: 17 (10.4%)
  - Isolation Forest: 17

**OP_0024** (anomaly_detection)

- Total Records: 156
- Anomalies: 16 (10.3%)
  - Isolation Forest: 16

**OP_0025** (anomaly_detection)

- Total Records: 147
- Anomalies: 15 (10.2%)
  - Isolation Forest: 15

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

## Top Anomalies by Stake Magnitude

**OP_0017**: 2,172,874,685 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 95.7%
- Stake z-score: 4.19

**OP_0017**: 2,079,198,735 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 87.2%
- Stake z-score: 3.82

**OP_0017**: 1,942,318,370 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 74.9%
- Stake z-score: 3.28

**OP_0017**: 1,940,742,070 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 74.8%
- Stake z-score: 3.27

**OP_0017**: 1,746,100,035 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 57.2%
- Stake z-score: 2.51

**OP_0017**: 1,732,810,004 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 56.0%
- Stake z-score: 2.45

**OP_0017**: 1,669,054,015 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 50.3%
- Stake z-score: 2.20

**OP_0017**: 1,471,610,305 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 32.5%
- Stake z-score: 1.42

**OP_0017**: 932,468,060 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 16.0%
- Stake z-score: -0.70

**OP_0017**: 916,955,910 UGX

- Type: isolation_forest
- Expected: 1,110,449,976 UGX
- Deviation: 17.4%
- Stake z-score: -0.76

---

## Recommendations

### For Regression Operators

1. **Monitor prediction accuracy** - Track R² scores over time
2. **Alert on deviations** - Flag stakes >20% from predictions
3. **Investigate patterns** - Look for systematic deviations by game type or time
4. **Retrain monthly** - Update models with new data

### For Anomaly Detection Operators

1. **Review flagged records** - Prioritize by anomaly score
2. **Check stake z-scores** - Focus on |z| > 2 for stake-driven anomalies
3. **Business context** - Verify if anomalies are legitimate or errors
4. **Trend monitoring** - Track if anomaly rate increases above 15%

### When to Switch Models

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
