"""
Chunked Luigi tasks for Weibull rarity scoring with parallelism.

This breaks the casino rounds into smaller chunks that can be processed in parallel,
then combines the results for faster execution.
"""

import luigi
import pandas as pd
import numpy as np
import json
import os
from scipy.stats import weibull_min
from pathlib import Path


class WeibullRarityChunkTask(luigi.Task):
    """
    Process a chunk of casino rounds for rarity scoring.
    """
    
    chunk_id = luigi.IntParameter()
    chunk_size = luigi.IntParameter(default=1000)
    weibull_params_file = luigi.Parameter(default="output/weibull_distribution_params.json")
    casino_data_file = luigi.Parameter(default="output/id_skins_ticks_stake_dataset.csv")
    n_simulations = luigi.IntParameter(default=50000)  # Reduced for faster chunks
    output_dir = luigi.Parameter(default="output/rarity_chunks")
    
    def requires(self):
        """Require Weibull parameters and casino dataset."""
        from tasks.fit_weibull_distribution import FitWeibullDistributionTask
        from tasks.create_id_skins_stake_dataset import CreateIDSkinsStakeDatasetTask
        return [
            FitWeibullDistributionTask(),
            CreateIDSkinsStakeDatasetTask()
        ]
    
    def output(self):
        """Define chunk output file."""
        return luigi.LocalTarget(f"{self.output_dir}/chunk_{self.chunk_id:04d}.csv")
    
    def run(self):
        """Process a specific chunk of casino rounds."""
        # Load Weibull parameters
        with open(self.weibull_params_file, 'r') as f:
            weibull_data = json.load(f)
        
        shape = weibull_data['distribution_parameters']['scipy_parameterization']['shape']
        scale = weibull_data['distribution_parameters']['scipy_parameterization']['scale']
        loc = weibull_data['distribution_parameters']['scipy_parameterization']['location']
        
        # Load casino data
        df = pd.read_csv(self.casino_data_file)
        
        # Calculate chunk bounds
        start_idx = self.chunk_id * self.chunk_size
        end_idx = min(start_idx + self.chunk_size, len(df))
        
        if start_idx >= len(df):
            # Empty chunk - create empty output
            empty_df = pd.DataFrame(columns=['ID', 'skins', 'ticks', 'stake', 'p_value', 'rarity_score'])
            os.makedirs(self.output_dir, exist_ok=True)
            empty_df.to_csv(self.output().path, index=False)
            print(f"Chunk {self.chunk_id}: Empty chunk (start_idx={start_idx} >= len={len(df)})")
            return
        
        chunk_df = df.iloc[start_idx:end_idx].copy()
        
        print(f"Processing chunk {self.chunk_id}: rows {start_idx}-{end_idx-1} ({len(chunk_df)} rounds)")
        
        # Initialize results lists
        p_values = []
        rarity_scores = []
        
        # Set up random number generator with different seed per chunk
        rng = np.random.default_rng(42 + self.chunk_id)
        
        # Process each round in the chunk
        for idx, row in chunk_df.iterrows():
            skins_count = int(row['skins'])
            observed_stake = float(row['stake'])
            
            if skins_count <= 0 or observed_stake <= 0:
                p_values.append(1.0)
                rarity_scores.append(0.0)
                continue
            
            # Generate simulated stakes for this skin count
            draws = weibull_min.rvs(c=shape, scale=scale, loc=loc, 
                                  size=(self.n_simulations, skins_count), 
                                  random_state=rng)
            
            # Sum per simulation round
            simulated_stakes = draws.sum(axis=1)
            
            # Calculate tail probability
            p_value = np.mean(simulated_stakes >= observed_stake)
            p_value = max(p_value, 1e-12)  # Numerical safety
            rarity_score = -np.log10(p_value)
            
            p_values.append(p_value)
            rarity_scores.append(rarity_score)
        
        # Add results to chunk dataframe
        chunk_df['p_value'] = p_values
        chunk_df['rarity_score'] = rarity_scores
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save chunk results
        chunk_df.to_csv(self.output().path, index=False)
        
        print(f"Chunk {self.chunk_id} completed: {len(chunk_df)} rounds processed")


