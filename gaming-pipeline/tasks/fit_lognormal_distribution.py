"""
Luigi task to fit a lognormal distribution on the skins price data.

This task reads the flattened price data and fits a lognormal distribution,
returning the distribution parameters in JSON format.
"""

import luigi
import pandas as pd
import numpy as np
import json
import os
from scipy import stats
from pathlib import Path


class FitLognormalDistributionTask(luigi.Task):
    """
    Luigi task to fit a lognormal distribution on the price data.
    
    Fits a lognormal distribution to the price column and outputs
    the distribution parameters (shape, loc, scale) in JSON format.
    """
    
    input_file = luigi.Parameter(default="output/simple_item_price.csv")
    output_file = luigi.Parameter(default="output/lognormal_distribution_params.json")
    
    def requires(self):
        """This task requires the flattened data to exist."""
        from tasks.flatten_skins_data import FlattenSkinsSimpleTask
        return FlattenSkinsSimpleTask()
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Fit the lognormal distribution and save parameters."""
        # Read the price data
        df = pd.read_csv(self.input_file)
        prices = df['price'].values
        
        # Remove any zero or negative prices (log-normal requires positive values)
        prices = prices[prices > 0]
        
        print(f"Fitting lognormal distribution on {len(prices)} price points")
        print(f"Price statistics:")
        print(f"  Mean: ${np.mean(prices):.2f}")
        print(f"  Median: ${np.median(prices):.2f}")
        print(f"  Min: ${np.min(prices):.2f}")
        print(f"  Max: ${np.max(prices):.2f}")
        print(f"  Std: ${np.std(prices):.2f}")
        
        # Fit lognormal distribution
        # scipy.stats.lognorm uses parameterization: lognorm(s, loc, scale)
        # where s is the shape parameter (sigma), loc is location, scale is exp(mu)
        shape, loc, scale = stats.lognorm.fit(prices, floc=0)  # floc=0 fixes location to 0
        
        # Calculate alternative parameterizations
        # For lognormal: if X ~ lognorm(s, loc, scale), then log(X-loc) ~ norm(log(scale), s)
        mu = np.log(scale)  # mean of underlying normal distribution
        sigma = shape       # std of underlying normal distribution
        
        # Calculate distribution statistics
        mean_theoretical = stats.lognorm.mean(shape, loc, scale)
        var_theoretical = stats.lognorm.var(shape, loc, scale)
        median_theoretical = stats.lognorm.median(shape, loc, scale)
        
        # Goodness of fit test
        ks_statistic, p_value = stats.kstest(prices, lambda x: stats.lognorm.cdf(x, shape, loc, scale))
        
        # Create comprehensive results dictionary
        results = {
            "distribution": "lognormal",
            "fitting_method": "maximum_likelihood_estimation",
            "data_summary": {
                "sample_size": int(len(prices)),
                "mean": float(np.mean(prices)),
                "median": float(np.median(prices)),
                "std": float(np.std(prices)),
                "min": float(np.min(prices)),
                "max": float(np.max(prices)),
                "skewness": float(stats.skew(prices)),
                "kurtosis": float(stats.kurtosis(prices))
            },
            "distribution_parameters": {
                "scipy_parameterization": {
                    "shape": float(shape),
                    "location": float(loc),
                    "scale": float(scale),
                    "description": "scipy.stats.lognorm(s=shape, loc=location, scale=scale)"
                },
                "standard_parameterization": {
                    "mu": float(mu),
                    "sigma": float(sigma),
                    "description": "log(X) ~ Normal(mu, sigma^2) where mu=log(scale), sigma=shape"
                }
            },
            "theoretical_statistics": {
                "mean": float(mean_theoretical),
                "variance": float(var_theoretical),
                "median": float(median_theoretical),
                "mode": float(np.exp(mu - sigma**2)) if sigma > 0 else None
            },
            "goodness_of_fit": {
                "kolmogorov_smirnov_test": {
                    "statistic": float(ks_statistic),
                    "p_value": float(p_value),
                    "interpretation": "good_fit" if p_value > 0.05 else "poor_fit"
                }
            },
            "percentiles": {
                f"{p}th": float(stats.lognorm.ppf(p/100, shape, loc, scale))
                for p in [5, 10, 25, 50, 75, 90, 95, 99]
            },
            "metadata": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "input_file": self.input_file,
                "output_file": self.output_file
            }
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save results to JSON
        with open(self.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\nLognormal Distribution Fit Results:")
        print(f"  Shape parameter (σ): {shape:.4f}")
        print(f"  Location parameter: {loc:.4f}")
        print(f"  Scale parameter: {scale:.4f}")
        print(f"  Standard form - μ: {mu:.4f}, σ: {sigma:.4f}")
        print(f"  Theoretical mean: ${mean_theoretical:.2f}")
        print(f"  Theoretical median: ${median_theoretical:.2f}")
        print(f"  KS test p-value: {p_value:.4f} ({'Good fit' if p_value > 0.05 else 'Poor fit'})")
        print(f"Results saved to: {self.output_file}")


class AnalyzePriceDistributionTask(luigi.Task):
    """
    Extended task that also generates distribution analysis and visualization data.
    """
    
    input_file = luigi.Parameter(default="output/simple_item_price.csv")
    output_file = luigi.Parameter(default="output/price_distribution_analysis.json")
    
    def requires(self):
        """This task requires the flattened data to exist."""
        from tasks.flatten_skins_data import FlattenSkinsSimpleTask
        return FlattenSkinsSimpleTask()
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Perform comprehensive distribution analysis."""
        # Read the price data
        df = pd.read_csv(self.input_file)
        prices = df['price'].values
        prices = prices[prices > 0]  # Remove non-positive prices
        
        print(f"Analyzing price distribution for {len(prices)} items")
        
        # Fit multiple distributions for comparison
        distributions = {
            'lognormal': stats.lognorm,
            'exponential': stats.expon,
            'gamma': stats.gamma,
            'weibull': stats.weibull_min
        }
        
        distribution_results = {}
        
        for name, dist in distributions.items():
            try:
                # Fit distribution
                if name == 'lognormal':
                    params = dist.fit(prices, floc=0)
                elif name == 'exponential':
                    params = dist.fit(prices, floc=0)
                else:
                    params = dist.fit(prices)
                
                # Calculate goodness of fit
                ks_stat, p_val = stats.kstest(prices, lambda x: dist.cdf(x, *params))
                
                # Calculate AIC/BIC for model comparison
                log_likelihood = np.sum(dist.logpdf(prices, *params))
                aic = 2 * len(params) - 2 * log_likelihood
                bic = len(params) * np.log(len(prices)) - 2 * log_likelihood
                
                distribution_results[name] = {
                    "parameters": [float(p) for p in params],
                    "log_likelihood": float(log_likelihood),
                    "aic": float(aic),
                    "bic": float(bic),
                    "ks_statistic": float(ks_stat),
                    "ks_p_value": float(p_val)
                }
                
            except Exception as e:
                print(f"Failed to fit {name} distribution: {e}")
                distribution_results[name] = {"error": str(e)}
        
        # Determine best fitting distribution
        valid_fits = {k: v for k, v in distribution_results.items() if 'error' not in v}
        if valid_fits:
            best_aic = min(valid_fits.items(), key=lambda x: x[1]['aic'])
            best_bic = min(valid_fits.items(), key=lambda x: x[1]['bic'])
            best_ks = max(valid_fits.items(), key=lambda x: x[1]['ks_p_value'])
        else:
            best_aic = best_bic = best_ks = None
        
        # Create comprehensive analysis
        analysis = {
            "analysis_type": "price_distribution_comparison",
            "data_summary": {
                "sample_size": int(len(prices)),
                "descriptive_statistics": {
                    "mean": float(np.mean(prices)),
                    "median": float(np.median(prices)),
                    "mode_estimate": float(stats.mode(prices, keepdims=False)[0]) if len(set(prices)) < len(prices)/2 else None,
                    "std": float(np.std(prices)),
                    "variance": float(np.var(prices)),
                    "skewness": float(stats.skew(prices)),
                    "kurtosis": float(stats.kurtosis(prices)),
                    "min": float(np.min(prices)),
                    "max": float(np.max(prices)),
                    "range": float(np.max(prices) - np.min(prices)),
                    "iqr": float(np.percentile(prices, 75) - np.percentile(prices, 25))
                },
                "percentiles": {
                    f"{p}th": float(np.percentile(prices, p))
                    for p in [1, 5, 10, 25, 50, 75, 90, 95, 99]
                }
            },
            "distribution_fits": distribution_results,
            "best_fit_candidates": {
                "by_aic": best_aic[0] if best_aic else None,
                "by_bic": best_bic[0] if best_bic else None,
                "by_ks_test": best_ks[0] if best_ks else None
            },
            "lognormal_specific": distribution_results.get('lognormal', {}),
            "metadata": {
                "timestamp": pd.Timestamp.now().isoformat(),
                "input_file": self.input_file
            }
        }
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
        
        # Save results
        with open(self.output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"Distribution analysis completed and saved to: {self.output_file}")
        if valid_fits:
            print(f"Best fit by AIC: {best_aic[0]} (AIC: {best_aic[1]['aic']:.2f})")
            print(f"Best fit by BIC: {best_bic[0]} (BIC: {best_bic[1]['bic']:.2f})")
            print(f"Best fit by KS test: {best_ks[0]} (p-value: {best_ks[1]['ks_p_value']:.4f})")


if __name__ == "__main__":
    luigi.run()