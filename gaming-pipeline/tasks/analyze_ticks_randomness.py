"""
Luigi task to analyze the randomness and distribution of ticks (multiplication coefficient).

This task examines whether the ticks values appear to be random or follow some pattern.
"""

import luigi
import pandas as pd
import numpy as np
import json
import os
from scipy import stats
from pathlib import Path


class AnalyzeTicksRandomnessTask(luigi.Task):
    """
    Luigi task to analyze the distribution and randomness of ticks values.
    
    Examines patterns, distribution, and statistical properties to determine
    if the multiplication coefficient appears to be random.
    """
    
    input_file = luigi.Parameter(default="data/onlineCasino.csv")
    output_file = luigi.Parameter(default="output/ticks_randomness_analysis.json")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Analyze ticks for randomness and patterns."""
        # Read the casino data
        df = pd.read_csv(self.input_file)
        ticks = df['ticks'].values
        
        print(f"Analyzing {len(ticks)} tick values for randomness patterns")
        
        # Basic statistics
        basic_stats = {
            "count": int(len(ticks)),
            "mean": float(np.mean(ticks)),
            "median": float(np.median(ticks)),
            "std": float(np.std(ticks)),
            "min": float(np.min(ticks)),
            "max": float(np.max(ticks)),
            "range": float(np.max(ticks) - np.min(ticks)),
            "skewness": float(stats.skew(ticks)),
            "kurtosis": float(stats.kurtosis(ticks))
        }
        
        # Percentile analysis
        percentiles = {
            f"{p}th": float(np.percentile(ticks, p))
            for p in [1, 5, 10, 25, 50, 75, 90, 95, 99, 99.9]
        }
        
        # Value frequency analysis
        unique_values = len(np.unique(ticks))
        most_common = stats.mode(ticks, keepdims=False)
        
        # Analyze common multiplier patterns
        common_multipliers = {}
        rounded_ticks = np.round(ticks, 2)
        unique_rounded, counts = np.unique(rounded_ticks, return_counts=True)
        
        # Get top 20 most common values
        top_indices = np.argsort(counts)[-20:][::-1]
        for i in top_indices:
            common_multipliers[float(unique_rounded[i])] = int(counts[i])
        
        # Test for patterns
        pattern_tests = {}
        
        # 1. Check for whole number preference
        whole_numbers = ticks[ticks == np.round(ticks)]
        pattern_tests["whole_number_frequency"] = {
            "count": int(len(whole_numbers)),
            "percentage": float(len(whole_numbers) / len(ticks) * 100)
        }
        
        # 2. Check for low value clustering
        low_values = ticks[ticks <= 2.0]
        pattern_tests["low_values_under_2"] = {
            "count": int(len(low_values)),
            "percentage": float(len(low_values) / len(ticks) * 100)
        }
        
        # 3. Check for exponential-like distribution
        try:
            exp_params = stats.expon.fit(ticks)
            ks_stat_exp, p_value_exp = stats.kstest(ticks, lambda x: stats.expon.cdf(x, *exp_params))
            pattern_tests["exponential_fit"] = {
                "parameters": [float(p) for p in exp_params],
                "ks_statistic": float(ks_stat_exp),
                "p_value": float(p_value_exp),
                "fits_exponential": p_value_exp > 0.05
            }
        except Exception as e:
            pattern_tests["exponential_fit"] = {"error": str(e)}
        
        # 4. Test for uniform distribution
        try:
            uniform_params = stats.uniform.fit(ticks)
            ks_stat_uniform, p_value_uniform = stats.kstest(ticks, lambda x: stats.uniform.cdf(x, *uniform_params))
            pattern_tests["uniform_fit"] = {
                "parameters": [float(p) for p in uniform_params],
                "ks_statistic": float(ks_stat_uniform),
                "p_value": float(p_value_uniform),
                "fits_uniform": p_value_uniform > 0.05
            }
        except Exception as e:
            pattern_tests["uniform_fit"] = {"error": str(e)}
        
        # 5. Autocorrelation test (are consecutive values related?)
        if len(ticks) > 1:
            from scipy.stats import pearsonr
            autocorr_lag1 = pearsonr(ticks[:-1], ticks[1:])
            pattern_tests["autocorrelation_lag1"] = {
                "correlation": float(autocorr_lag1[0]),
                "p_value": float(autocorr_lag1[1]),
                "significant": autocorr_lag1[1] < 0.05
            }
        
        # 6. Runs test for randomness
        def runs_test(data):
            median = np.median(data)
            runs = []
            current_run = data[0] > median
            run_length = 1
            
            for i in range(1, len(data)):
                if (data[i] > median) == current_run:
                    run_length += 1
                else:
                    runs.append(run_length)
                    current_run = not current_run
                    run_length = 1
            runs.append(run_length)
            
            n_runs = len(runs)
            n1 = np.sum(data > median)
            n2 = len(data) - n1
            
            if n1 > 0 and n2 > 0:
                expected_runs = (2 * n1 * n2) / (n1 + n2) + 1
                variance_runs = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / ((n1 + n2) ** 2 * (n1 + n2 - 1))
                
                if variance_runs > 0:
                    z_score = (n_runs - expected_runs) / np.sqrt(variance_runs)
                    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
                    
                    return {
                        "n_runs": int(n_runs),
                        "expected_runs": float(expected_runs),
                        "z_score": float(z_score),
                        "p_value": float(p_value),
                        "appears_random": p_value > 0.05
                    }
            
            return {"error": "Cannot compute runs test"}
        
        pattern_tests["runs_test"] = runs_test(ticks)
        
        # Special multiplier analysis (common casino multipliers)
        special_multipliers = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0]
        special_analysis = {}
        for mult in special_multipliers:
            count = np.sum(np.abs(ticks - mult) < 0.01)  # Allow small tolerance
            special_analysis[f"mult_{mult}"] = {
                "exact_count": int(count),
                "percentage": float(count / len(ticks) * 100)
            }
        
        # Compile results
        analysis_results = {
            "analysis_type": "ticks_multiplication_coefficient_randomness",
            "summary": {
                "total_games": int(len(ticks)),
                "unique_values": int(unique_values),
                "uniqueness_ratio": float(unique_values / len(ticks)),
                "most_common_value": float(most_common[0]),
                "most_common_frequency": int(most_common[1])
            },
            "basic_statistics": basic_stats,
            "percentiles": percentiles,
            "top_20_most_common_multipliers": common_multipliers,
            "pattern_analysis": pattern_tests,
            "special_multipliers_frequency": special_analysis,
            "randomness_conclusion": self._assess_randomness(pattern_tests, basic_stats, ticks),
            "metadata": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "input_file": self.input_file
            }
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save results
        with open(self.output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        # Print summary
        print(f"\nTicks Randomness Analysis Results:")
        print(f"  Total unique values: {unique_values:,} out of {len(ticks):,} games")
        print(f"  Uniqueness ratio: {unique_values/len(ticks):.1%}")
        print(f"  Most common value: {most_common[0]:.2f} (appears {most_common[1]:,} times)")
        print(f"  Values under 2.0: {pattern_tests['low_values_under_2']['percentage']:.1f}%")
        print(f"  Whole numbers: {pattern_tests['whole_number_frequency']['percentage']:.1f}%")
        
        if 'runs_test' in pattern_tests and 'appears_random' in pattern_tests['runs_test']:
            print(f"  Runs test for randomness: {'RANDOM' if pattern_tests['runs_test']['appears_random'] else 'NOT RANDOM'}")
        
        if 'autocorrelation_lag1' in pattern_tests:
            print(f"  Autocorrelation: {pattern_tests['autocorrelation_lag1']['correlation']:.3f}")
        
        print(f"Analysis saved to: {self.output_file}")
    
    def _assess_randomness(self, pattern_tests, basic_stats, ticks=None):
        """Assess overall randomness based on test results."""
        randomness_indicators = []
        
        # High uniqueness suggests more randomness
        if basic_stats["count"] > 0 and ticks is not None:
            uniqueness_ratio = len(np.unique(ticks)) / basic_stats["count"]
            randomness_indicators.append(("high_uniqueness", uniqueness_ratio > 0.8))
        
        # Low autocorrelation suggests randomness
        if 'autocorrelation_lag1' in pattern_tests:
            low_autocorr = abs(pattern_tests['autocorrelation_lag1']['correlation']) < 0.1
            randomness_indicators.append(("low_autocorrelation", low_autocorr))
        
        # Runs test result
        if 'runs_test' in pattern_tests and 'appears_random' in pattern_tests['runs_test']:
            randomness_indicators.append(("runs_test", pattern_tests['runs_test']['appears_random']))
        
        # Distribution fit tests
        if 'exponential_fit' in pattern_tests and 'fits_exponential' in pattern_tests['exponential_fit']:
            randomness_indicators.append(("exponential_distribution", pattern_tests['exponential_fit']['fits_exponential']))
        
        random_indicators = sum(1 for _, is_random in randomness_indicators if is_random)
        total_indicators = len(randomness_indicators)
        
        if total_indicators > 0:
            randomness_score = random_indicators / total_indicators
            
            if randomness_score >= 0.7:
                conclusion = "LIKELY_RANDOM"
            elif randomness_score >= 0.4:
                conclusion = "PARTIALLY_RANDOM"
            else:
                conclusion = "LIKELY_NOT_RANDOM"
        else:
            conclusion = "INSUFFICIENT_DATA"
        
        return {
            "conclusion": conclusion,
            "randomness_score": float(randomness_score) if total_indicators > 0 else 0.0,
            "indicators_supporting_randomness": random_indicators,
            "total_indicators_tested": total_indicators,
            "supporting_evidence": [name for name, is_random in randomness_indicators if is_random]
        }


if __name__ == "__main__":
    luigi.run()