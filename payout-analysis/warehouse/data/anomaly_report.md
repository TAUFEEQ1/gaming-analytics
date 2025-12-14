# Gaming Operator Stake Anomaly Detection Report

## Executive Summary

**Date:** 2025-12-14 00:14

**Approach:** Hybrid modeling strategy combining Linear Regression and Isolation Forest

**Total Anomalies Detected:** 553

---

## Model Classification

### Regression Operators (R² > 0.6)
**Count:** 20 operators

These operators have predictable stake patterns and use tier-based linear regression models:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
| OP_0028 | noise | 1.0000 | 119 | Linear Regression |
| OP_0011 | noise | 1.0000 | 278 | Linear Regression |
| OP_0005 | noise | 1.0000 | 378 | Linear Regression |
| OP_0016 | low | 1.0000 | 235 | Linear Regression |
| OP_0013 | noise | 1.0000 | 247 | Linear Regression |
| OP_0002 | low | 1.0000 | 338 | Linear Regression |
| OP_0017 | zero | 1.0000 | 134 | Linear Regression |
| OP_0023 | noise | 1.0000 | 149 | Linear Regression |
| OP_0009 | zero | 1.0000 | 333 | Linear Regression |
| OP_0007 | noise | 1.0000 | 335 | Linear Regression |
| OP_0024 | noise | 1.0000 | 156 | Linear Regression |
| OP_0020 | mid | 1.0000 | 216 | Linear Regression |
| OP_0022 | noise | 1.0000 | 163 | Linear Regression |
| OP_0025 | noise | 1.0000 | 147 | Linear Regression |
| OP_0003 | noise | 1.0000 | 390 | Linear Regression |
| OP_0001 | noise | 1.0000 | 266 | Linear Regression |
| OP_0010 | mid | 0.9958 | 131 | Linear Regression |
| OP_0015 | noise | 0.9924 | 247 | Linear Regression |
| OP_0004 | noise | 0.8985 | 588 | Linear Regression |
| OP_0006 | noise | 0.8698 | 342 | Linear Regression |

**Performance:**
- Mean R²: 0.9878
- Median R²: 1.0000
- Best: OP_0028 (R²=1.0000)

---

### Anomaly Detection Operators (R² ≤ 0.6)
**Count:** 1 operators

These operators have volatile stake patterns and use Isolation Forest for anomaly detection:

| Operator | Tier | R² Score | Samples | Model |
|----------|------|----------|---------|-------|
| OP_0012 | zero | 0.4224 | 269 | Isolation Forest |

**Rationale:**
These operators show unpredictable patterns that cannot be reliably modeled with regression. Focus is on detecting unusual stake amounts rather than prediction.

---

## Anomaly Detection Results

### Overall Statistics

| Metric | Value |
|--------|-------|
| Total Records | 5,461 |
| Total Anomalies | 553 |
| Overall Anomaly Rate | 10.1% |
| Isolation Forest Anomalies | 553 |

---

### Per-Operator Anomaly Rates

**OP_0017** (High R² (>0.6))
- Total Records: 134
- Anomalies: 14 (10.4%)
- Median Deviation: 0.0%
- Median Payout Z-Score: 1.47

**OP_0022** (High R² (>0.6))
- Total Records: 163
- Anomalies: 17 (10.4%)
- Median Deviation: 10.6%
- Median Payout Z-Score: 1.95

**OP_0024** (High R² (>0.6))
- Total Records: 156
- Anomalies: 16 (10.3%)
- Median Deviation: 14.6%
- Median Payout Z-Score: 1.29

**OP_0006** (High R² (>0.6))
- Total Records: 342
- Anomalies: 35 (10.2%)
- Median Deviation: 6.2%
- Median Payout Z-Score: 2.65

**OP_0016** (High R² (>0.6))
- Total Records: 235
- Anomalies: 24 (10.2%)
- Median Deviation: 0.0%
- Median Payout Z-Score: 2.21

**OP_0009** (High R² (>0.6))
- Total Records: 333
- Anomalies: 34 (10.2%)
- Median Deviation: 1.0%
- Median Payout Z-Score: 2.78

**OP_0025** (High R² (>0.6))
- Total Records: 147
- Anomalies: 15 (10.2%)
- Median Deviation: 0.0%
- Median Payout Z-Score: 1.29

**OP_0020** (High R² (>0.6))
- Total Records: 216
- Anomalies: 22 (10.2%)
- Median Deviation: 1.2%
- Median Payout Z-Score: 2.98

**OP_0001** (High R² (>0.6))
- Total Records: 266
- Anomalies: 27 (10.2%)
- Median Deviation: 53.6%
- Median Payout Z-Score: 2.27

**OP_0007** (High R² (>0.6))
- Total Records: 335
- Anomalies: 34 (10.1%)
- Median Deviation: 18.9%
- Median Payout Z-Score: 1.67

---

## Anomaly Flags by Operator

