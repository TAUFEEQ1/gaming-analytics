import luigi
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN


class DBSCANAnomalyDetectionTask(luigi.Task):
    """Run DBSCAN anomaly detection on interesting_with_global_z.csv.
    
    Scales stake, payout, house_net with StandardScaler, then applies DBSCAN.
    Adds a `db_anomaly` column: 1 for anomaly (cluster label -1), 0 otherwise.
    Writes output to `output/rolling/interesting_with_dbscan.csv`.
    """
    eps = luigi.FloatParameter(default=0.5)
    min_samples = luigi.IntParameter(default=5)

    def requires(self):
        from tasks.global_zscore_interesting import GlobalZscoreInterestingTask
        return GlobalZscoreInterestingTask()

    def output(self):
        out = Path('output/rolling')
        out.mkdir(parents=True, exist_ok=True)
        return luigi.LocalTarget(str(out / 'interesting_with_dbscan.csv'))

    def run(self):
        df = pd.read_csv(self.input().path, parse_dates=['time'])

        # select features for DBSCAN
        feature_cols = ['stake', 'payout', 'house_net']
        X = df[feature_cols].values

        # standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # run DBSCAN
        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        labels = dbscan.fit_predict(X_scaled)

        # anomalies are labeled -1 by DBSCAN
        df['db_anomaly'] = (labels == -1).astype(int)
        df['db_cluster'] = labels

        # write output
        df.to_csv(self.output().path, index=False)


if __name__ == '__main__':
    luigi.run()
