import luigi
import pandas as pd


class BaseResampleWindowsTask(luigi.Task):
    """Base Luigi Task for resampling `data/player_averages.csv`.

    Subclasses must set the `window` (pandas offset alias, e.g. '15T') and
    `output_path` (relative path under `output/`).
    """
    window = None
    output_path = None

    def input(self):
        return luigi.LocalTarget('data/player_averages.csv')

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


class Resample15MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 15-minute windows."""
    window = '15T'
    output_path = 'output/windows/resampled_15min_windows.csv'


class Resample30MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 30-minute windows."""
    window = '30T'
    output_path = 'output/windows/resampled_30min_windows.csv'


class Resample60MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 60-minute windows."""
    window = '60T'
    output_path = 'output/windows/resampled_60min_windows.csv'


class Resample120MinWindowsTask(BaseResampleWindowsTask):
    """Resample into 120-minute windows."""
    window = '120T'
    output_path = 'output/windows/resampled_120min_windows.csv'


class ResampleAllWindowsTask(luigi.Task):
    """Run all resampling tasks."""
    def requires(self):
        return [
            Resample15MinWindowsTask(),
            Resample30MinWindowsTask(),
            Resample60MinWindowsTask(),
            Resample120MinWindowsTask(),
        ]

    def output(self):
        return luigi.LocalTarget('output/resample_all_complete.txt')

    def run(self):
        with self.output().open('w') as f:
            f.write('All resampling tasks completed successfully\n')


if __name__ == '__main__':
    luigi.run()
