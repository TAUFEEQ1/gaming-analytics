# Co-Pilot Guide: Stake Spike Analysis

## Overview

This guide explains the setup for Stake Spike Analysis, which flags unusual spikes or drops in stakes, payouts, and related metrics in gaming data. It combines univariate and multivariate models while providing business-friendly insights.

## Architecture

### 1. Data Sources

- CSV or logs of gaming transactions.
- Key columns: `stake_real_money`, `stake_free_money`, `payout_base_win`, `game_category`, `game_variant`, `transaction_types`, `no_of_bets`, etc.

### 2. ETL Pipeline (Airflow)

- **Airflow** orchestrates tasks.
- Tasks:
  1. `extract_raw_data`: load source files.
  2. `clean_data`: fix missing values, normalize dates.
  3. `feature_engineering`: scaling, dummy variables, PCA for game structure.
  4. `train_regression_model`: fit model predicting `stake_real_money`.
  5. `compute_dbscan_rarity`: detect rare combinations.
  6. `compute_z_scores`: univariate baseline analysis.
  7. `update_dashboard`: prepare summary tables for Streamlit.

### 3. Storage

- **Parquet files** for persistence.
- Optional DuckDB catalog for OLAP queries.
- Suggested folder structure:

```env
/warehouse/
  /raw/
  /clean/
  /features/
  /models/
  /inference/
  /anomaly/
  /reports/
duckdb.db
```

### 4. ML Models

- **Univariate Z-score analysis**: high recall, baseline anomaly detection.
- **Regression Model**: predicts `stake_real_money` using PCA components, dummy transaction types, `no_of_bets`, `stake_free_money`. High precision.
- **DBSCAN Clustering**: identifies rare feature combinations for low-confidence flags.

### 5. Dashboard (Streamlit)

- Sections:
  1. **Overview**: KPIs, total stakes & payouts, distribution plots.
  2. **Stake Spike Analysis – Baseline**: Z-score analysis with business-friendly messaging.
  3. **Regression Insights**: Predicted vs actual stakes, residuals, MAE.
  4. **Rare Categories / Low Confidence**: DBSCAN outputs.
  5. **Filters & Drill-down**: by operator, game_category, date range, transaction type.

### 6. Deployment

- Dockerize Streamlit + DuckDB + ML dependencies.
- Airflow DAGs update Parquet daily.
- Streamlit reads latest Parquet snapshot.
- Optional reverse proxy for authentication.

## Notes & Considerations

- **Z-score**: baseline, high recall, low precision.
- **Regression**: context-aware, high precision, explains variance.
- **DBSCAN**: flags rare categories/low-confidence data.
- **Ground truth**: calibrates MAE thresholds, limited use for rare categories.
- **Thresholds**: kept in business logic, not exposed on dashboard.

## Recommended Tools

- Python 3.11+
- Pandas / NumPy
- Scikit-learn (Regression, DBSCAN, PCA)
- DuckDB
- Parquet files
- Airflow
- Streamlit
- Plotly / Altair for interactive plots
