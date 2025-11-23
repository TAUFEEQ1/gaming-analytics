import luigi
import pandas as pd
import numpy as np
from pathlib import Path


class AddRollingMetricsInterestingTask(luigi.Task):
    """Compute rolling mean, std and z-score for `stake` and `payout`

    Reads `data/interesting_data.csv` and writes `output/rolling/interesting_with_rolling.csv`.
    """
    rolling_windows = luigi.IntParameter(default=1)
    min_periods = luigi.IntParameter(default=1)

    def input(self):
        return luigi.LocalTarget('data/interesting_data.csv')

    def output(self):
        out = Path('output/rolling')
        out.mkdir(parents=True, exist_ok=True)
        return luigi.LocalTarget(str(out / 'interesting_with_rolling.csv'))

    def run(self):
        df = pd.read_csv(self.input().path, parse_dates=['time'])

        # ensure time is the index for rolling operations
        df.set_index('time', inplace=True)

        # operate only on the two columns requested
        cols = [c for c in ('stake', 'payout','house_net','outpay') if c in df.columns]

        for col in cols:
            mean_col = f"{col}_rolling_mean_{self.rolling_windows}"
            std_col = f"{col}_rolling_std_{self.rolling_windows}"
            z_col = f"{col}_zscore_{self.rolling_windows}"

            rolling_mean = df[col].rolling(window=self.rolling_windows, min_periods=self.min_periods).mean()
            # use ddof=0 so that std of single-value window is 0 (not NaN)
            rolling_std = df[col].rolling(window=self.rolling_windows, min_periods=self.min_periods).std(ddof=0)

            df[mean_col] = rolling_mean
            df[std_col] = rolling_std

            # z-score; avoid division-by-zero producing infs and fill NaNs with 0
            z = (df[col] - df[mean_col]) / df[std_col]
            z = z.replace([np.inf, -np.inf], 0).fillna(0)
            df[z_col] = z

        # Backfill numeric NaNs with each column's mean (non-inplace to avoid chained-assignment warnings)
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_cols:
            col_mean = df[col].mean()
            if pd.notna(col_mean):
                df[col] = df[col].fillna(col_mean)

        # write out with time as a column again
        df.reset_index().to_csv(self.output().path, index=False)


if __name__ == '__main__':
    luigi.run()
