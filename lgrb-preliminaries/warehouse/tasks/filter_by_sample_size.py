"""
Filter operators based on sample size using Z-score analysis
Removes operators with insufficient entries for ML modeling
"""
import luigi
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats


class RemoveZeros(luigi.Task):
    """Remove records with zero values in key numeric columns"""
    
    def requires(self):
        from warehouse.tasks.filter_and_extract import ExtractColumns
        return ExtractColumns()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/no_zeros_data.csv')
    
    def run(self):
        # Load extracted data
        df = pd.read_csv(self.input().path)
        
        initial_count = len(df)
        
        # Remove rows where no_of_bets or stake_real_money are zero
        df_filtered = df[
            (df['no_of_bets'] > 0) & 
            (df['stake_real_money'] > 0)
        ].copy()
        
        removed_count = initial_count - len(df_filtered)
        
        # Save filtered data
        df_filtered.to_csv(self.output().path, index=False)
        
        print(f"\n=== Zero Value Removal ===")
        print(f"Initial records: {initial_count}")
        print(f"Records with zeros removed: {removed_count}")
        print(f"Remaining records: {len(df_filtered)} ({len(df_filtered)/initial_count*100:.1f}%)")


class FilterLowStakes(luigi.Task):
    """
    Winsorize (cap) low stake-per-bet ratios instead of removing them.
    Caps values below the specified percentile to improve model robustness
    without losing data.
    """
    
    lower_percentile = luigi.FloatParameter(default=5.0)  # Cap values below this percentile
    
    def requires(self):
        return RemoveZeros()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/winsorized_stakes_data.csv')
    
    def run(self):
        # Load data without zeros
        df = pd.read_csv(self.input().path)
        
        initial_count = len(df)
        
        # Calculate stake per bet ratio
        df['stake_per_bet'] = df['stake_real_money'] / df['no_of_bets']
        
        # Calculate statistics before winsorization
        Q1 = df['stake_per_bet'].quantile(0.25)
        Q2 = df['stake_per_bet'].quantile(0.50)
        Q3 = df['stake_per_bet'].quantile(0.75)
        IQR = Q3 - Q1
        original_min = df['stake_per_bet'].min()
        original_max = df['stake_per_bet'].max()
        
        # Calculate the lower percentile threshold
        lower_threshold = df['stake_per_bet'].quantile(self.lower_percentile / 100)
        
        # Count how many will be capped
        n_capped = (df['stake_per_bet'] < lower_threshold).sum()
        
        # Winsorize: cap low values at the threshold
        df.loc[df['stake_per_bet'] < lower_threshold, 'stake_per_bet'] = lower_threshold
        
        # Recalculate stake_real_money based on capped stake_per_bet
        df.loc[df['stake_per_bet'] == lower_threshold, 'stake_real_money'] = (
            df.loc[df['stake_per_bet'] == lower_threshold, 'no_of_bets'] * lower_threshold
        )
        
        # Drop the temporary column before saving
        df_output = df.drop(columns=['stake_per_bet'])
        
        # Save winsorized data
        df_output.to_csv(self.output().path, index=False)
        
        # Print statistics
        print(f"\n=== Winsorization: Capping Low Stake-Per-Bet Values ({self.lower_percentile}th percentile) ===")
        print(f"Total records: {initial_count}")
        print(f"Lower threshold ({self.lower_percentile}th percentile): {lower_threshold:,.2f} UGX/bet")
        print(f"Records capped (not removed): {n_capped} ({n_capped/initial_count*100:.1f}%)")
        print(f"All {initial_count} records retained (100%)")
        
        print(f"\nOriginal stake-per-bet statistics:")
        print(f"  - Min: {original_min:,.2f} UGX/bet")
        print(f"  - Q1 (25th percentile): {Q1:,.2f} UGX/bet")
        print(f"  - Q2 (50th percentile/Median): {Q2:,.2f} UGX/bet")
        print(f"  - Q3 (75th percentile): {Q3:,.2f} UGX/bet")
        print(f"  - Max: {original_max:,.2f} UGX/bet")
        print(f"  - IQR: {IQR:,.2f} UGX/bet")
        
        print(f"\nAfter winsorization:")
        print(f"  - New min: {lower_threshold:,.2f} UGX/bet (capped at threshold)")
        print(f"  - Mean: {df['stake_per_bet'].mean():,.2f} UGX/bet")
        print(f"  - Max: {df['stake_per_bet'].max():,.2f} UGX/bet (unchanged)")


class FilterBySampleSize(luigi.Task):
    """
    Filter out operators with insufficient data based on minimum count threshold.
    Keeps only well-represented operators for ML modeling.
    """
    
    min_count = luigi.IntParameter(default=100)
    
    def requires(self):
        return FilterLowStakes()
    
    def output(self):
        return {
            'filtered_data': luigi.LocalTarget('warehouse/data/ml_ready_data.csv'),
            'sample_analysis': luigi.LocalTarget('warehouse/data/sample_size_analysis.csv')
        }
    
    def run(self):
        # Load extracted data
        df = pd.read_csv(self.input().path)
        
        # Count entries per operator
        operator_counts = df['operator'].value_counts()
        
        # Create analysis dataframe
        analysis_df = pd.DataFrame({
            'operator': operator_counts.index,
            'entry_count': operator_counts.values
        }).sort_values('entry_count', ascending=False)
        
        # Identify operators with sufficient sample size (>= min_count)
        sufficient_operators = analysis_df[
            analysis_df['entry_count'] >= self.min_count
        ]['operator'].tolist()
        
        # Filter original data to keep only sufficient operators
        filtered_df = df[df['operator'].isin(sufficient_operators)].copy()
        
        # Save filtered data
        filtered_df.to_csv(self.output()['filtered_data'].path, index=False)
        
        # Save analysis results
        analysis_df['kept'] = analysis_df['entry_count'] >= self.min_count
        analysis_df.to_csv(self.output()['sample_analysis'].path, index=False)
        
        # Print summary
        removed_operators = len(operator_counts) - len(sufficient_operators)
        removed_records = len(df) - len(filtered_df)
        
        print(f"\n=== Sample Size Filtering (Min count: {self.min_count}) ===")
        print(f"Total operators: {len(operator_counts)}")
        print(f"Operators kept (>= {self.min_count} records): {len(sufficient_operators)}")
        print(f"Operators removed: {removed_operators}")
        print(f"Records retained: {len(filtered_df):,} / {len(df):,} ({len(filtered_df)/len(df)*100:.1f}%)")
        print(f"Records removed: {removed_records:,}")
        
        print(f"\n✓ Operators kept:")
        kept_ops = analysis_df[analysis_df['kept']]
        for _, row in kept_ops.iterrows():
            print(f"  {row['operator']}: {int(row['entry_count']):,} records")
        
        print(f"\n✗ Operators removed (< {self.min_count} records):")
        removed_ops = analysis_df[~analysis_df['kept']]
        for _, row in removed_ops.iterrows():
            print(f"  {row['operator']}: {int(row['entry_count']):,} records")