### High-Risk Operators

**OP_0016** - HIGH RISK
- Anomaly Rate: 10.2% (24/235)
- Avg Deviation: 0.0%
- Avg Payout Z-Score: 3.08
- High Deviation Anomalies: 0
- High Z-Score Anomalies: 13

**OP_0009** - HIGH RISK
- Anomaly Rate: 10.2% (34/333)
- Avg Deviation: 24.9%
- Avg Payout Z-Score: 5.61
- High Deviation Anomalies: 1
- High Z-Score Anomalies: 18

**OP_0025** - HIGH RISK
- Anomaly Rate: 10.2% (15/147)
- Avg Deviation: 32.1%
- Avg Payout Z-Score: 7.30
- High Deviation Anomalies: 4
- High Z-Score Anomalies: 7

**OP_0013** - HIGH RISK
- Anomaly Rate: 10.1% (25/247)
- Avg Deviation: 30.0%
- Avg Payout Z-Score: 9.08
- High Deviation Anomalies: 7
- High Z-Score Anomalies: 9

**OP_0028** - HIGH RISK
- Anomaly Rate: 10.1% (12/119)
- Avg Deviation: 42.8%
- Avg Payout Z-Score: 4.73
- High Deviation Anomalies: 6
- High Z-Score Anomalies: 9

**OP_0005** - HIGH RISK
- Anomaly Rate: 10.1% (38/378)
- Avg Deviation: 47.3%
- Avg Payout Z-Score: 27.93
- High Deviation Anomalies: 12
- High Z-Score Anomalies: 36

**OP_0012** - HIGH RISK
- Anomaly Rate: 10.0% (27/269)
- Avg Deviation: 30.6%
- Avg Payout Z-Score: 9.47
- High Deviation Anomalies: 9
- High Z-Score Anomalies: 19

**OP_0003** - HIGH RISK
- Anomaly Rate: 10.0% (39/390)
- Avg Deviation: 117.5%
- Avg Payout Z-Score: 3.94
- High Deviation Anomalies: 13
- High Z-Score Anomalies: 22

### Medium Risk Operators

**OP_0017** - Medium Risk (10.4% anomaly rate)
**OP_0022** - Medium Risk (10.4% anomaly rate)
**OP_0024** - Medium Risk (10.3% anomaly rate)
**OP_0006** - Medium Risk (10.2% anomaly rate)
**OP_0020** - Medium Risk (10.2% anomaly rate)


---

## Anomaly Flags by Game Type

### High-Risk Game Types

**CTG_generalBetting** - HIGH RISK
- Anomaly Rate: 34.8% (8/23)
- Affected Operators: 1
- Avg Deviation: 37.1%
- Avg Payout Z-Score: 0.64
- High Deviation Anomalies: 3
- High Z-Score Anomalies: 1

**RRI_slot** - HIGH RISK
- Anomaly Rate: 10.8% (44/407)
- Affected Operators: 2
- Avg Deviation: 42.8%
- Avg Payout Z-Score: 24.55
- High Deviation Anomalies: 13
- High Z-Score Anomalies: 39

**RRI_other** - HIGH RISK
- Anomaly Rate: 10.2% (96/945)
- Affected Operators: 5
- Avg Deviation: 13.4%
- Avg Payout Z-Score: 3.10
- High Deviation Anomalies: 11
- High Z-Score Anomalies: 62

**RRI_sports** - HIGH RISK
- Anomaly Rate: 9.8% (205/2101)
- Affected Operators: 12
- Avg Deviation: 51.8%
- Avg Payout Z-Score: 5.02
- High Deviation Anomalies: 53
- High Z-Score Anomalies: 112

### Game Type Anomaly Summary

| Game Type | Anomaly Rate | Risk Level | Affected Operators |
|-----------|--------------|------------|-------------------|
| CTG_generalBetting | 34.8% | HIGH | 1 |
| CTG_multi | 10.9% | MEDIUM | 7 |
| RRI_slot | 10.8% | HIGH | 2 |
| RRI_other | 10.2% | HIGH | 5 |
| RRI_roulette | 10.1% | MEDIUM | 1 |
| RRI_sports | 9.8% | HIGH | 12 |
| CTG_virtualSports | 8.7% | MEDIUM | 2 |
| CTG_eSports | 4.2% | LOW | 1 |


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

**OP_0006**: Payout 22,022,385,337 UGX
- Type: isolation_forest
- **Actual Payout**: 22,022,385,337 UGX
- **Predicted Payout**: 22,359,790,225 UGX
- **Deviation**: 1.5%
- Stake (Real): 10,270,151,858 UGX
- Stake (Free): 0 UGX
- Refund: 237,204 UGX
- Adjustment: 0 UGX
- Revenue: -11,752,470,682 UGX
- No. of Bets: 1828366.0
- Game Type: CTG_multi
- Payout z-score: 8.39

