# Gaming Operator Anomaly Detection - User Guide

## Overview

This guide explains how to use the anomaly detection datasets for stake and payout analysis in dashboards and presentations. The system detects unusual patterns in both stake (betting volume) and payout (winnings) across all 7 operator tiers.

---

## 📁 Available Files

### 1. **Combined Anomalies (Full Dataset)**

- **File:** `combined_anomalies_full_detail.parquet` (462.6 KB)
- **Records:** 5,250 operator-days
- **Contains:** ALL records (normal + anomalies)
- **Use for:** Dashboards, trend analysis, overall monitoring

### 2. **Anomalies Only (Filtered Dataset)**

- **File:** `anomalies_only_full_detail.parquet` (70.8 KB)
- **Records:** 553 anomalous operator-days
- **Contains:** Only flagged anomalies
- **Use for:** Investigation, drill-down analysis, reporting

---

## 📊 Data Structure

### Key Identification Fields

| Field | Type | Description |
|-------|------|-------------|
| `date` | Date | Transaction date |
| `operator` | String | Operator code (e.g., INT, MAS, BLU) |
| `operator_tier` | String | Risk tier (Top Tier, Large, Large+, Medium+, Medium, Small, Micro) |

### Anomaly Classification

| Field | Type | Description |
|-------|------|-------------|
| `is_anomaly_combined` | Integer | 1 = Anomaly detected (stake OR payout), 0 = Normal |
| `anomaly_type` | String | 'Normal', 'Stake Only', 'Payout Only', 'Both' |
| `is_anomaly_stake` | Integer | 1 = Stake anomaly, 0 = Normal stake |
| `is_anomaly_payout` | Integer | 1 = Payout anomaly, 0 = Normal payout |

### Stake Drill-Down Fields

| Field | Type | Description | Example Use |
|-------|------|-------------|-------------|
| `total_stake` | Float | Actual stake amount | Show what customers bet |
| `stake_predicted` | Float | Expected stake (model prediction) | Compare against actual |
| `stake_deviation` | Float | Difference (actual - predicted) | Absolute deviation amount |
| `stake_deviation_pct` | Float | Percentage deviation | Key anomaly indicator |
| `anomaly_score_stake` | Float | Isolation Forest score (-1 to 0) | Lower = more anomalous |

### Payout Drill-Down Fields

| Field | Type | Description | Example Use |
|-------|------|-------------|-------------|
| `total_payout` | Float | Actual payout amount | Show what customers won |
| `payout_predicted` | Float | Expected payout (model prediction) | Compare against actual |
| `payout_deviation` | Float | Difference (actual - predicted) | Absolute deviation amount |
| `payout_deviation_pct` | Float | Percentage deviation | Key anomaly indicator |
| `anomaly_score_payout` | Float | Isolation Forest score (-1 to 0) | Lower = more anomalous |

### Game Category Context

8 additional columns showing game type distribution:

- `pct_RRI_casinoGame_stake` / `pct_RRI_casinoGame_payout`
- `pct_RRI_fantasy_stake` / `pct_RRI_fantasy_payout`
- `pct_RRI_fixedOdds_stake` / `pct_RRI_fixedOdds_payout`
- `pct_RRI_landFixedOdds_stake` / `pct_RRI_landFixedOdds_payout`

---

## 🎯 Common Use Cases

### 1. **Dashboard Overview**

```python
import pandas as pd

# Load full dataset
df = pd.read_parquet('combined_anomalies_full_detail.parquet')

# Summary metrics
total_days = len(df)
anomaly_count = df['is_anomaly_combined'].sum()
anomaly_rate = (anomaly_count / total_days) * 100

print(f"Total operator-days: {total_days:,}")
print(f"Anomalies detected: {anomaly_count:,} ({anomaly_rate:.2f}%)")
```

**Key Metrics to Display:**

- Total anomalies: 553 (10.5% of all records)
- Stake-only anomalies: 267
- Payout-only anomalies: 268
- Both stake + payout: 150

### 2. **Filter by Anomaly Type**

