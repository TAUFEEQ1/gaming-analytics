import luigi
import pandas as pd
import numpy as np

from tasks.resample_windows import (
    Resample1MinWindowsTask,
    Resample3MinWindowsTask,
    Resample5MinWindowsTask,
)


class AddRollingMetricsBase(luigi.Task):
    """Base Luigi task that computes rolling mean and std for numeric columns
    in a resampled windows CSV. Concrete tasks should set `window_minutes`.
    """
    rolling_windows = luigi.IntParameter(default=3)
    min_periods = luigi.IntParameter(default=1)

    # concrete tasks must override
    window_minutes = None

    def input(self):
        return luigi.LocalTarget(f'output/windows/resampled_{self.window_minutes}min_windows.csv')

    def output(self):
        return luigi.LocalTarget(f'output/rolling/resampled_{self.window_minutes}min_windows_with_rolling.csv')

    def run(self):
        df = pd.read_csv(self.input().path, parse_dates=['time'])

        # ensure time is the index for rolling by time-based index (rows are ordered)
        df.set_index('time', inplace=True)

        # operate only on numeric columns
        numeric_cols = df.select_dtypes(include='number').columns.tolist()

        for col in numeric_cols:
            mean_col = f"{col}_rolling_mean_{self.rolling_windows}"
            std_col = f"{col}_rolling_std_{self.rolling_windows}"
            df[mean_col] = df[col].rolling(window=self.rolling_windows, min_periods=self.min_periods).mean()
            # use ddof=0 so std of a single value is 0 rather than NaN
            df[std_col] = df[col].rolling(window=self.rolling_windows, min_periods=self.min_periods).std(ddof=0)
            # z-score using the rolling mean/std; fill infs and NaNs with 0
            z_col = f"{col}_zscore_{self.rolling_windows}"
            z = (df[col] - df[mean_col]) / df[std_col]
            df[z_col] = z.replace([np.inf, -np.inf], 0).fillna(0)

        # Backfill numeric NaNs with each column's mean (useful for empty windows)
        numeric_all = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_all:
            col_mean = df[col].mean()
            if pd.notna(col_mean):
                df[col] = df[col].fillna(col_mean)

        # write out with time as a column again
        df.reset_index().to_csv(self.output().path, index=False)

    def requires(self):
        """Ensure the corresponding resample task runs first.

        This allows AddRollingMetrics tasks to be executed in parallel
        by requiring their upstream resample tasks.
        """
        if self.window_minutes == 1:
            return Resample1MinWindowsTask()
        if self.window_minutes == 3:
            return Resample3MinWindowsTask()
        if self.window_minutes == 5:
            return Resample5MinWindowsTask()
        return None


class AddRollingMetrics1MinTask(AddRollingMetricsBase):
    window_minutes = 1


class AddRollingMetrics3MinTask(AddRollingMetricsBase):
    window_minutes = 3


class AddRollingMetrics5MinTask(AddRollingMetricsBase):
    window_minutes = 5


class AddRollingMetricsAllTask(luigi.Task):
    """Run all AddRollingMetrics tasks in parallel (each depends on its resample)."""
    def requires(self):
        return [
            AddRollingMetrics1MinTask(),
            AddRollingMetrics3MinTask(),
            AddRollingMetrics5MinTask(),
        ]

    def output(self):
        return luigi.LocalTarget('output/add_rolling_all_complete.txt')

    def run(self):
        with self.output().open('w') as f:
            f.write('All rolling-metrics tasks completed successfully\n')


if __name__ == '__main__':
    luigi.run()

