import luigi
import pandas as pd


class BaseResampleWindowsTask(luigi.Task):
    """Base Luigi Task for resampling `data/interesting_data.csv`.

    Subclasses must set the `window` (pandas offset alias, e.g. '15T') and
    `output_path` (relative path under `output/`).
    """
    window = None
    output_path = None

    def input(self):
        return luigi.LocalTarget('data/interesting_data.csv')

    def output(self):
        if not self.output_path:
            raise NotImplementedError('Subclasses must set `output_path`')
        return luigi.LocalTarget(self.output_path)

    def run(self):
        if not self.window:
            raise NotImplementedError('Subclasses must set `window`')

        # Read, prepare, resample and write output. Centralised to avoid repetition.
        df = pd.read_csv(self.input().path, parse_dates=['time'])
        df.set_index('time', inplace=True)
        df = df.drop(columns=['ID'], errors='ignore')

        resampled_df = df.resample(self.window).sum(numeric_only=True).reset_index()
        resampled_df.to_csv(self.output().path, index=False)


class Resample1MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 1-minute windows."""
    window = '1T'
    output_path = 'output/windows/resampled_1min_windows.csv'

class Resample3MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 3-minute windows."""
    window = '3T'
    output_path = 'output/windows/resampled_3min_windows.csv'


class Resample5MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 5-minute windows."""
    window = '5T'
    output_path = 'output/windows/resampled_5min_windows.csv'



class ResampleAllWindowsTask(luigi.Task):
    """Run all resampling tasks."""
    def requires(self):
        return [
            Resample1MinWindowsTask(),
            Resample3MinWindowsTask(),
            Resample5MinWindowsTask(),
        ]

    def output(self):
        return luigi.LocalTarget('output/resample_all_complete.txt')

    def run(self):
        with self.output().open('w') as f:
            f.write('All resampling tasks completed successfully\n')


if __name__ == '__main__':
    luigi.run()
