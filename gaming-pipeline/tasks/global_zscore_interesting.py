import luigi
import pandas as pd
import numpy as np
from pathlib import Path


class GlobalZscoreInterestingTask(luigi.Task):
    """Compute global mean/std for `stake` and `payout` and per-row global z-scores.

    Reads `data/interesting_data.csv` and writes `output/rolling/interesting_with_global_z.csv`.
    Adds columns: `stake_global_mean`, `stake_global_std`, `stake_global_z`,
    and similarly for `payout` when present.
    """

    def input(self):
        return luigi.LocalTarget('data/interesting_data.csv')

    def output(self):
        out = Path('output/rolling')
        out.mkdir(parents=True, exist_ok=True)
        return luigi.LocalTarget(str(out / 'interesting_with_global_z.csv'))

    def run(self):
        df = pd.read_csv(self.input().path, parse_dates=['time'])

        # compute global stats for all numeric columns except index/time-like fields
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        # exclude ID if present
        numeric_cols = [c for c in numeric_cols if c.lower() not in ('id', )]

        for col in numeric_cols:
            gmean = df[col].mean()
            gstd = df[col].std(ddof=0)  # population std as 'global std'

            # attach global stats as constant columns
            df[f'{col}_global_mean'] = gmean
            df[f'{col}_global_std'] = gstd

            # compute z-score; guard against zero std
            if pd.isna(gstd) or gstd == 0:
                z = pd.Series(0, index=df.index)
            else:
                z = (df[col] - gmean) / gstd

            # replace infinities/nans with 0
            z = z.replace([np.inf, -np.inf], 0).fillna(0)
            df[f'{col}_global_z'] = z

        # write out with time as a column
        df.to_csv(self.output().path, index=False)


if __name__ == '__main__':
    luigi.run()
