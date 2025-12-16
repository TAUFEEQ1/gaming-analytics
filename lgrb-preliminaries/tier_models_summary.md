# Tier-Specific Payout Models with Per-Record Residuals

## Model Performance Summary

### With Winsorization + Optimized AR Features

| Tier | AR Features | R² Score | Records | Status |
|------|-------------|----------|---------|--------|
| **Large** | ✅ Yes | **0.9896** | 340 | Excellent |
| **Medium+** | ✅ Yes | **0.9818** | 341 | Excellent |
| **Large+** | ✅ Yes | **0.8715** | 278 | Very Good |
| **Top Tier** | ✅ Yes | **0.5951** | 342 | Moderate |
| **Small** | ✅ Yes | **0.5663** | 334 | Moderate |
| **Micro** | ✅ Yes | **0.5393** | 337 | Moderate (improved from 0.35) |
| **Medium** | ❌ No | **0.4642** | 343 | Moderate (AR hurt performance) |

Total Records: 2,315 individual daily tier aggregations

## Key Findings

### 1. Winsorization is Critical

- **Medium tier** went from R²=0.01 to R²=0.46 with winsorization (99th percentile capping)
- Extreme jackpot payouts were breaking the linear relationship
- Without winsorization, models couldn't capture the underlying patterns

### 2. AR Features Help Most Tiers

- **Top Tier**: R²=0.60 with AR (improvement)
- **Large**: R²=0.99 with AR (excellent)  
- **Large+**: R²=0.87 with AR (very good)
- **Medium+**: R²=0.98 with AR (excellent)
- **Small**: R²=0.57 with AR (moderate)
- **Micro**: R²=0.54 with AR vs 0.35 without AR (+54% improvement)

### 3. Medium Tier Exception

- **Medium tier**: R²=0.46 without AR vs R²=0.01 with AR
- AR features (stake_lag1, bets_lag1, won_lag1) introduced noise
- Keeping it simple: only current-day features (total_stake, total_bets, bets_won_cnt)
- Winsorization + simple features = best performance

## Per-Record Residuals Generated

✅ **All 2,315 records now have individual residuals calculated**:

- `payout_predicted`: Model prediction for that specific day/tier
- `payout_deviation`: Actual - Predicted (the residual)

These residuals will be used for:

1. **Isolation Forest** anomaly detection per tier
2. Identifying unusual payout patterns
3. Detecting potential gaming/fraud activities
4. Business insights on operator behavior

## Feature Configuration

```python
tier_configs = {
    'Top Tier': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1'],
    'Large': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1'],
    'Large+': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1'],
    'Medium+': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1'],
    'Medium': ['total_stake', 'total_bets', 'bets_won_cnt'],  # No AR features!
    'Small': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1'],
    'Micro': ['total_stake', 'total_bets', 'bets_won_cnt', 'stake_lag1', 'bets_lag1', 'won_lag1']
}
```

## Next Steps

1. ✅ Per-record residuals calculated for all 2,315 records
2. ⏳ Run Isolation Forest anomaly detection (Cell 21)
3. ⏳ Save anomaly results to parquet file (Cell 22)
4. ⏳ Analyze and visualize anomalies

---
*Models trained with optimized feature sets and winsorization*  
*Residuals ready for distribution-based anomaly detection*
