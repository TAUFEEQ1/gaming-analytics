"""
Prepare GGR time-series data for forecasting.

This task:
1. Aggregates GGR across all operators (irrespective of operator)
2. Sums multiple reportings on the same day
3. Creates a continuous time-series with date index
"""
import luigi
import pandas as pd
import numpy as np
from pathlib import Path


class PrepareGGRTimeSeries(luigi.Task):
    """
    Prepare GGR time-series data aggregated across all operators.
    Handles multiple reportings per day and creates continuous date range.
    """
    
    def output(self):
        return {
            'ggr_timeseries': luigi.LocalTarget('warehouse/data/ggr_timeseries.csv'),
            'ggr_summary': luigi.LocalTarget('warehouse/data/ggr_timeseries_summary.txt')
        }
    
    def run(self):
        # Load raw dataset
        df = pd.read_csv('lotterries_plain_dataset.csv')
        
        print(f"\n{'='*80}")
        print("PREPARING GGR TIME-SERIES DATA")
        print(f"{'='*80}")
        print(f"Total records: {len(df):,}")
        
        # Filter for gameSummary entries only
        df = df[df['source_type'] == 'gameSummary'].copy()
        print(f"GameSummary records: {len(df):,}")
        
        # Convert timestamp_end to datetime and extract date
        df['timestamp_end'] = pd.to_datetime(df['timestamp_end'])
        df['date'] = df['timestamp_end'].dt.date
        
        # Check GGR column
        print(f"\nGGR column info:")
        print(f"  Total GGR records: {df['GGR'].notna().sum():,}")
        print(f"  Missing GGR records: {df['GGR'].isna().sum():,}")
        print(f"  Total GGR (raw): {df['GGR'].sum():,.2f}")
        
        # Fill missing values with 0
        df['no_of_bets'] = df['no_of_bets'].fillna(0)
        df['stake_real_money'] = df['stake_real_money'].fillna(0)
        df['stake_free_money'] = df['stake_free_money'].fillna(0)
        df['payout_base_win'] = df['payout_base_win'].fillna(0)
        
        # Calculate total stake
        df['total_stake'] = df['stake_real_money'] + df['stake_free_money']
        
        # Aggregate by date (sum across all operators and multiple reportings)
        daily_ggr = df.groupby('date').agg({
            'GGR': 'sum',
            'operator': ['nunique', lambda x: ','.join(sorted(set(x)))],  # Count and list operators
            'report_id': 'count',    # Count number of reports per day
            'no_of_bets': 'sum',     # Total number of bets per day
            'total_stake': 'sum',    # Total stake per day
            'payout_base_win': 'sum',  # Total payout per day
            'game_type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'unknown'  # Modal game_type
        }).reset_index()
        
        daily_ggr.columns = ['date', 'GGR', 'num_operators', 'operators_list', 'num_reports', 'total_bets', 'total_stake', 'total_payout', 'modal_game_type']
        
        # Convert date back to datetime for time-series operations
        daily_ggr['date'] = pd.to_datetime(daily_ggr['date'])
        
        # Sort by date
        daily_ggr = daily_ggr.sort_values('date').reset_index(drop=True)
        
        # Get date range
        min_date = daily_ggr['date'].min()
        max_date = daily_ggr['date'].max()
        date_range = (max_date - min_date).days
        
        # Create complete date range (including missing dates)
        full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
        full_df = pd.DataFrame({'date': full_date_range})
        
        # Merge with actual data (missing dates will have NaN for GGR)
        daily_ggr_complete = full_df.merge(daily_ggr, on='date', how='left')
        
        # Fill missing metadata with 0 or appropriate defaults
        daily_ggr_complete['num_operators'] = daily_ggr_complete['num_operators'].fillna(0).astype(int)
        daily_ggr_complete['operators_list'] = daily_ggr_complete['operators_list'].fillna('')
        daily_ggr_complete['num_reports'] = daily_ggr_complete['num_reports'].fillna(0).astype(int)
        daily_ggr_complete['total_bets'] = daily_ggr_complete['total_bets'].fillna(0).astype(int)
        daily_ggr_complete['total_stake'] = daily_ggr_complete['total_stake'].fillna(0)
        daily_ggr_complete['total_payout'] = daily_ggr_complete['total_payout'].fillna(0)
        daily_ggr_complete['modal_game_type'] = daily_ggr_complete['modal_game_type'].fillna('unknown')
        
        # Mark missing days
        daily_ggr_complete['is_missing'] = daily_ggr_complete['GGR'].isna().astype(int)
        
        # Save time-series data
        daily_ggr_complete.to_csv(self.output()['ggr_timeseries'].path, index=False)
        
        # Generate summary report
        summary = self._generate_summary(daily_ggr_complete, min_date, max_date, date_range)
        with open(self.output()['ggr_summary'].path, 'w') as f:
            f.write(summary)
        
        print(f"\n{'='*80}")
        print("GGR TIME-SERIES PREPARATION COMPLETE")
        print(f"{'='*80}")
        print(f"Date range: {min_date.date()} to {max_date.date()} ({date_range + 1} days)")
        print(f"Days with data: {(~daily_ggr_complete['GGR'].isna()).sum()}")
        print(f"Missing days: {daily_ggr_complete['GGR'].isna().sum()}")
        print(f"Total GGR: {daily_ggr_complete['GGR'].sum():,.2f}")
        print(f"\n✓ Time-series data saved to: {self.output()['ggr_timeseries'].path}")
        print(f"✓ Summary saved to: {self.output()['ggr_summary'].path}")
    
    def _generate_summary(self, df, min_date, max_date, date_range):
        """Generate summary statistics for the GGR time-series"""
        
        # Calculate statistics
        days_with_data = (~df['GGR'].isna()).sum()
        missing_days = df['GGR'].isna().sum()
        total_ggr = df['GGR'].sum()
        
        # Statistics for days with data
        data_days = df[~df['GGR'].isna()]
        
        summary = f"""
{'='*80}
GGR TIME-SERIES SUMMARY
{'='*80}

DATE RANGE:
  Start Date: {min_date.date()}
  End Date: {max_date.date()}
  Total Days: {date_range + 1}
  Days with Data: {days_with_data} ({days_with_data/(date_range+1)*100:.1f}%)
  Missing Days: {missing_days} ({missing_days/(date_range+1)*100:.1f}%)

GGR STATISTICS (Days with Data):
  Total GGR: {total_ggr:,.2f}
  Mean Daily GGR: {data_days['GGR'].mean():,.2f}
  Median Daily GGR: {data_days['GGR'].median():,.2f}
  Std Dev: {data_days['GGR'].std():,.2f}
  Min Daily GGR: {data_days['GGR'].min():,.2f}
  Max Daily GGR: {data_days['GGR'].max():,.2f}

REPORTING STATISTICS:
  Avg Operators per Day: {data_days['num_operators'].mean():.1f}
  Avg Reports per Day: {data_days['num_reports'].mean():.1f}
  Max Operators in One Day: {data_days['num_operators'].max()}
  Max Reports in One Day: {data_days['num_reports'].max()}

DATA QUALITY:
  Days with Zero GGR: {(data_days['GGR'] == 0).sum()}
  Days with Negative GGR: {(data_days['GGR'] < 0).sum()}
  
{'='*80}
"""
        return summary


if __name__ == '__main__':
    luigi.build([PrepareGGRTimeSeries()], local_scheduler=True, log_level='INFO')