**OP_0006**: Payout 19,732,867,984 UGX
- Type: isolation_forest
- **Actual Payout**: 19,732,867,984 UGX
- **Predicted Payout**: 17,294,726,245 UGX
- **Deviation**: 14.1%
- Stake (Real): 7,766,166,879 UGX
- Stake (Free): 0 UGX
- Refund: 9,500 UGX
- Adjustment: 0 UGX
- Revenue: -11,966,710,605 UGX
- No. of Bets: 1772616.0
- Game Type: CTG_multi
- Payout z-score: 7.36

**OP_0006**: Payout 14,769,000,237 UGX
- Type: isolation_forest
- **Actual Payout**: 14,769,000,237 UGX
- **Predicted Payout**: 14,257,110,837 UGX
- **Deviation**: 3.6%
- Stake (Real): 12,649,712,311 UGX
- Stake (Free): 0 UGX
- Refund: 2,000 UGX
- Adjustment: 0 UGX
- Revenue: -2,119,289,926 UGX
- No. of Bets: 2926213.0
- Game Type: CTG_multi
- Payout z-score: 5.13

**OP_0006**: Payout 13,237,645,853 UGX
- Type: isolation_forest
- **Actual Payout**: 13,237,645,853 UGX
- **Predicted Payout**: 14,270,820,435 UGX
- **Deviation**: 7.2%
- Stake (Real): 7,220,540,976 UGX
- Stake (Free): 0 UGX
- Refund: 10,390 UGX
- Adjustment: 0 UGX
- Revenue: -6,017,115,266 UGX
- No. of Bets: 1514246.0
- Game Type: CTG_multi
- Payout z-score: 4.44

**OP_0006**: Payout 13,200,727,840 UGX
- Type: isolation_forest
- **Actual Payout**: 13,200,727,840 UGX
- **Predicted Payout**: 13,274,151,389 UGX
- **Deviation**: 0.6%
- Stake (Real): 12,242,416,423 UGX
- Stake (Free): 0 UGX
- Refund: 7,525 UGX
- Adjustment: 0 UGX
- Revenue: -958,318,942 UGX
- No. of Bets: 2764967.0
- Game Type: CTG_multi
- Payout z-score: 4.43

**OP_0006**: Payout 13,160,328,692 UGX
- Type: isolation_forest
- **Actual Payout**: 13,160,328,692 UGX
- **Predicted Payout**: 13,171,013,577 UGX
- **Deviation**: 0.1%
- Stake (Real): 11,453,464,561 UGX
- Stake (Free): 0 UGX
- Refund: 10,450 UGX
- Adjustment: 0 UGX
- Revenue: -1,706,874,581 UGX
- No. of Bets: 2413401.0
- Game Type: CTG_multi
- Payout z-score: 4.41

**OP_0006**: Payout 12,848,265,569 UGX
- Type: isolation_forest
- **Actual Payout**: 12,848,265,569 UGX
- **Predicted Payout**: 13,092,014,635 UGX
- **Deviation**: 1.9%
- Stake (Real): 13,180,321,266 UGX
- Stake (Free): 0 UGX
- Refund: 27,328 UGX
- Adjustment: 0 UGX
- Revenue: 332,028,370 UGX
- No. of Bets: 3205839.0
- Game Type: CTG_multi
- Payout z-score: 4.27

**OP_0006**: Payout 12,126,898,575 UGX
- Type: isolation_forest
- **Actual Payout**: 12,126,898,575 UGX
- **Predicted Payout**: 11,658,971,540 UGX
- **Deviation**: 4.0%
- Stake (Real): 12,075,322,308 UGX
- Stake (Free): 0 UGX
- Refund: 99,920 UGX
- Adjustment: 0 UGX
- Revenue: -51,676,187 UGX
- No. of Bets: 2621581.0
- Game Type: CTG_multi
- Payout z-score: 3.95

**OP_0006**: Payout 11,055,233,288 UGX
- Type: isolation_forest
- **Actual Payout**: 11,055,233,288 UGX
- **Predicted Payout**: 11,230,652,413 UGX
- **Deviation**: 1.6%
- Stake (Real): 14,086,149,529 UGX
- Stake (Free): 0 UGX
- Refund: 2,630 UGX
- Adjustment: 0 UGX
- Revenue: 3,030,913,612 UGX
- No. of Bets: 3413789.0
- Game Type: CTG_multi
- Payout z-score: 3.46

**OP_0006**: Payout 10,831,181,394 UGX
- Type: isolation_forest
- **Actual Payout**: 10,831,181,394 UGX
- **Predicted Payout**: 10,458,830,609 UGX
- **Deviation**: 3.6%
- Stake (Real): 8,214,572,252 UGX
- Stake (Free): 0 UGX
- Refund: 88 UGX
- Adjustment: 0 UGX
- Revenue: -2,616,609,230 UGX
- No. of Bets: 2005563.0
- Game Type: CTG_multi
- Payout z-score: 3.36

---

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
