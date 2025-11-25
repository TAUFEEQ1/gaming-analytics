# Overview

- **Purpose:**: This document explains how to run the pipeline tasks in `tasks/` using `python -m tasks.<task_module>` and describes the rationale, recommended order, outputs, and configuration knobs for each task.
- **Location:**: repository `docs/PIPELINE.md`

## Prerequisites

- **Python environment:**: Create and activate a virtual environment (macOS / zsh):

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

- **Input data:**: Ensure `data/onlineCasino.csv` is present. Several tasks read/write files in `data/` and `output/`.

### How to run tasks

- **General pattern:**: Run a task module via its module name, then pass the Luigi task class name and any parameters. Add `--local-scheduler` for local runs.

- **Examples:**
  - Resample all windows (1/3/5 minutes):

    ```bash
    python -m tasks.resample_windows ResampleAllWindowsTask --local-scheduler
    ```

  - Compute rolling metrics for resampled windows (all):

    ```bash
    python -m tasks.add_rolling_metrics_to_windows AddRollingMetricsAllTask --local-scheduler
    ```

  - Compute rolling metrics for the `interesting` dataset:

    ```bash
    python -m tasks.add_rolling_metrics_interesting AddRollingMetricsInterestingTask --local-scheduler
    ```

  - Compute global z-scores for `interesting` data:

    ```bash
    python -m tasks.global_zscore_interesting GlobalZscoreInterestingTask --local-scheduler
    ```

  - DBSCAN anomaly detection (adjustable `eps` and `min_samples`):

    ```bash
    python -m tasks.dbscan_anomaly_detection DBSCANAnomalyDetectionTask --eps 2 --min-samples 4 --local-scheduler
    ```

  - Compute player averages:

    ```bash
    python -m tasks.compute_player_averages ComputePlayerAveragesTask --local-scheduler
    ```

  - Load generated CSVs into SQLite (script-style; not Luigi):

    ```bash
    python -m tasks.load_to_sqlite --db output/gaming_metrics.db
    ```

### Recommended run order (what runs first and why)

- **1. Isolate interesting columns**: `python -m tasks.isolate_interesting_columns IsolateColumnsTask --local-scheduler`
  - **Why:** Creates `data/interesting_data.csv` by extracting the columns used by downstream tasks (stake/payout/house_net/outpay/time/ID). Many downstream tasks read `data/interesting_data.csv`.

- **2. Resample windows**: `python -m tasks.resample_windows ResampleAllWindowsTask --local-scheduler`
  - **Why:** Produces time-windowed aggregates used for rolling statistics. Outputs are written to `output/windows/`.

- **3. Add rolling metrics to windows**: `python -m tasks.add_rolling_metrics_to_windows AddRollingMetricsAllTask --local-scheduler`
  - **Why:** Computes rolling mean/std and z-scores for columns in the resampled windows files. These outputs are saved in `output/rolling/` and are useful for monitoring or further analysis.

- **4. Add rolling metrics for interesting data**: `python -m tasks.add_rolling_metrics_interesting AddRollingMetricsInterestingTask --local-scheduler`
  - **Why:** Computes rolling values specifically for the `interesting` dataset (e.g., `stake`, `payout`, `house_net`) and writes `output/rolling/interesting_with_rolling.csv`.

- **5. Global z-score on interesting**: `python -m tasks.global_zscore_interesting GlobalZscoreInterestingTask --local-scheduler`
  - **Why:** Computes dataset-wide (global) mean/std and per-row global z-scores for numeric fields in `data/interesting_data.csv`. Produces `output/rolling/interesting_with_global_z.csv`.

- **6. DBSCAN anomaly detection**: `python -m tasks.dbscan_anomaly_detection DBSCANAnomalyDetectionTask --local-scheduler`
  - **Why:** Standardizes features (`stake`, `payout`, `house_net`) and runs DBSCAN to mark anomalies. Produces `output/rolling/interesting_with_dbscan.csv` with `db_anomaly` and `db_cluster` columns.

- **7. Compute player averages**: `python -m tasks.compute_player_averages ComputePlayerAveragesTask --local-scheduler`
  - **Why:** Produces `data/player_averages.csv` with per-player average metrics derived from `data/onlineCasino.csv`.

- **8. Load to SQLite**: `python -m tasks.load_to_sqlite --db output/gaming_metrics.db`
  - **Why:** Consolidates CSV outputs into an SQLite database. By default writes `output/gaming_metrics.db`. It will load `data/interesting_data.csv`, `data/onlineCasino.csv`, and any rolling CSVs under `output/` that match `*with_*.csv`.

### Where outputs land

- **Resampled windows:**: `output/windows/resampled_1min_windows.csv`, `resampled_3min_windows.csv`, `resampled_5min_windows.csv`
- **Rolling outputs (per-window):**: `output/rolling/resampled_1min_windows_with_rolling.csv`, `resampled_3min_windows_with_rolling.csv`, `resampled_5min_windows_with_rolling.csv`
- **Interesting derivatives:**: `data/interesting_data.csv`, `output/rolling/interesting_with_rolling.csv`, `output/rolling/interesting_with_global_z.csv`, `output/rolling/interesting_with_dbscan.csv`
- **Player averages:**: `data/player_averages.csv`
- **Completion markers / logs:**: `output/resample_all_complete.txt`, `output/add_rolling_all_complete.txt`
- **SQLite DB (optional):**: `output/gaming_metrics.db` (default used by `load_to_sqlite`)

### Pipeline stages (conceptual)

- **Ingestion / Extraction:**: `tasks.isolate_interesting_columns` extracts the subset of columns needed for analysis.
- **Windowing / Aggregation:**: `tasks.resample_windows` creates time-based aggregated windows.
- **Feature engineering:**: Rolling statistics and z-scores computed by `add_rolling_metrics_to_windows` and `add_rolling_metrics_interesting`.
- **Anomaly detection:**: Global z-scores (`global_zscore_interesting`) and clustering-based anomalies (`dbscan_anomaly_detection`).
- **Aggregation / summary:**: `compute_player_averages` creates per-player summary metrics.
- **Persistence / delivery:**: `load_to_sqlite` loads CSVs into a local database for queries and downstream use.

#### Parameters & tuning

- **Luigi parameters:** Tasks that accept parameters expose them as Luigi parameters. Example CLI names:
  - `AddRollingMetricsBase.rolling_windows` → `--rolling-windows`
  - `DBSCANAnomalyDetectionTask.eps` → `--eps`
  - `DBSCANAnomalyDetectionTask.min_samples` → `--min-samples`

- **Examples:**
  - Change rolling window count when running rolling metrics:

    ```bash
    python -m tasks.add_rolling_metrics_to_windows AddRollingMetricsAllTask --rolling-windows 5 --local-scheduler
    ```

  - Run DBSCAN with custom parameters:

    ```bash
    python -m tasks.dbscan_anomaly_detection DBSCANAnomalyDetectionTask --eps 2 --min-samples 5 --local-scheduler
    ```

#### Troubleshooting & notes

- **Missing `data/interesting_data.csv`:** Run `IsolateColumnsTask` first.
- **Luigi scheduling:** The code uses plain `luigi.run()` in each module. For local one-off runs add `--local-scheduler` to avoid the central scheduler requirement.
- **File permissions / directories:** Tasks create directories under `output/` and `data/` as needed, but ensure the running user can create files there.
- **Large datasets / memory:** Some tasks read full CSVs into pandas. If memory is constrained, consider sampling or processing in chunks (not implemented by the tasks today).
