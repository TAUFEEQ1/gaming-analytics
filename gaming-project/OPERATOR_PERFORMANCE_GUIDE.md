# Operator Performance Analysis with Z-Score Rankings

## Overview

The `OperatorPerformanceHandler` provides category-aware operator performance analysis using Z-scores to enable fair comparisons across different game categories.

## Why Z-Scores?

Traditional rankings by absolute GGR don't account for the fact that operators compete in different game categories with vastly different revenue potential:

- **RRI_fixedOdds**: ~95% market share, 21 operators
- **RRI_fantasy**: ~2% market share, 1 operator  
- **RRI_casinoGame**: ~1.8% market share, 17 operators
- **RRI_landFixedOdds**: ~1.3% market share, 7 operators
- **RRI_betExchange**: 0% market share, 1 operator

**Z-scores standardize performance within each category:**

```bash
Z-score = (Operator GGR - Category Mean GGR) / Category Std Dev
```

This allows us to:

1. Compare operators across categories on equal footing
2. Identify underperformers relative to their peers
3. Rank operators by how many standard deviations they deviate from their category average

## Performance Tiers

Based on Z-scores:

- **Exceptional**: Z-score > 2 (top 2.3% in category)
- **Above Average**: Z-score > 1 (top 16% in category)
- **Average**: Z-score between -1 and 1 (middle 68%)
- **Below Average**: Z-score between -2 and -1 (bottom 16%)
- **Underperforming**: Z-score < -2 (bottom 2.3%)

## Key Methods

### 1. `calculate_operator_z_scores(start_date, end_date)`

Returns Z-scores for all operators in their respective categories with:

- `total_ggr`: Total GGR for the period
- `z_score`: Standardized performance metric
- `percentile`: Rank within category (0-100)
- `performance_tier`: Human-readable tier
- `category_mean`: Average GGR in category
- `category_std`: Standard deviation in category

### 2. `get_top_performers(n=10, by_category=False)`

Get top N performers:

- `by_category=False`: Top N across all categories by Z-score
- `by_category=True`: Top N per category

### 3. `get_bottom_performers(n=10, by_category=False)`  

Get bottom N performers (same logic as top performers)

### 4. `get_underperformers_cross_category()`

**Critical for regulatory oversight:**
Returns all operators with Z-score < 0 (below their category mean), ranked cross-category. This identifies operators that:

1. Underperform relative to their peers
2. Can be compared regardless of category
3. May need regulatory attention

### 5. `get_operator_summary()`

Comprehensive view of all operators with:

- Weighted average Z-score across categories
- Total GGR across all categories
- Number of categories they operate in
- Overall rank

### 6. `get_category_distribution()`

Market analysis showing:

- Operator count per category
- Total/mean/std GGR per category
- Market share percentages
- Total bets, stakes, payouts

## Example Use Cases

### Regulatory Triage

```python
from dashboard.operator_performance_utils import OperatorPerformanceHandler

handler = OperatorPerformanceHandler()

# Get operators underperforming in their categories
underperformers = handler.get_underperformers_cross_category()
# Result: 30 operators with Z-score < 0, ranked cross-category

# Get worst performers requiring immediate attention
critical = underperformers.head(10)
```

### Performance Dashboards

```python
# Top performers across all categories
top_10 = handler.get_top_performers(n=10, by_category=False)
# Shows MAS (casino), INT (fixed odds), SPO (fantasy) as top 3

# Top performers per category
top_per_cat = handler.get_top_performers(n=5, by_category=True)
# Shows best operators in each game category
```

### Category Analysis

```python
# Market structure
cat_dist = handler.get_category_distribution()
# Shows RRI_fixedOdds dominates with 95% market share

# Category statistics  
cat_stats = handler.calculate_category_stats()
# Mean/std GGR per category for understanding volatility
```

## Current Data Insights

From operator_performance.parquet (343 days, 33 operators):

**Top Performers by Z-score:**

1. MAS (RRI_casinoGame): Z=929.94 - Exceptional dominance in casino
2. INT (RRI_fixedOdds): Z=472.81 - Market leader in fixed odds
3. SPO (RRI_fantasy): Z=168.76 - Only fantasy operator, strong performance

**Underperformers:**

- 30 operators below their category mean (Z < 0)
- SYN (RRI_fixedOdds): Z=-0.60 - Underperforming in main category
- Multiple operators with Z=-0.35 in casinoGame (zero GGR)

**Category Insights:**

- RRI_fixedOdds: Highest volatility (std=851.7M)
- RRI_betExchange: Zero activity (0 GGR, std=0)
- RRI_casinoGame: 17 operators, most competitive

## Integration with Existing Dashboard

The Z-score approach complements your existing:

- **GGR forecasting** (ggr_forecast.parquet) - Adds operator-level granularity
- **Anomaly detection** - Z-scores can flag sudden performance drops
- **Operators list** - Replace mock data with real Z-score rankings
- **Operator detail pages** - Show category context and peer comparison

## Next Steps

1. **Update operators_list view** to use real Z-score data
2. **Add category filter** to operators list page
3. **Create performance comparison** charts showing operators vs category mean
4. **Integrate with anomalies** - Flag when operator Z-score drops significantly
5. **Add trend analysis** - Track Z-score changes over time windows
