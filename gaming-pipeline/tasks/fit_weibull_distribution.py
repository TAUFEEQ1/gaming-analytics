"""
Luigi task to fit a Weibull distribution on the skins price data.

This task reads the flattened price data and fits a Weibull distribution,
returning the distribution parameters in JSON format.
"""

import luigi
import pandas as pd
import numpy as np
import json
import os
import math
from scipy import stats
from pathlib import Path


class FitWeibullDistributionTask(luigi.Task):
    """
    Luigi task to fit a Weibull distribution on the price data.
    
    Fits a Weibull distribution to the price column and outputs
    the distribution parameters (shape, scale) in JSON format.
    """
    
    input_file = luigi.Parameter(default="output/simple_item_price.csv")
    output_file = luigi.Parameter(default="output/weibull_distribution_params.json")
    
    def requires(self):
        """This task requires the flattened data to exist."""
        from tasks.flatten_skins_data import FlattenSkinsSimpleTask
        return FlattenSkinsSimpleTask()
    
    def output(self):
        """Define the output target."""
        return luigi.LocalTarget(self.output_file)
    
    def run(self):
        """Fit the Weibull distribution and save parameters."""
        # Read the price data
        df = pd.read_csv(self.input_file)
        prices = df['price'].values
        
        # Remove any zero or negative prices (Weibull requires positive values)
        prices = prices[prices > 0]
        
        print(f"Fitting Weibull distribution on {len(prices)} price points")
        print(f"Price statistics:")
        print(f"  Mean: ${np.mean(prices):.2f}")
        print(f"  Median: ${np.median(prices):.2f}")
        print(f"  Min: ${np.min(prices):.2f}")
        print(f"  Max: ${np.max(prices):.2f}")
        print(f"  Std: ${np.std(prices):.2f}")
        
        # Fit Weibull distribution (scipy uses weibull_min)
        # scipy.stats.weibull_min uses parameterization: weibull_min(c, loc, scale)
        # where c is the shape parameter (k), loc is location, scale is the scale parameter (λ)
        shape, loc, scale = stats.weibull_min.fit(prices, floc=0)  # floc=0 fixes location to 0
        
        # Alternative parameterizations
        k = shape  # shape parameter (Weibull k)
        lambda_param = scale  # scale parameter (Weibull λ)
        
        # Calculate distribution statistics
        mean_theoretical = stats.weibull_min.mean(shape, loc, scale)
        var_theoretical = stats.weibull_min.var(shape, loc, scale)
        median_theoretical = stats.weibull_min.median(shape, loc, scale)
        
        # Mode calculation for Weibull
        if shape > 1:
            mode_theoretical = scale * ((shape - 1) / shape) ** (1 / shape)
        else:
            mode_theoretical = 0.0  # Mode is at 0 when shape <= 1
        
        # Goodness of fit test
        ks_statistic, p_value = stats.kstest(prices, lambda x: stats.weibull_min.cdf(x, shape, loc, scale))
        
        # Calculate log-likelihood for model comparison
        log_likelihood = np.sum(stats.weibull_min.logpdf(prices, shape, loc, scale))
        aic = 2 * 3 - 2 * log_likelihood  # 3 parameters (shape, loc, scale)
        bic = 3 * np.log(len(prices)) - 2 * log_likelihood
        
        # Create comprehensive results dictionary
        results = {
            "distribution": "weibull",
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
                    "description": "scipy.stats.weibull_min(c=shape, loc=location, scale=scale)"
                },
                "standard_parameterization": {
                    "k": float(k),
                    "lambda": float(lambda_param),
                    "description": "f(x; k, λ) = (k/λ)(x/λ)^(k-1) * exp(-(x/λ)^k)"
                }
            },
            "theoretical_statistics": {
                "mean": float(mean_theoretical),
                "variance": float(var_theoretical),
                "median": float(median_theoretical),
                "mode": float(mode_theoretical)
            },
            "distribution_properties": {
                "shape_interpretation": self._interpret_shape(shape),
                "hazard_rate": "increasing" if shape > 1 else ("constant" if shape == 1 else "decreasing"),
                "coefficient_of_variation": float(np.sqrt(var_theoretical) / mean_theoretical),
                "gamma_function_mean": float(scale * math.gamma(1 + 1/shape)),
                "gamma_function_variance": float(scale**2 * (math.gamma(1 + 2/shape) - math.gamma(1 + 1/shape)**2))
            },
            "goodness_of_fit": {
                "kolmogorov_smirnov_test": {
                    "statistic": float(ks_statistic),
                    "p_value": float(p_value),
                    "interpretation": "good_fit" if p_value > 0.05 else "poor_fit"
                },
                "log_likelihood": float(log_likelihood),
                "aic": float(aic),
                "bic": float(bic)
            },
            "percentiles": {
                f"{p}th": float(stats.weibull_min.ppf(p/100, shape, loc, scale))
                for p in [5, 10, 25, 50, 75, 90, 95, 99]
            },
            "reliability_metrics": {
                "scale_percentiles": {
                    "10_percent_life": float(stats.weibull_min.ppf(0.1, shape, loc, scale)),
                    "50_percent_life": float(stats.weibull_min.ppf(0.5, shape, loc, scale)),
                    "90_percent_life": float(stats.weibull_min.ppf(0.9, shape, loc, scale))
                },
                "characteristic_life": float(scale),  # 63.2% of values are below this
                "mean_residual_life_at_median": float(self._mean_residual_life(median_theoretical, shape, scale))
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
        print(f"\nWeibull Distribution Fit Results:")
        print(f"  Shape parameter (k): {shape:.4f}")
        print(f"  Scale parameter (λ): {scale:.4f}")
        print(f"  Location parameter: {loc:.4f}")
        print(f"  Shape interpretation: {self._interpret_shape(shape)}")
        print(f"  Theoretical mean: ${mean_theoretical:.2f}")
        print(f"  Theoretical median: ${median_theoretical:.2f}")
        print(f"  Theoretical mode: ${mode_theoretical:.2f}")
        print(f"  AIC: {aic:.2f}, BIC: {bic:.2f}")
        print(f"  KS test p-value: {p_value:.4f} ({'Good fit' if p_value > 0.05 else 'Poor fit'})")
        print(f"Results saved to: {self.output_file}")
    
    def _interpret_shape(self, k):
        """Interpret the shape parameter value."""
        if k < 1:
            return f"Decreasing hazard rate (k={k:.3f} < 1) - high initial values, then decreasing"
        elif k == 1:
            return "Constant hazard rate (k=1) - equivalent to exponential distribution"
        elif 1 < k < 2:
            return f"Increasing hazard rate (k={k:.3f}) - moderate right skew"
        elif 2 <= k < 3.6:
            return f"Increasing hazard rate (k={k:.3f}) - approaching normal-like behavior"
        elif k >= 3.6:
            return f"Near-normal distribution (k={k:.3f} ≥ 3.6) - bell-shaped with slight skew"
        else:
            return f"Shape parameter k={k:.3f}"
    
    def _mean_residual_life(self, t, k, lambda_param):
        """Calculate mean residual life at time t."""
        if t <= 0:
            return lambda_param * math.gamma(1 + 1/k)
        
        # For Weibull, mean residual life = λ * Γ(1+1/k, (t/λ)^k) / exp(-(t/λ)^k)
        # This is a simplified approximation
        survival_prob = np.exp(-((t / lambda_param) ** k))
        if survival_prob > 0:
            return lambda_param * math.gamma(1 + 1/k) * survival_prob
        else:
            return 0.0


if __name__ == "__main__":
    luigi.run()