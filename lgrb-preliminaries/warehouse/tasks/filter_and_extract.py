"""
Initial data filtering and column extraction tasks
"""
import luigi
import pandas as pd
from pathlib import Path
import hashlib
import json


class FilterGameSummary(luigi.Task):
    """Filter dataset to only include gameSummary entries"""
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/filtered_game_summary.csv')
    
    def run(self):
        # Load the raw dataset
        df = pd.read_csv('lotterries_plain_dataset.csv')
        
        # Filter for source_type = gameSummary
        filtered_df = df[df['source_type'] == 'gameSummary'].copy()
        
        # Save filtered data
        filtered_df.to_csv(self.output().path, index=False)
        print(f"Filtered {len(filtered_df)} gameSummary records from {len(df)} total records")


class AnonymizeOperators(luigi.Task):
    """Anonymize operator names and create/update lookup table"""
    
    def requires(self):
        return FilterGameSummary()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/anonymized_game_summary.csv')
    
    def run(self):
        # Load filtered data
        df = pd.read_csv(self.input().path)
        
        # Path for mapping file (gitignored)
        mapping_file = Path('warehouse/data/mappings/operator_mapping.json')
        mapping_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing mapping or create new
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                operator_mapping = json.load(f)
        else:
            operator_mapping = {}
        
        # Get unique operators
        unique_operators = df['operator'].unique()
        
        # Create pseudonymous IDs for new operators
        for operator in unique_operators:
            if operator not in operator_mapping:
                # Generate pseudonymous ID: OP_{counter}
                counter = len(operator_mapping) + 1
                operator_mapping[operator] = f"OP_{counter:04d}"
        
        # Save updated mapping (in gitignored directory)
        with open(mapping_file, 'w') as f:
            json.dump(operator_mapping, f, indent=2)
        
        # Replace operator names with pseudonymous IDs
        df['operator'] = df['operator'].map(operator_mapping)
        
        # Save anonymized data
        df.to_csv(self.output().path, index=False)
        print(f"Anonymized {len(unique_operators)} operators. Mapping saved to {mapping_file}")


class ExtractColumns(luigi.Task):
    """Extract specific columns and engineer is_weekend feature"""
    
    def requires(self):
        return AnonymizeOperators()
    
    def output(self):
        return luigi.LocalTarget('warehouse/data/extracted_columns.csv')
    
    def run(self):
        # Load anonymized data from previous task
        df = pd.read_csv(self.input().path)
        
        # Extract required columns including stake_free_money, movement_wager_amt, and movement_win_amt
        columns_to_extract = ['operator', 'no_of_bets', 'game_type', 'stake_real_money', 'stake_free_money', 'movement_wager_amt', 'movement_win_amt', 'timestamp_end']
        extracted_df = df[columns_to_extract].copy()
        
        # Convert timestamp to datetime and extract is_weekend feature
        extracted_df['timestamp_end'] = pd.to_datetime(extracted_df['timestamp_end'])
        extracted_df['is_weekend'] = extracted_df['timestamp_end'].dt.dayofweek.isin([5, 6]).astype(int)
        
        # Drop the timestamp column (no longer needed)
        extracted_df = extracted_df.drop(columns=['timestamp_end'])
        
        # Save extracted columns with engineered features
        extracted_df.to_csv(self.output().path, index=False)
        
        weekend_pct = extracted_df['is_weekend'].mean() * 100
        promo_pct = (extracted_df['stake_free_money'] > 0).mean() * 100
        print(f"Extracted {len(extracted_df)} rows with engineered features")
        print(f"  - is_weekend: {weekend_pct:.1f}% weekend records")
        print(f"  - Promotional activity (stake_free_money > 0): {promo_pct:.1f}% of records")