```python
# Stake anomalies only
stake_issues = df[df['is_anomaly_stake'] == 1]

# Payout anomalies only
payout_issues = df[df['is_anomaly_payout'] == 1]

# High-risk: Both stake and payout anomalies
critical = df[df['anomaly_type'] == 'Both']
```

### 3. **Tier-Based Analysis**

```python
# Anomalies by tier
tier_summary = df.groupby('operator_tier').agg({
    'is_anomaly_combined': ['sum', 'count'],
    'stake_deviation_pct': 'mean',
    'payout_deviation_pct': 'mean'
})
```

**Expected Anomaly Rates by Tier:**

- **Micro:** 17.2% (highest risk)
- **Small:** 10.2%
- **Medium:** 7.2%
- **Medium+:** 5.4%
- **Large:** 3.1%
- **Large+:** 3.4%
- **Top Tier:** 2.3% (lowest risk)

### 4. **Operator Drill-Down**

```python
# Investigate specific operator
operator_code = 'INT'
operator_history = df[df['operator'] == operator_code]

# Show anomalies for this operator
operator_anomalies = operator_history[operator_history['is_anomaly_combined'] == 1]

# Display details
for _, row in operator_anomalies.iterrows():
    print(f"Date: {row['date']}")
    print(f"Type: {row['anomaly_type']}")
    if row['is_anomaly_stake'] == 1:
        print(f"  Stake: {row['total_stake']:,.0f} (expected {row['stake_predicted']:,.0f})")
        print(f"  Deviation: {row['stake_deviation_pct']:.2f}%")
    if row['is_anomaly_payout'] == 1:
        print(f"  Payout: {row['total_payout']:,.0f} (expected {row['payout_predicted']:,.0f})")
        print(f"  Deviation: {row['payout_deviation_pct']:.2f}%")
```

### 5. **Time-Series Analysis**

```python
# Daily anomaly trends
daily_anomalies = df.groupby('date')['is_anomaly_combined'].sum().reset_index()

# Plot trend (for visualization)
import matplotlib.pyplot as plt
plt.plot(daily_anomalies['date'], daily_anomalies['is_anomaly_combined'])
plt.title('Daily Anomaly Count')
plt.xlabel('Date')
plt.ylabel('Number of Anomalies')
```

### 6. **Severity Ranking**

```python
# Load pre-filtered anomalies
anomalies = pd.read_parquet('anomalies_only_full_detail.parquet')

# Calculate combined severity
anomalies['severity'] = (
    anomalies['stake_deviation_pct'].abs().fillna(0) + 
    anomalies['payout_deviation_pct'].abs().fillna(0)
)

# Top 10 most severe
top_10 = anomalies.nlargest(10, 'severity')[
    ['date', 'operator', 'operator_tier', 'anomaly_type', 
     'stake_deviation_pct', 'payout_deviation_pct', 'severity']
]
```

---

## 🚨 Interpretation Guidelines

### Anomaly Scores

- **Isolation Forest Score:** Ranges from -1 (most anomalous) to 0 (normal)
- Values < -0.5 indicate strong anomalies
- Combined with deviation % for severity assessment

### Deviation Percentages

- **Low:** < 20% - Minor fluctuation
- **Medium:** 20-50% - Moderate concern
- **High:** 50-100% - Significant anomaly
- **Critical:** > 100% - Extreme deviation requiring investigation

### Risk Prioritization

1. **Critical (Immediate Action):**
   - `anomaly_type == 'Both'` (stake + payout)
   - Micro/Small tier operators
   - Deviation > 100%

2. **High (Review Required):**
   - `anomaly_type == 'Stake Only'` or `'Payout Only'`
   - Deviation 50-100%
   - Repeated anomalies (same operator, multiple days)

3. **Medium (Monitor):**
   - Single anomaly with deviation 20-50%
   - Large/Top tier operators

---

## 📈 Dashboard Visualizations

### Recommended Charts

1. **Summary Cards**
   - Total anomalies count
   - Anomaly rate by tier
   - Stake vs Payout anomaly split

2. **Time Series**
   - Daily anomaly count trend
   - Operator-specific anomaly timeline

