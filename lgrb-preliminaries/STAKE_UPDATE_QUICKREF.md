# Quick Reference: Stake Models Update

## What Was Done

### 📊 **Data Source Fixed**

```python
# BEFORE (Missing free money)
total_stake = stake_real_money

# AFTER (Complete)
total_stake = stake_real_money + stake_free_money

```bash
- **Impact:** 0.019% overall, but 4.4% for BLU, 100% for GAM
```

---

### 🔍 **Zero-Stake Filtering Added**

```bash
Original Data: 8,203 operator-days
    ↓
Categorization:
├── Active (stake > 0):         6,998 rows → ✅ USE FOR MODELING
├── No-activity (both = 0):     1,017 rows → ℹ️  Report separately
└── Data errors (stake=0, bets>0): 188 rows → ⚠️  Remove & investigate
```

---

### 📓 **Notebooks Updated**

#### stake_forecasting_models.ipynb

- ✅ Added Section 0: Zero-filtering logic
- ✅ Modified Section 1: Use filtered data
- ✅ Added data quality summary
- Status: **Ready to run**

#### stake_anomaly_detection.ipynb

- ✅ Added Section 0: Zero-filtering documentation
- ✅ Modified Section 1: Filter and verify data
- ✅ Added data quality summary
- Status: **Ready to run** (after forecasting models)

---

## To Run

### Step 1: Re-run Forecasting Models

```bash
# Open stake_forecasting_models.ipynb
# Execute all cells (will take ~5-10 minutes)
# Verify outputs generated:
#   - warehouse/data/stake_predictions.parquet
#   - warehouse/data/stake_model_performance.csv
#   - warehouse/data/stake_data_errors.csv (188 rows)
#   - warehouse/data/models/stake_model_*.pkl (7 files)
```

### Step 2: Re-run Anomaly Detection

```bash
# Open stake_anomaly_detection.ipynb  
# Execute all cells (will take ~5-10 minutes)
# Verify outputs generated:
#   - warehouse/data/stake_anomalies.parquet
#   - warehouse/data/stake_anomalies_tier_specific.parquet
#   - warehouse/data/models/stake_anomaly_*.pkl (7 files)
```

### Step 3: Verify Improvements

```python
# Check file timestamps (should be after 23:32:56)
import os
import datetime

files_to_check = [
    'warehouse/data/stake_predictions.parquet',
    'warehouse/data/stake_anomalies.parquet'
]

for f in files_to_check:
    mtime = os.path.getmtime(f)
    print(f"{f}: {datetime.datetime.fromtimestamp(mtime)}")
```

---

## Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Training Data** | 8,203 rows (with errors) | 6,998 rows (clean) | -14.7% (cleaner) |
| **BLU Stake Accuracy** | Missing 4.4% | Complete | +4.4% |
| **GAM Stake Accuracy** | $0 (100% missing) | Complete | +100% |
| **Data Errors** | Mixed in training | Removed & logged | 188 rows saved |
| **False Anomalies** | Higher (from errors) | Lower (clean data) | Expected -15-20% |

---

## Key Files

### Input (Updated)

- `warehouse/data/operator_performance.parquet` ✅ (2024-12-15 23:32:56)

### Output (To Regenerate)

- `warehouse/data/stake_predictions.parquet` ⏳
- `warehouse/data/stake_anomalies.parquet` ⏳
- `warehouse/data/stake_data_errors.csv` ⏳

### Documentation

- `STAKE_MODELS_UPDATE_SUMMARY.md` - Full details
- `payout_eda.ipynb` - Investigation history
- Updated notebooks with new Section 0

---

## Quick Checks

### ✅ Verification Checklist

- [x] stake_free_money column verified
- [x] GGR formula verified correct
- [x] Zero-stake categories defined
- [x] Notebooks updated with filtering
- [ ] Forecasting models re-run
- [ ] Anomaly detection re-run
- [ ] Outputs have recent timestamps
- [ ] stake_data_errors.csv contains 188 rows

### 🎯 Success Indicators

After re-running both notebooks:

1. **No errors during execution** ✓
2. **All output files generated** ✓
3. **File timestamps > 2024-12-15 23:32:56** ✓
4. **stake_data_errors.csv has 188 rows** ✓
5. **Model performance metrics similar or improved** ✓

---

## Operator-Specific Notes

| Operator | Free Money % | Data Errors | Notes |
|----------|--------------|-------------|-------|
| **GAM** | 100% | 0 | Pure promotional (UGX 800 total) |
| **BLU** | 4.4% | 2 | Heavy promotions (UGX 265M) |
| **ABE** | 1.9% | 181 | **⚠️ Major data quality issue** |
| **ADV** | 3.7% | 0 | Moderate promotions |
| **Others** | <2% | 5 | Minor impact |

**Action Required:** Investigate ABE operator's 181 days of zero-stake + bets data
