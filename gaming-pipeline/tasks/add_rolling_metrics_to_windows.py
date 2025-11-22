import luigi
import pandas as pd
import numpy as np

from tasks.resample_windows import (
    Resample15MinWindowsTask,
    Resample30MinWindowsTask,
    Resample60MinWindowsTask,
    Resample120MinWindowsTask,
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
            df[std_col] = df[col].rolling(window=self.rolling_windows, min_periods=self.min_periods).std()
            # z-score using the rolling mean/std; will be filled later if NaN
            z_col = f"{col}_zscore_{self.rolling_windows}"
            df[z_col] = (df[col] - df[mean_col]) / df[std_col]
            # Replace infinite z-scores (std == 0) with 0
            df[z_col].replace([np.inf, -np.inf], 0, inplace=True)

        # Backfill numeric NaNs with each column's mean (useful for empty windows)
        numeric_all = df.select_dtypes(include='number').columns.tolist()
        for col in numeric_all:
            col_mean = df[col].mean()
            if pd.notna(col_mean):
                df[col].fillna(col_mean, inplace=True)

        # write out with time as a column again
        df.reset_index().to_csv(self.output().path, index=False)

    def requires(self):
        """Ensure the corresponding resample task runs first.

        This allows AddRollingMetrics tasks to be executed in parallel
        by requiring their upstream resample tasks.
        """
        if self.window_minutes == 15:
            return Resample15MinWindowsTask()
        if self.window_minutes == 30:
            return Resample30MinWindowsTask()
        if self.window_minutes == 60:
            return Resample60MinWindowsTask()
        if self.window_minutes == 120:
            return Resample120MinWindowsTask()
        return None


class AddRollingMetrics15MinTask(AddRollingMetricsBase):
    window_minutes = 15


class AddRollingMetrics30MinTask(AddRollingMetricsBase):
    window_minutes = 30


class AddRollingMetrics60MinTask(AddRollingMetricsBase):
    window_minutes = 60


class AddRollingMetrics120MinTask(AddRollingMetricsBase):
    window_minutes = 120


class AddRollingMetricsAllTask(luigi.Task):
    """Run all AddRollingMetrics tasks in parallel (each depends on its resample)."""
    def requires(self):
        return [
            AddRollingMetrics15MinTask(),
            AddRollingMetrics30MinTask(),
            AddRollingMetrics60MinTask(),
            AddRollingMetrics120MinTask(),
        ]

    def output(self):
        return luigi.LocalTarget('output/add_rolling_all_complete.txt')

    def run(self):
        with self.output().open('w') as f:
            f.write('All rolling-metrics tasks completed successfully\n')


if __name__ == '__main__':
    luigi.run()