3. **Tier Comparison**
   - Bar chart: Anomalies by tier
   - Heatmap: Operator x Date anomaly matrix

4. **Drill-Down Table**
   - Filterable by: date range, operator, tier, anomaly type
   - Columns: Date, Operator, Type, Stake Deviation %, Payout Deviation %
   - Click-through to full details

5. **Scatter Plot**
   - X-axis: Stake deviation %
   - Y-axis: Payout deviation %
   - Color: Anomaly type
   - Size: Severity score

---

## 🔍 Example Queries for Dashboards

### PowerBI DAX Examples

**Anomaly Count Measure:**

```dax
Anomaly Count = 
CALCULATE(
    COUNT('Anomalies'[date]),
    'Anomalies'[is_anomaly_combined] = 1
)
```

**Anomaly Rate:**

```dax
Anomaly Rate = 
DIVIDE(
    [Anomaly Count],
    COUNT('Anomalies'[date]),
    0
)
```

**Critical Anomalies (Both):**

```dax
Critical Anomalies = 
CALCULATE(
    COUNT('Anomalies'[date]),
    'Anomalies'[anomaly_type] = "Both"
)
```

### SQL Queries (if loaded to database)

**Top 10 Operators by Anomaly Count:**

```sql
SELECT 
    operator,
    operator_tier,
    COUNT(*) as anomaly_count,
    AVG(stake_deviation_pct) as avg_stake_dev,
    AVG(payout_deviation_pct) as avg_payout_dev
FROM anomalies_only_full_detail
GROUP BY operator, operator_tier
ORDER BY anomaly_count DESC
LIMIT 10;
```

**Daily Anomaly Trend:**

```sql
SELECT 
    date,
    COUNT(*) as total_anomalies,
    SUM(CASE WHEN anomaly_type = 'Stake Only' THEN 1 ELSE 0 END) as stake_only,
    SUM(CASE WHEN anomaly_type = 'Payout Only' THEN 1 ELSE 0 END) as payout_only,
    SUM(CASE WHEN anomaly_type = 'Both' THEN 1 ELSE 0 END) as both
FROM anomalies_only_full_detail
GROUP BY date
ORDER BY date;
```

---

## 📋 Data Quality Notes

### Coverage

- **Date Range:** 2024-12-30 to 2025-12-07 (343 days)
- **Operators:** 28 operators across 7 tiers
- **Records:** 5,250 operator-days analyzed
- **Anomalies:** 553 flagged (10.5%)

### Model Details

- **Stake Models:** Tier-specific regression with AR lag features
- **Payout Models:** Tier-specific regression with AR lag features
- **Anomaly Detection:** Isolation Forest (risk-based contamination rates)
- **Features:** Deviation % + game category distribution

### Confidence Levels

- **High Confidence:** Anomalies with deviation > 50%
- **Medium Confidence:** Anomalies with deviation 20-50%
- **Review:** Edge cases with deviation < 20% (may be normal variance)

---

## 🛠️ Troubleshooting

### Missing Values

- Some records may have `NaN` for stake or payout metrics if data unavailable
- Use `.fillna(0)` when calculating aggregates
- Filter by `.notna()` when drilling down

### Loading Performance

- **Full Dataset (462 KB):** Use for dashboards with filters
- **Anomalies Only (71 KB):** Use for investigation/reports
- Consider date range filters for large dashboards

### Date Handling

```python
# Ensure date is datetime type
df['date'] = pd.to_datetime(df['date'])

# Filter by date range
start_date = '2025-01-01'
end_date = '2025-03-31'
filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
```

---

## 📞 Support

For questions about:

- **Data Structure:** See column descriptions above
- **Interpretation:** See guidelines section
- **Model Details:** Contact analytics team
- **New Features:** Submit enhancement request

---

## 🔄 Updates

**Last Updated:** December 16, 2025

**Version:** 1.0

**Changes in This Version:**

- Initial release with full stake + payout anomaly detection
- All 7 tiers included (Micro and Small added)
- Combined anomaly flagging (stake OR payout)
- Full drill-down details for investigation