class CombineRarityChunksTask(luigi.Task):
    """
    Combine all rarity score chunks into a single result file.
    """
    
    chunk_size = luigi.IntParameter(default=1000)
    casino_data_file = luigi.Parameter(default="output/id_skins_ticks_stake_dataset.csv")
    n_simulations = luigi.IntParameter(default=50000)
    output_file = luigi.Parameter(default="output/rarity_scores_analysis.csv")
    output_dir = luigi.Parameter(default="output/rarity_chunks")
    
    def requires(self):
        """Require all chunks to be completed."""
        # First, determine how many chunks we need
        df = pd.read_csv(self.casino_data_file)
        n_chunks = (len(df) + self.chunk_size - 1) // self.chunk_size  # Ceiling division
        
        # Create tasks for all chunks
        return [
            WeibullRarityChunkTask(
                chunk_id=i,
                chunk_size=self.chunk_size,
                n_simulations=self.n_simulations,
                output_dir=self.output_dir
            ) 
            for i in range(n_chunks)
        ]
    
    def output(self):
        """Define combined output file."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Combine all chunk results."""
        print("Combining rarity score chunks...")
        
        chunk_files = []
        for task in self.requires():
            chunk_path = task.output().path
            if os.path.exists(chunk_path):
                chunk_files.append(chunk_path)
        
        if not chunk_files:
            raise ValueError("No chunk files found!")
        
        print(f"Found {len(chunk_files)} chunk files to combine")
        
        # Read and combine all chunks
        chunk_dfs = []
        for chunk_file in sorted(chunk_files):
            chunk_df = pd.read_csv(chunk_file)
            if len(chunk_df) > 0:  # Skip empty chunks
                chunk_dfs.append(chunk_df)
                print(f"Added chunk {chunk_file}: {len(chunk_df)} rows")
        
        # Combine all chunks
        combined_df = pd.concat(chunk_dfs, ignore_index=True)
        
        # Sort by ID to maintain original order
        combined_df = combined_df.sort_values('ID')
        
        # Calculate summary statistics
        print(f"\nRarity Score Analysis Summary:")
        print(f"Total rounds analyzed: {len(combined_df):,}")
        print(f"Rarity score statistics:")
        print(f"  Mean: {combined_df['rarity_score'].mean():.3f}")
        print(f"  Median: {combined_df['rarity_score'].median():.3f}")
        print(f"  Max: {combined_df['rarity_score'].max():.3f}")
        print(f"  Min: {combined_df['rarity_score'].min():.3f}")
        
        # Identify highly rare events
        high_rarity = combined_df[combined_df['rarity_score'] >= 6.0]  # p < 1e-6
        print(f"Highly rare events (score ≥ 6.0): {len(high_rarity):,}")
        
        if len(high_rarity) > 0:
            print(f"Top 5 rarest events:")
            top_rare = high_rarity.nlargest(5, 'rarity_score')
            for _, row in top_rare.iterrows():
                print(f"  ID {row['ID']}: {row['skins']} skins, ${row['stake']:.2f} stake, score {row['rarity_score']:.2f}")
        
        # Save combined results
        combined_df.to_csv(self.output_file, index=False)
        print(f"\nCombined results saved to: {self.output_file}")


