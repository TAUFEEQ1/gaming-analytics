"""
Luigi task to create a dataset with ID, skins, and stake from onlineCasino.csv.

This task reads the casino data and creates a simplified dataset with just the three
requested columns: ID, skins, and stake (using the money column as stake).
"""

import luigi
import pandas as pd
import numpy as np
import os
from pathlib import Path


class CreateIDSkinsStakeDatasetTask(luigi.Task):
    """
    Luigi task to create a dataset with ID, skins, ticks, and stake columns.
    
    Reads from onlineCasino.csv and extracts:
    - ID: A unique identifier assigned to each individual game event
    - skins: The quantity of virtual items (skins) wagered by all participants (from 'skins' column which represents 'items')
    - ticks: The site's multiplication coefficient for the specific game round (outcome of the 'roulette')
    - stake: The equivalent value of the items bet, expressed in real money dollars (from 'money' column)
    """
    
    input_file = luigi.Parameter(default="data/onlineCasino.csv")
    output_file = luigi.Parameter(default="output/id_skins_ticks_stake_dataset.csv")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Create the ID, skins, ticks, stake dataset."""
        # Read the casino data
        df = pd.read_csv(self.input_file)
        
        print(f"Processing {len(df)} records from {self.input_file}")
        
        # Create the simplified dataset
        simplified_df = pd.DataFrame({
            'ID': df['ID'],
            'skins': df['skins'],  # Quantity of virtual items (skins) wagered by all participants
            'ticks': df['ticks'],  # Site's multiplication coefficient for the game round
            'stake': df['money']   # Equivalent value of items bet in dollars
        })
        
        # Remove any rows with missing values
        initial_count = len(simplified_df)
        simplified_df = simplified_df.dropna()
        final_count = len(simplified_df)
        
        if initial_count != final_count:
            print(f"Removed {initial_count - final_count} rows with missing values")
        
        # Sort by ID for consistency
        simplified_df = simplified_df.sort_values('ID')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save to CSV
        simplified_df.to_csv(self.output_file, index=False)
        
        # Print summary statistics
        print(f"\nDataset Summary:")
        print(f"  Total records: {len(simplified_df)}")
        print(f"  ID range: {simplified_df['ID'].min()} - {simplified_df['ID'].max()}")
        print(f"  Skins statistics:")
        print(f"    Mean: {simplified_df['skins'].mean():.2f}")
        print(f"    Median: {simplified_df['skins'].median():.2f}")
        print(f"    Min: {simplified_df['skins'].min()}")
        print(f"    Max: {simplified_df['skins'].max()}")
        print(f"  Ticks statistics:")
        print(f"    Mean: {simplified_df['ticks'].mean():.2f}")
        print(f"    Median: {simplified_df['ticks'].median():.2f}")
        print(f"    Min: {simplified_df['ticks'].min():.2f}")
        print(f"    Max: {simplified_df['ticks'].max():.2f}")
        print(f"  Stake statistics:")
        print(f"    Mean: ${simplified_df['stake'].mean():.2f}")
        print(f"    Median: ${simplified_df['stake'].median():.2f}")
        print(f"    Min: ${simplified_df['stake'].min():.2f}")
        print(f"    Max: ${simplified_df['stake'].max():.2f}")
        
        print(f"\nDataset saved to: {self.output_file}")


class CreateIDSkinsStakeWithMetadataTask(luigi.Task):
    """
    Enhanced version that includes additional metadata while maintaining the core ID, skins, stake structure.
    """
    
    input_file = luigi.Parameter(default="data/onlineCasino.csv")
    output_file = luigi.Parameter(default="output/id_skins_stake_with_metadata.csv")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Create enhanced dataset with metadata."""
        # Read the casino data
        df = pd.read_csv(self.input_file)
        
        print(f"Processing {len(df)} records with metadata from {self.input_file}")
        
        # Create enhanced dataset
        enhanced_df = pd.DataFrame({
            'ID': df['ID'],
            'skins': df['skins'],
            'stake': df['money'],
            # Additional metadata
            'gamers': df['gamers'],
            'ticks': df['ticks'],
            'peopleWin': df['peopleWin'],
            'peopleLost': df['peopleLost'],
            'outpay': df['outpay'],
            'time': df['time'],
            'moderator': df['moderator'],
            # Derived metrics
            'stake_per_skin': df['money'] / df['skins'].replace(0, np.nan),  # Avoid division by zero
            'stake_per_gamer': df['money'] / df['gamers'].replace(0, np.nan),
            'win_rate': df['peopleWin'] / (df['peopleWin'] + df['peopleLost']).replace(0, np.nan),
            'profit_margin': (df['outpay'] - df['money']) / df['money'].replace(0, np.nan),
            'skins_per_gamer': df['skins'] / df['gamers'].replace(0, np.nan)
        })
        
        # Convert time to datetime
        enhanced_df['time'] = pd.to_datetime(enhanced_df['time'])
        
        # Add time-based features
        enhanced_df['hour'] = enhanced_df['time'].dt.hour
        enhanced_df['day_of_week'] = enhanced_df['time'].dt.dayofweek
        enhanced_df['date'] = enhanced_df['time'].dt.date
        
        # Remove rows with missing core values (ID, skins, stake)
        core_columns = ['ID', 'skins', 'stake']
        initial_count = len(enhanced_df)
        enhanced_df = enhanced_df.dropna(subset=core_columns)
        final_count = len(enhanced_df)
        
        if initial_count != final_count:
            print(f"Removed {initial_count - final_count} rows with missing core values")
        
        # Sort by ID and time
        enhanced_df = enhanced_df.sort_values(['ID', 'time'])
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save to CSV
        enhanced_df.to_csv(self.output_file, index=False)
        
        # Print summary
        print(f"\nEnhanced Dataset Summary:")
        print(f"  Total records: {len(enhanced_df)}")
        print(f"  Date range: {enhanced_df['date'].min()} to {enhanced_df['date'].max()}")
        print(f"  Average stake per skin: ${enhanced_df['stake_per_skin'].mean():.2f}")
        print(f"  Average win rate: {enhanced_df['win_rate'].mean():.2%}")
        print(f"  Average profit margin: {enhanced_df['profit_margin'].mean():.2%}")
        
        print(f"Enhanced dataset saved to: {self.output_file}")


if __name__ == "__main__":
    luigi.run()