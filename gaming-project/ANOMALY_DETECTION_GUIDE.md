# Gaming Operator Anomaly Detection - User Guide

## Overview

This guide explains how to use the anomaly detection datasets for stake and payout analysis in dashboards and presentations. The system detects unusual patterns in both stake (betting volume) and payout (winnings) across all 7 operator tiers.

---

## 📁 Available Files

### Main Anomaly Detection Files

#### 1. **Combined Anomalies (Full Dataset)**

- **File:** `combined_anomalies_full_detail.parquet` (462.6 KB)
- **Records:** 5,250 operator-days
- **Contains:** ALL records (normal + anomalies)
- **Operators:** 28 operators with sufficient data
- **Use for:** Dashboards, trend analysis, overall monitoring

#### 2. **Anomalies Only (Filtered Dataset)**

- **File:** `anomalies_only_full_detail.parquet` (70.8 KB)
- **Records:** 553 anomalous operator-days
- **Contains:** Only flagged anomalies
- **Use for:** Investigation, drill-down analysis, reporting

### Excluded Data Files (Separate Monitoring)

#### 3. **Excluded Operators and Zero Stakes**

- **File:** `excluded_operators_and_zero_stakes.parquet`
- **Contains:** Records excluded from ML-based anomaly detection
- **Includes:**
  - 5 missing operators (insufficient data or no tier assignment)
  - All zero stake entries (inactivity/downtime)
  - Combined de-duplicated dataset
- **Use for:** Activity monitoring, downtime tracking, threshold-based alerts
- **Additional Columns:**
  - `exclusion_reason` - Why record was excluded
  - `is_zero_stake` - Flag for zero stake days
  - `is_missing_operator` - Flag for operators not in anomaly detection
  - `is_zero_payout` - Flag for zero payout days
  - `stake_to_payout_ratio` - Activity metric

#### 4. **Excluded Operators Summary**

- **File:** `excluded_operators_summary.parquet`
- **Contains:** Per-operator statistics for excluded data
- **Columns:**
  - `operator` - Operator code
  - `Record_Count` - Total records for this operator
  - `Total_Stake` / `Avg_Stake` - Stake aggregates
  - `Total_Payout` / `Avg_Payout` - Payout aggregates
  - `Zero_Stake_Days` - Count of inactive days
  - `Zero_Payout_Days` - Count of zero payout days
  - `Is_Missing_Operator` - 1 if not in anomaly detection, 0 otherwise
- **Use for:** Understanding why operators were excluded, identifying when operators have sufficient data

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

## ⚠️ Data Exclusions and Limitations

### Excluded Operators

**Total Operators in Dataset:** 33  
**Operators in Anomaly Detection:** 28  
**Excluded Operators:** 5

**Dataset:** See `excluded_operators_and_zero_stakes.parquet` for complete data

**Why operators are excluded:**

1. **Insufficient Training Data**
   - Models require at least 7-10 days of data with autoregressive lag features
   - Operators with sparse data cannot generate reliable predictions
   - Example: New operators with < 10 days of history

2. **No Tier Assignment**
   - Operators not classified into one of the 7 risk tiers
   - Cannot apply tier-specific models without tier classification
   - These may be test operators or pending classification

3. **Inactive/Zero Stake Records**
   - Operators with predominantly zero stakes excluded
   - These represent system downtime or data gaps, not operational anomalies
   - See `Zero Stake Entries` section below for details

4. **Data Quality Issues**
   - Missing critical fields (dates, stakes, payouts)
   - Inconsistent reporting periods
   - Data gaps preventing lag feature creation

**How to Identify Excluded Operators:**

```python
import pandas as pd

# Load excluded operators summary
excluded_summary = pd.read_parquet('excluded_operators_summary.parquet')

# Filter to missing operators only
missing_ops = excluded_summary[excluded_summary['Is_Missing_Operator'] == 1]

print("Missing Operators:")
for _, row in missing_ops.iterrows():
    print(f"  {row['operator']}: {row['Record_Count']} days, "
          f"{row['Zero_Stake_Days']} zero stakes ({row['Zero_Stake_Days']/row['Record_Count']*100:.1f}%)")
```

**Recommendation:** Excluded operators should be analyzed separately using different methods:

- **Threshold-based alerts:** Flag if stake changes >50% day-over-day
- **Manual review:** Investigate operators with <30 days of data
- **Readiness check:** Monitor until operator has 10+ consecutive active days, then re-include in anomaly detection