class RarityScoreAnalysisTask(luigi.Task):
    """
    Generate additional analysis and insights from the rarity scores.
    """
    
    rarity_scores_file = luigi.Parameter(default="output/rarity_scores_analysis.csv")
    output_file = luigi.Parameter(default="output/rarity_analysis_summary.json")
    
    def requires(self):
        """Require the combined rarity scores."""
        return CombineRarityChunksTask()
    
    def output(self):
        """Define analysis output file."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Generate comprehensive analysis of rarity scores."""
        df = pd.read_csv(self.rarity_scores_file)
        
        print("Generating rarity score analysis...")
        
        # Basic statistics
        analysis = {
            "dataset_info": {
                "total_rounds": int(len(df)),
                "date_range": "2021-08-25",  # From the data we saw
                "analysis_date": pd.Timestamp.now().isoformat()
            },
            "rarity_score_statistics": {
                "mean": float(df['rarity_score'].mean()),
                "median": float(df['rarity_score'].median()),
                "std": float(df['rarity_score'].std()),
                "min": float(df['rarity_score'].min()),
                "max": float(df['rarity_score'].max()),
                "q25": float(df['rarity_score'].quantile(0.25)),
                "q75": float(df['rarity_score'].quantile(0.75)),
                "q95": float(df['rarity_score'].quantile(0.95)),
                "q99": float(df['rarity_score'].quantile(0.99))
            },
            "p_value_statistics": {
                "mean": float(df['p_value'].mean()),
                "median": float(df['p_value'].median()),
                "min": float(df['p_value'].min()),
                "max": float(df['p_value'].max())
            }
        }
        
        # Rarity categories
        rarity_categories = {
            "very_common": len(df[df['rarity_score'] < 1.0]),      # p > 0.1
            "common": len(df[(df['rarity_score'] >= 1.0) & (df['rarity_score'] < 2.0)]),  # 0.01 < p <= 0.1
            "uncommon": len(df[(df['rarity_score'] >= 2.0) & (df['rarity_score'] < 3.0)]),  # 0.001 < p <= 0.01
            "rare": len(df[(df['rarity_score'] >= 3.0) & (df['rarity_score'] < 4.0)]),     # 0.0001 < p <= 0.001
            "very_rare": len(df[(df['rarity_score'] >= 4.0) & (df['rarity_score'] < 6.0)]), # 1e-6 < p <= 1e-4
            "extremely_rare": len(df[df['rarity_score'] >= 6.0])   # p <= 1e-6
        }
        
        analysis["rarity_categories"] = rarity_categories
        analysis["rarity_percentages"] = {
            k: float(v / len(df) * 100) for k, v in rarity_categories.items()
        }
        
        # Correlation analysis
        analysis["correlations"] = {
            "rarity_vs_skins": float(df['rarity_score'].corr(df['skins'])),
            "rarity_vs_stake": float(df['rarity_score'].corr(df['stake'])),
            "rarity_vs_ticks": float(df['rarity_score'].corr(df['ticks']))
        }
        
        # Top rare events
        top_rare = df.nlargest(10, 'rarity_score')
        analysis["top_10_rarest_events"] = []
        for _, row in top_rare.iterrows():
            analysis["top_10_rarest_events"].append({
                "id": int(row['ID']),
                "skins": int(row['skins']),
                "stake": float(row['stake']),
                "ticks": float(row['ticks']),
                "rarity_score": float(row['rarity_score']),
                "p_value": float(row['p_value'])
            })
        
        # Stake vs skins analysis
        stake_per_skin = df['stake'] / df['skins'].replace(0, np.nan)
        analysis["stake_per_skin_analysis"] = {
            "mean": float(stake_per_skin.mean()),
            "median": float(stake_per_skin.median()),
            "std": float(stake_per_skin.std()),
            "correlation_with_rarity": float(df['rarity_score'].corr(stake_per_skin))
        }
        
        # Save analysis
        with open(self.output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Rarity analysis saved to: {self.output_file}")


class FastRarityScoreTask(luigi.Task):
    """
    Main task to run the complete chunked rarity scoring pipeline.
    """
    
    chunk_size = luigi.IntParameter(default=500)  # Smaller chunks for better parallelism
    n_simulations = luigi.IntParameter(default=25000)  # Balanced accuracy/speed
    
    def requires(self):
        """Require the complete analysis."""
        return RarityScoreAnalysisTask()
    
    def output(self):
        """Main task completion marker."""
        return luigi.LocalTarget("output/rarity_scoring_complete.txt")
    
    def run(self):
        """Mark completion of the full pipeline."""
        with open(self.output().path, 'w') as f:
            f.write(f"Rarity scoring pipeline completed at {pd.Timestamp.now().isoformat()}\n")
            f.write(f"Chunk size: {self.chunk_size}\n")
            f.write(f"Simulations per chunk: {self.n_simulations}\n")
        
        print("✓ Rarity scoring pipeline completed successfully!")


if __name__ == "__main__":
    luigi.run()