"""
Luigi task to implement Weibull-based rarity scoring for gaming stakes.

This task uses the fitted Weibull distribution from skins price data to estimate
the rarity of observed stakes given the number of skins through Monte Carlo simulation.
"""

import luigi
import pandas as pd
import numpy as np
import json
import os
from scipy.stats import weibull_min
from pathlib import Path


class WeibullRarityScoreTask(luigi.Task):
    """
    Luigi task to implement rarity scoring using Weibull distribution.
    
    Uses Monte Carlo simulation to determine how rare an observed stake is
    given the number of skins and the fitted Weibull price distribution.
    """
    
    weibull_params_file = luigi.Parameter(default="output/weibull_distribution_params.json")
    casino_data_file = luigi.Parameter(default="output/id_skins_ticks_stake_dataset.csv")
    output_file = luigi.Parameter(default="output/rarity_scores_analysis.csv")
    n_simulations = luigi.IntParameter(default=100000)
    
    def requires(self):
        """Requires Weibull distribution fitting to be completed."""
        from tasks.fit_weibull_distribution import FitWeibullDistributionTask
        from tasks.create_id_skins_stake_dataset import CreateIDSkinsStakeDatasetTask
        return [FitWeibullDistributionTask(), CreateIDSkinsStakeDatasetTask()]
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Implement the Weibull-based rarity scoring system."""
        # Load Weibull parameters from the fitted skins price distribution
        with open(self.weibull_params_file, 'r') as f:
            weibull_data = json.load(f)
        
        shape = weibull_data['distribution_parameters']['scipy_parameterization']['shape']
        scale = weibull_data['distribution_parameters']['scipy_parameterization']['scale']
        loc = weibull_data['distribution_parameters']['scipy_parameterization']['location']
        
        print(f"Using Weibull parameters from skins price distribution:")
        print(f"  Shape (k): {shape:.4f}")
        print(f"  Scale (λ): {scale:.4f}")
        print(f"  Location: {loc:.4f}")
        
        # Load casino data
        casino_df = pd.read_csv(self.casino_data_file)
        
        print(f"Analyzing {len(casino_df):,} casino rounds...")
        
        # Calculate rarity scores for all rounds
        rarity_scores = []
        p_values = []
        
        for idx, row in casino_df.iterrows():
            if idx % 10000 == 0:
                print(f"Processing round {idx:,}/{len(casino_df):,}")
            
            skins_count = int(row['skins'])
            observed_stake = float(row['stake'])
            ticks = float(row['ticks'])
            
            # Skip rounds with zero or negative values
            if skins_count <= 0 or observed_stake <= 0:
                rarity_scores.append(np.nan)
                p_values.append(np.nan)
                continue
            
            # Calculate rarity score
            p_value, rarity_score = self.weibull_global_p_value(
                skins_count, observed_stake, shape, scale, loc, ticks
            )
            
            rarity_scores.append(rarity_score)
            p_values.append(p_value)
        
        # Add rarity scores to the dataset
        casino_df['rarity_score'] = rarity_scores
        casino_df['p_value'] = p_values
        
        # Calculate rarity categories
        casino_df['rarity_category'] = casino_df['rarity_score'].apply(self.categorize_rarity)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save results
        casino_df.to_csv(self.output_file, index=False)
        
        # Generate summary statistics
        self.generate_summary_report(casino_df, shape, scale, loc)
        
        print(f"Rarity analysis completed and saved to: {self.output_file}")
    
    def weibull_global_p_value(self, K, S_obs, shape, scale, loc=0.0, ticks=1.0, seed=42):
        """
        Calculate the probability that a randomly drawn stake is >= observed stake.
        
        Parameters:
        - K: number of skins in the round
        - S_obs: observed stake for this round
        - shape, scale, loc: Weibull distribution parameters from skins price data
        - ticks: platform multiplier (from casino data)
        - seed: random seed for reproducibility
        """
        rng = np.random.default_rng(seed)
        
        # Draw K skins prices from the Weibull distribution
        # This simulates what the stake "should be" based on real skin price distribution
        draws = weibull_min.rvs(c=shape, scale=scale, loc=loc, 
                               size=(self.n_simulations, K), random_state=rng)
        
        # Sum per round (total value of K skins)
        S_base = draws.sum(axis=1)
        
        # Apply platform multiplier (ticks) to get final stake
        S_sim = S_base * ticks
        
        # Calculate tail probability (how often do we see stakes >= observed?)
        p_value = np.mean(S_sim >= S_obs)
        p_value = max(p_value, 1e-12)  # numerical safety
        
        # Rarity score: higher values = more rare
        rarity_score = -np.log10(p_value)
        
        return p_value, rarity_score
    
    def categorize_rarity(self, rarity_score):
        """Categorize rarity scores into meaningful groups."""
        if pd.isna(rarity_score):
            return 'Invalid'
        elif rarity_score < 1.0:
            return 'Common'        # p > 0.1 (happens >10% of the time)
        elif rarity_score < 2.0:
            return 'Uncommon'      # 0.01 < p <= 0.1 (1-10%)
        elif rarity_score < 3.0:
            return 'Rare'          # 0.001 < p <= 0.01 (0.1-1%)
        elif rarity_score < 4.0:
            return 'Very Rare'     # 0.0001 < p <= 0.001 (0.01-0.1%)
        elif rarity_score < 5.0:
            return 'Extremely Rare' # 0.00001 < p <= 0.0001 (0.001-0.01%)
        else:
            return 'Legendary'     # p <= 0.00001 (<0.001%)
    
    def generate_summary_report(self, df, shape, scale, loc):
        """Generate a summary report of the rarity analysis."""
        valid_df = df.dropna(subset=['rarity_score'])
        
        summary = {
            "weibull_parameters": {
                "shape": float(shape),
                "scale": float(scale),
                "location": float(loc),
                "source": "skins_price_distribution"
            },
            "analysis_summary": {
                "total_rounds": int(len(df)),
                "valid_rounds": int(len(valid_df)),
                "invalid_rounds": int(len(df) - len(valid_df)),
                "simulations_per_round": int(self.n_simulations)
            },
            "rarity_distribution": {
                category: int(count) 
                for category, count in valid_df['rarity_category'].value_counts().items()
            },
            "rarity_statistics": {
                "mean_rarity_score": float(valid_df['rarity_score'].mean()),
                "median_rarity_score": float(valid_df['rarity_score'].median()),
                "max_rarity_score": float(valid_df['rarity_score'].max()),
                "min_rarity_score": float(valid_df['rarity_score'].min()),
                "std_rarity_score": float(valid_df['rarity_score'].std())
            },
            "extreme_cases": {
                "most_rare_rounds": valid_df.nlargest(5, 'rarity_score')[
                    ['ID', 'skins', 'stake', 'ticks', 'rarity_score', 'rarity_category']
                ].to_dict('records'),
                "most_common_rounds": valid_df.nsmallest(5, 'rarity_score')[
                    ['ID', 'skins', 'stake', 'ticks', 'rarity_score', 'rarity_category']
                ].to_dict('records')
            }
        }
        
        # Save summary report
        summary_file = self.output_file.replace('.csv', '_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nRARITY ANALYSIS SUMMARY:")
        print(f"=" * 50)
        print(f"Valid rounds analyzed: {len(valid_df):,}")
        print(f"Mean rarity score: {summary['rarity_statistics']['mean_rarity_score']:.2f}")
        print(f"Max rarity score: {summary['rarity_statistics']['max_rarity_score']:.2f}")
        print(f"\nRarity distribution:")
        for category, count in summary['rarity_distribution'].items():
            percentage = count / len(valid_df) * 100
            print(f"  {category:15s}: {count:6,} ({percentage:5.1f}%)")
        
        print(f"\nSummary report saved to: {summary_file}")


class TestRarityScoreTask(luigi.Task):
    """
    Test task to demonstrate the rarity scoring system with examples.
    """
    
    weibull_params_file = luigi.Parameter(default="output/weibull_distribution_params.json")
    output_file = luigi.Parameter(default="output/rarity_score_examples.json")
    
    def requires(self):
        """Requires Weibull distribution fitting to be completed."""
        from tasks.fit_weibull_distribution import FitWeibullDistributionTask
        return FitWeibullDistributionTask()
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Run test examples of the rarity scoring system."""
        # Load Weibull parameters
        with open(self.weibull_params_file, 'r') as f:
            weibull_data = json.load(f)
        
        shape = weibull_data['distribution_parameters']['scipy_parameterization']['shape']
        scale = weibull_data['distribution_parameters']['scipy_parameterization']['scale']
        loc = weibull_data['distribution_parameters']['scipy_parameterization']['location']
        
        # Test examples
        test_cases = [
            {"skins": 5, "stake": 50, "ticks": 2.0, "description": "Low stake, few skins"},
            {"skins": 10, "stake": 200, "ticks": 1.5, "description": "Medium stake, medium skins"},
            {"skins": 20, "stake": 500, "ticks": 3.0, "description": "High stake, many skins"},
            {"skins": 3, "stake": 1000, "ticks": 1.0, "description": "Very high stake, few skins"},
            {"skins": 100, "stake": 100, "ticks": 1.0, "description": "Low stake per skin, many skins"}
        ]
        
        results = []
        
        print("TESTING RARITY SCORING SYSTEM:")
        print("=" * 60)
        
        for i, case in enumerate(test_cases, 1):
            p_value, rarity_score = self.weibull_global_p_value(
                case["skins"], case["stake"], shape, scale, loc, case["ticks"]
            )
            
            category = self.categorize_rarity(rarity_score)
            
            result = {
                **case,
                "p_value": float(p_value),
                "rarity_score": float(rarity_score),
                "rarity_category": category
            }
            results.append(result)
            
            print(f"Test {i}: {case['description']}")
            print(f"  Skins: {case['skins']}, Stake: ${case['stake']}, Ticks: {case['ticks']}")
            print(f"  P-value: {p_value:.8f}")
            print(f"  Rarity score: {rarity_score:.2f}")
            print(f"  Category: {category}")
            print()
        
        # Save results
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Test results saved to: {self.output_file}")
    
    def weibull_global_p_value(self, K, S_obs, shape, scale, loc=0.0, ticks=1.0, seed=42):
        """Same as main task but with fewer simulations for testing."""
        rng = np.random.default_rng(seed)
        
        draws = weibull_min.rvs(c=shape, scale=scale, loc=loc, 
                               size=(10000, K), random_state=rng)
        S_base = draws.sum(axis=1)
        S_sim = S_base * ticks
        
        p_value = np.mean(S_sim >= S_obs)
        p_value = max(p_value, 1e-12)
        rarity_score = -np.log10(p_value)
        
        return p_value, rarity_score
    
    def categorize_rarity(self, rarity_score):
        """Same categorization as main task."""
        if pd.isna(rarity_score):
            return 'Invalid'
        elif rarity_score < 1.0:
            return 'Common'
        elif rarity_score < 2.0:
            return 'Uncommon'
        elif rarity_score < 3.0:
            return 'Rare'
        elif rarity_score < 4.0:
            return 'Very Rare'
        elif rarity_score < 5.0:
            return 'Extremely Rare'
        else:
            return 'Legendary'


if __name__ == "__main__":
    luigi.run()