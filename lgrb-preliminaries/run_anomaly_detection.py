"""
Run the complete hybrid anomaly detection pipeline.

This script orchestrates the full pipeline:
1. Filter and extract data
2. Train hybrid models (regression + isolation forest)
3. Detect anomalies using statistical outlier detection
4. Generate results in warehouse/data/

Usage:
    python run_anomaly_detection.py
"""
import luigi
from warehouse.tasks.detect_anomalies import DetectAnomalies

if __name__ == '__main__':
    luigi.build(
        [DetectAnomalies()],
        local_scheduler=True,
        log_level='INFO'
    )