### Zero Stake Entries

**Dataset:** All zero stake records available in `excluded_operators_and_zero_stakes.parquet`

**Impact:** Zero stake entries (days with no betting activity) are present in the original dataset but excluded from anomaly detection.

**Statistics:**

- Total operators with zero stake days: See `excluded_operators_summary.parquet`
- Filter by: `is_zero_stake == 1` in excluded operators file

**Why Zero Stakes Are Excluded:**

- Cannot calculate meaningful deviation percentages (division by zero)
- Do not represent operational anomalies but rather inactivity
- Would bias model training toward detecting activity vs. inactivity
- Models trained on active days cannot predict inactive days

**Handling Zero Stakes:**

1. **Load Zero Stake Data:**

   ```python
   import pandas as pd
   
   # Load excluded data
   excluded = pd.read_parquet('excluded_operators_and_zero_stakes.parquet')
   
   # Filter to zero stake entries only
   zero_stakes = excluded[excluded['is_zero_stake'] == 1]
   
   print(f"Total zero stake days: {len(zero_stakes):,}")
   print(f"Operators affected: {zero_stakes['operator'].nunique()}")
   
   # Group by operator to see inactivity patterns
   inactivity = zero_stakes.groupby('operator').agg({
       'date': 'count',
       'total_payout': 'sum'  # Check if any payouts during "zero stake" days
   }).rename(columns={'date': 'zero_stake_days'})
   ```

2. **Consecutive Zero Stake Alert:**

   ```python
   # Detect consecutive zero stake periods
   excluded['date'] = pd.to_datetime(excluded['date'])
   excluded = excluded.sort_values(['operator', 'date'])
   
   for op in excluded['operator'].unique():
       op_data = excluded[excluded['operator'] == op].copy()
       op_data['consecutive_zeros'] = (
           op_data['is_zero_stake'] * 
           (op_data.groupby((op_data['is_zero_stake'] != op_data['is_zero_stake'].shift()).cumsum()).cumcount() + 1)
       )
       
       max_consecutive = op_data['consecutive_zeros'].max()
       if max_consecutive >= 3:
           print(f"⚠️  {op}: {max_consecutive} consecutive zero stake days")
   ```

3. **Activity Rate Dashboard:**

   ```python
   # Calculate activity rate per operator
   summary = pd.read_parquet('excluded_operators_summary.parquet')
   
   summary['activity_rate'] = (
       (summary['Record_Count'] - summary['Zero_Stake_Days']) / 
       summary['Record_Count'] * 100
   ).round(2)
   
   # Flag low activity operators
   low_activity = summary[summary['activity_rate'] < 50]
   print("Low Activity Operators (<50% active days):")
   print(low_activity[['operator', 'Record_Count', 'Zero_Stake_Days', 'activity_rate']])
   ```

4. **Separate Monitoring Dashboard:**
   - Track zero stake days separately as "downtime" metric
   - Alert if operator has extended period of zero stakes (>3 consecutive days)
   - Use different thresholds than anomaly detection
   - Monitor reactivation patterns

**Zero Stakes May Indicate:**

- **Planned maintenance/downtime:** Expected, coordinate with operations team
- **System outages:** Unplanned, requires immediate investigation
- **Regulatory suspension:** Check compliance status
- **Data collection failures:** Verify data pipeline health
- **Operator closure:** Check business status

**Best Practice Alerts:**

- **Warning:** 1-2 consecutive zero stake days
- **Critical:** 3+ consecutive zero stake days
- **Investigation:** Any operator with >20% zero stake days over 30-day period

### Zero Payout Entries

Similar considerations apply to zero payout entries, though these can occur naturally on days where customers place bets but no one wins, making them less reliable as activity indicators than zero stakes.

**Distinction:**

- **Zero Stake:** Definite inactivity (no betting occurred)
- **Zero Payout:** May be normal (bets placed but no wins) or indicate payout processing issues

**Analysis:**

```python
# Zero payout but non-zero stake (normal gambling variance)
normal_zero_payout = excluded[(excluded['is_zero_payout'] == 1) & 
                               (excluded['is_zero_stake'] == 0)]

# Both zero (true inactivity)
true_inactive = excluded[(excluded['is_zero_payout'] == 1) & 
                         (excluded['is_zero_stake'] == 1)]

print(f"Normal zero payout days: {len(normal_zero_payout):,}")
print(f"True inactive days (both zero): {len(true_inactive):,}")
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
