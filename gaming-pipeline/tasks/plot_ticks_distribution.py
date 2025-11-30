"""
Luigi task to plot the ticks (multiplication coefficient) distribution.

This task creates comprehensive visualizations of the ticks data to show
its distribution characteristics and compare against theoretical distributions.
"""

import luigi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy import stats
from pathlib import Path


class PlotTicksDistributionTask(luigi.Task):
    """
    Luigi task to create comprehensive plots of the ticks distribution.
    """
    
    input_file = luigi.Parameter(default="data/onlineCasino.csv")
    output_dir = luigi.Parameter(default="output/plots")
    
    def requires(self):
        """No dependencies for this task."""
        return []
    
    def output(self):
        """Define the output targets for all plots."""
        return [
            luigi.LocalTarget(f"{self.output_dir}/ticks_histogram.png"),
            luigi.LocalTarget(f"{self.output_dir}/ticks_log_histogram.png"),
            luigi.LocalTarget(f"{self.output_dir}/ticks_distribution_comparison.png"),
            luigi.LocalTarget(f"{self.output_dir}/ticks_comprehensive_analysis.png")
        ]
    
    def run(self):
        """Generate comprehensive plots of ticks distribution."""
        # Read the data
        df = pd.read_csv(self.input_file)
        ticks = df['ticks'].values
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"Creating plots for {len(ticks):,} tick values...")
        
        # Set up plotting style
        plt.style.use('default')
        
        # Plot 1: Basic Histogram
        self._plot_basic_histogram(ticks)
        
        # Plot 2: Log-scale Histogram  
        self._plot_log_histogram(ticks)
        
        # Plot 3: Distribution Comparison
        self._plot_distribution_comparison(ticks)
        
        # Plot 4: Comprehensive Analysis
        self._plot_comprehensive_analysis(ticks)
        
        print(f"All plots saved to: {self.output_dir}/")
    
    def _plot_basic_histogram(self, ticks):
        """Plot basic histogram of ticks."""
        plt.figure(figsize=(12, 8))
        
        # Main histogram
        plt.subplot(2, 2, 1)
        plt.hist(ticks, bins=100, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('Multiplication Coefficient (ticks)')
        plt.ylabel('Frequency')
        plt.title('Distribution of Multiplication Coefficients')
        plt.grid(True, alpha=0.3)
        
        # Zoomed in view (≤ 10x)
        plt.subplot(2, 2, 2)
        ticks_zoom = ticks[ticks <= 10]
        plt.hist(ticks_zoom, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
        plt.xlabel('Multiplication Coefficient (≤ 10x)')
        plt.ylabel('Frequency')
        plt.title('Zoomed View: Multipliers ≤ 10x')
        plt.grid(True, alpha=0.3)
        
        # Box plot
        plt.subplot(2, 2, 3)
        plt.boxplot(ticks, vert=True)
        plt.ylabel('Multiplication Coefficient')
        plt.title('Box Plot of Multipliers')
        plt.grid(True, alpha=0.3)
        
        # Cumulative distribution
        plt.subplot(2, 2, 4)
        sorted_ticks = np.sort(ticks)
        cumulative = np.arange(1, len(sorted_ticks) + 1) / len(sorted_ticks)
        plt.plot(sorted_ticks, cumulative, 'b-', linewidth=2)
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Cumulative Probability')
        plt.title('Cumulative Distribution Function')
        plt.grid(True, alpha=0.3)
        plt.xlim(0, 50)  # Limit x-axis for visibility
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/ticks_histogram.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _plot_log_histogram(self, ticks):
        """Plot histogram on log scale."""
        plt.figure(figsize=(14, 10))
        
        # Log-scale histogram
        plt.subplot(2, 3, 1)
        plt.hist(ticks, bins=100, alpha=0.7, color='green')
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Frequency')
        plt.title('Linear Scale Histogram')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 3, 2)
        plt.hist(ticks, bins=100, alpha=0.7, color='orange')
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Frequency')
        plt.title('Log-Log Scale Histogram')
        plt.xscale('log')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)
        
        # Log-transformed data histogram
        plt.subplot(2, 3, 3)
        log_ticks = np.log(ticks)
        plt.hist(log_ticks, bins=50, alpha=0.7, color='purple', edgecolor='black')
        plt.xlabel('Log(Multiplication Coefficient)')
        plt.ylabel('Frequency')
        plt.title('Histogram of Log-Transformed Data')
        plt.grid(True, alpha=0.3)
        
        # Q-Q plot against normal (for lognormal test)
        plt.subplot(2, 3, 4)
        stats.probplot(log_ticks, dist="norm", plot=plt)
        plt.title('Q-Q Plot: Log(ticks) vs Normal')
        plt.grid(True, alpha=0.3)
        
        # Percentile analysis
        plt.subplot(2, 3, 5)
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        values = [np.percentile(ticks, p) for p in percentiles]
        plt.plot(percentiles, values, 'ro-', linewidth=2, markersize=8)
        plt.xlabel('Percentile')
        plt.ylabel('Multiplication Coefficient')
        plt.title('Percentile Analysis')
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        
        # Frequency of common multipliers
        plt.subplot(2, 3, 6)
        common_mults = [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0, 100.0]
        frequencies = []
        for mult in common_mults:
            count = np.sum(np.abs(ticks - mult) < 0.01)
            frequencies.append(count)
        
        plt.bar([str(m) + 'x' for m in common_mults], frequencies, color='red', alpha=0.7)
        plt.xlabel('Common Multipliers')
        plt.ylabel('Frequency')
        plt.title('Frequency of Round Number Multipliers')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/ticks_log_histogram.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _plot_distribution_comparison(self, ticks):
        """Compare against theoretical distributions."""
        plt.figure(figsize=(16, 12))
        
        # Fit distributions
        lognorm_params = stats.lognorm.fit(ticks, floc=0)
        exp_params = stats.expon.fit(ticks)
        weibull_params = stats.weibull_min.fit(ticks, floc=0)
        
        x_range = np.linspace(1, 100, 1000)
        
        # Plot 1: PDF comparison
        plt.subplot(2, 3, 1)
        plt.hist(ticks[ticks <= 100], bins=50, density=True, alpha=0.5, color='gray', label='Actual Data')
        
        plt.plot(x_range, stats.lognorm.pdf(x_range, *lognorm_params), 'r-', 
                label=f'Lognormal (σ={lognorm_params[0]:.2f})', linewidth=2)
        plt.plot(x_range, stats.expon.pdf(x_range, *exp_params), 'b-',
                label=f'Exponential (λ={1/exp_params[1]:.2f})', linewidth=2)
        plt.plot(x_range, stats.weibull_min.pdf(x_range, *weibull_params), 'g-',
                label=f'Weibull (k={weibull_params[0]:.2f})', linewidth=2)
        
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Probability Density')
        plt.title('PDF Comparison (≤ 100x)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        
        # Plot 2: CDF comparison
        plt.subplot(2, 3, 2)
        sorted_ticks = np.sort(ticks[ticks <= 100])
        empirical_cdf = np.arange(1, len(sorted_ticks) + 1) / len(sorted_ticks)
        
        plt.plot(sorted_ticks, empirical_cdf, 'k-', label='Empirical CDF', linewidth=3)
        plt.plot(x_range, stats.lognorm.cdf(x_range, *lognorm_params), 'r--', 
                label='Lognormal CDF', linewidth=2)
        plt.plot(x_range, stats.expon.cdf(x_range, *exp_params), 'b--',
                label='Exponential CDF', linewidth=2)
        plt.plot(x_range, stats.weibull_min.cdf(x_range, *weibull_params), 'g--',
                label='Weibull CDF', linewidth=2)
        
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Cumulative Probability')
        plt.title('CDF Comparison (≤ 100x)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Survival function (1 - CDF)
        plt.subplot(2, 3, 3)
        plt.plot(sorted_ticks, 1 - empirical_cdf, 'k-', label='Empirical Survival', linewidth=3)
        plt.plot(x_range, 1 - stats.lognorm.cdf(x_range, *lognorm_params), 'r--', 
                label='Lognormal Survival', linewidth=2)
        plt.plot(x_range, 1 - stats.expon.cdf(x_range, *exp_params), 'b--',
                label='Exponential Survival', linewidth=2)
        
        plt.xlabel('Multiplication Coefficient')
        plt.ylabel('Survival Probability')
        plt.title('Survival Function (1 - CDF)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        
        # Plot 4: Log-scale comparison
        plt.subplot(2, 3, 4)
        log_ticks = np.log(ticks)
        plt.hist(log_ticks, bins=50, density=True, alpha=0.5, color='gray', label='Log(Actual Data)')
        
        # Normal distribution for comparison (if lognormal)
        log_x = np.linspace(log_ticks.min(), log_ticks.max(), 1000)
        mu, sigma = stats.norm.fit(log_ticks)
        plt.plot(log_x, stats.norm.pdf(log_x, mu, sigma), 'r-', 
                label=f'Normal (μ={mu:.2f}, σ={sigma:.2f})', linewidth=2)
        
        plt.xlabel('Log(Multiplication Coefficient)')
        plt.ylabel('Probability Density')
        plt.title('Log-Scale Distribution')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Plot 5: Tail behavior
        plt.subplot(2, 3, 5)
        tail_data = ticks[ticks > 10]
        if len(tail_data) > 0:
            plt.hist(tail_data, bins=30, alpha=0.7, color='red', label=f'Tail Data (n={len(tail_data)})')
            plt.xlabel('Multiplication Coefficient (> 10x)')
            plt.ylabel('Frequency')
            plt.title('Tail Behavior Analysis')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.yscale('log')
        
        # Plot 6: Goodness of fit statistics
        plt.subplot(2, 3, 6)
        distributions = ['Lognormal', 'Exponential', 'Weibull']
        
        # Calculate KS test statistics
        ks_lognorm = stats.kstest(ticks, lambda x: stats.lognorm.cdf(x, *lognorm_params))[0]
        ks_exp = stats.kstest(ticks, lambda x: stats.expon.cdf(x, *exp_params))[0]
        ks_weibull = stats.kstest(ticks, lambda x: stats.weibull_min.cdf(x, *weibull_params))[0]
        
        ks_stats = [ks_lognorm, ks_exp, ks_weibull]
        colors = ['red', 'blue', 'green']
        
        bars = plt.bar(distributions, ks_stats, color=colors, alpha=0.7)
        plt.ylabel('KS Test Statistic')
        plt.title('Goodness of Fit Comparison\n(Lower = Better Fit)')
        plt.grid(True, alpha=0.3)
        
        # Add values on bars
        for bar, stat in zip(bars, ks_stats):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    f'{stat:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/ticks_distribution_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
    def _plot_comprehensive_analysis(self, ticks):
        """Create a comprehensive analysis plot."""
        fig, axes = plt.subplots(3, 3, figsize=(18, 15))
        fig.suptitle('Comprehensive Ticks Distribution Analysis', fontsize=16)
        
        # Plot 1: Main histogram
        axes[0,0].hist(ticks, bins=100, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0,0].set_xlabel('Multiplication Coefficient')
        axes[0,0].set_ylabel('Frequency')
        axes[0,0].set_title('Full Distribution')
        axes[0,0].grid(True, alpha=0.3)
        
        # Plot 2: Low values detail (≤ 5x)
        low_ticks = ticks[ticks <= 5]
        axes[0,1].hist(low_ticks, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[0,1].set_xlabel('Multiplication Coefficient (≤ 5x)')
        axes[0,1].set_ylabel('Frequency')
        axes[0,1].set_title(f'Low Multipliers (n={len(low_ticks):,})')
        axes[0,1].grid(True, alpha=0.3)
        
        # Plot 3: Time series (first 1000 values)
        sample_size = min(1000, len(ticks))
        axes[0,2].plot(range(sample_size), ticks[:sample_size], alpha=0.7, linewidth=0.5)
        axes[0,2].set_xlabel('Game Number')
        axes[0,2].set_ylabel('Multiplication Coefficient')
        axes[0,2].set_title('Time Series (First 1000 Games)')
        axes[0,2].grid(True, alpha=0.3)
        
        # Plot 4: Log-log plot
        axes[1,0].hist(ticks, bins=100, alpha=0.7, color='orange')
        axes[1,0].set_xlabel('Multiplication Coefficient')
        axes[1,0].set_ylabel('Frequency')
        axes[1,0].set_title('Log-Log Scale')
        axes[1,0].set_xscale('log')
        axes[1,0].set_yscale('log')
        axes[1,0].grid(True, alpha=0.3)
        
        # Plot 5: Autocorrelation
        if len(ticks) > 100:
            lags = range(1, 21)
            autocorrs = []
            for lag in lags:
                if lag < len(ticks):
                    corr = np.corrcoef(ticks[:-lag], ticks[lag:])[0,1]
                    autocorrs.append(corr)
                else:
                    autocorrs.append(0)
            
            axes[1,1].plot(lags, autocorrs, 'ro-', markersize=4)
            axes[1,1].axhline(y=0, color='black', linestyle='--', alpha=0.5)
            axes[1,1].set_xlabel('Lag')
            axes[1,1].set_ylabel('Autocorrelation')
            axes[1,1].set_title('Autocorrelation Function')
            axes[1,1].grid(True, alpha=0.3)
        
        # Plot 6: Extreme values
        extreme_threshold = np.percentile(ticks, 99)
        extreme_ticks = ticks[ticks > extreme_threshold]
        if len(extreme_ticks) > 0:
            axes[1,2].hist(extreme_ticks, bins=20, alpha=0.7, color='red', edgecolor='black')
            axes[1,2].set_xlabel('Multiplication Coefficient')
            axes[1,2].set_ylabel('Frequency')
            axes[1,2].set_title(f'Extreme Values (>99th percentile)\nn={len(extreme_ticks)}')
            axes[1,2].grid(True, alpha=0.3)
        
        # Plot 7: Statistics summary
        axes[2,0].axis('off')
        stats_text = f"""
        Sample Size: {len(ticks):,}
        Mean: {np.mean(ticks):.2f}
        Median: {np.median(ticks):.2f}
        Std Dev: {np.std(ticks):.2f}
        Min: {np.min(ticks):.2f}
        Max: {np.max(ticks):.2f}
        
        Skewness: {stats.skew(ticks):.2f}
        Kurtosis: {stats.kurtosis(ticks):.2f}
        
        Values ≤ 2.0x: {np.sum(ticks <= 2.0)/len(ticks)*100:.1f}%
        Values ≤ 5.0x: {np.sum(ticks <= 5.0)/len(ticks)*100:.1f}%
        Values > 10.0x: {np.sum(ticks > 10.0)/len(ticks)*100:.1f}%
        """
        axes[2,0].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                      bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        axes[2,0].set_title('Summary Statistics')
        
        # Plot 8: Percentile plot
        percentiles = np.arange(5, 100, 5)
        values = [np.percentile(ticks, p) for p in percentiles]
        axes[2,1].semilogy(percentiles, values, 'bo-', markersize=4)
        axes[2,1].set_xlabel('Percentile')
        axes[2,1].set_ylabel('Value (log scale)')
        axes[2,1].set_title('Percentile Plot')
        axes[2,1].grid(True, alpha=0.3)
        
        # Plot 9: Density estimate
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(ticks[ticks <= 20])  # Limit to reasonable range
        x_kde = np.linspace(1, 20, 200)
        axes[2,2].plot(x_kde, kde(x_kde), 'b-', linewidth=2, label='KDE')
        axes[2,2].hist(ticks[ticks <= 20], bins=50, density=True, alpha=0.3, color='gray')
        axes[2,2].set_xlabel('Multiplication Coefficient (≤ 20x)')
        axes[2,2].set_ylabel('Density')
        axes[2,2].set_title('Kernel Density Estimation')
        axes[2,2].legend()
        axes[2,2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/ticks_comprehensive_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Basic histogram plot created")
        print("✓ Log-scale analysis plot created") 
        print("✓ Distribution comparison plot created")
        print("✓ Comprehensive analysis plot created")


if __name__ == "__main__":
    luigi.run()