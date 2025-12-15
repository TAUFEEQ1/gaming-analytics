import pandas as pd
import pyarrow.parquet as pq
from datetime import datetime, timedelta
from scipy import stats
import numpy as np


class OperatorPerformanceHandler:
    """
    Handler for operator performance data with category-aware rankings using Z-scores.
    Allows comparison of operators across different game categories by standardizing
    their performance relative to their category mean.
    """
    
    def __init__(self, parquet_path='dashboard/data/operator_performance.parquet'):
        self.parquet_path = parquet_path
        self._df = None
    
    @property
    def df(self):
        """Lazy load dataframe"""
        if self._df is None:
            self._df = pq.read_table(self.parquet_path).to_pandas()
            # Convert date column to datetime if not already
            if not pd.api.types.is_datetime64_any_dtype(self._df['date']):
                self._df['date'] = pd.to_datetime(self._df['date'])
        return self._df
    
    def get_date_range_data(self, start_date=None, end_date=None):
        """Filter dataframe by date range"""
        df = self.df.copy()
        
        if start_date:
            start_date = pd.Timestamp(start_date)
            df = df[df['date'] >= start_date]
        
        if end_date:
            end_date = pd.Timestamp(end_date)
            df = df[df['date'] <= end_date]
        
        return df
    
    def calculate_category_stats(self, start_date=None, end_date=None):
        """
        Calculate mean and std for each operator tier
        
        Returns:
            DataFrame with operator_tier, mean_ggr, std_ggr, operator_count
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Aggregate by operator first, then by tier
        operator_totals = df.groupby(['operator', 'operator_tier']).agg({
            'GGR': 'sum'
        }).reset_index()
        
        # Group by tier and aggregate
        tier_stats = operator_totals.groupby('operator_tier').agg({
            'GGR': ['mean', 'std', 'count'],
            'operator': 'nunique'
        }).reset_index()
        
        tier_stats.columns = ['operator_tier', 'mean_ggr', 'std_ggr', 'operator_count', 'operator_count_check']
        tier_stats = tier_stats.drop('operator_count_check', axis=1)
        
        return tier_stats
    
    def calculate_operator_z_scores(self, start_date=None, end_date=None):
        """
        Calculate Z-scores for each operator within their operator tier.
        Z-score = (operator_ggr - tier_mean) / tier_std
        
        This allows comparing operators within the same tier (Small, Medium, Large, etc.)
        by how many standard deviations they are from their tier mean.
        
        Returns:
            DataFrame with operator, operator_tier, total_ggr, tier_mean, 
            tier_std, z_score, percentile, performance_tier
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Aggregate operator performance across all game categories
        operator_performance = df.groupby(['operator', 'operator_tier']).agg({
            'GGR': 'sum',
            'total_stake': 'sum',
            'total_payout': 'sum',
            'total_bets': 'sum',
            'movement_wager_mean': 'mean',
            'game_category': lambda x: ', '.join(x.unique())  # List all game categories
        }).reset_index()
        
        # Calculate tier statistics (mean and std for each operator tier)
        tier_stats = operator_performance.groupby('operator_tier')['GGR'].agg(['mean', 'std']).reset_index()
        tier_stats.columns = ['operator_tier', 'tier_mean', 'tier_std']
        
        # Merge tier stats with operator performance
        result = operator_performance.merge(tier_stats, on='operator_tier')
        
        # Calculate Z-scores
        result['z_score'] = (result['GGR'] - result['tier_mean']) / result['tier_std']
        
        # Replace inf/nan with 0 (for cases where std is 0 or very small)
        result['z_score'] = result['z_score'].replace([np.inf, -np.inf], 0).fillna(0)
        
        # Calculate percentile rank within tier
        result['percentile'] = result.groupby('operator_tier')['GGR'].rank(pct=True) * 100
        
        # Assign performance tiers based on Z-score
        def get_performance_tier(z_score):
            if z_score > 2:
                return 'Exceptional'
            elif z_score > 1:
                return 'Above Average'
            elif z_score > -1:
                return 'Average'
            elif z_score > -2:
                return 'Below Average'
            else:
                return 'Underperforming'
        
        result['performance_tier'] = result['z_score'].apply(get_performance_tier)
        
        # Rename columns for clarity
        result = result.rename(columns={'GGR': 'total_ggr'})
        
        return result
    
    def get_top_performers(self, n=10, start_date=None, end_date=None, by_tier=False):
        """
        Get top performing operators by Z-score (deviation from their tier mean)
        
        Args:
            n: Number of top performers to return
            start_date: Filter start date
            end_date: Filter end date
            by_tier: If True, return top n per tier; if False, return top n overall
        
        Returns:
            DataFrame with top performers
        """
        df_scores = self.calculate_operator_z_scores(start_date, end_date)
        
        if by_tier:
            # Get top n per tier
            top_performers = df_scores.groupby('operator_tier').apply(
                lambda x: x.nlargest(n, 'z_score')
            ).reset_index(drop=True)
        else:
            # Get top n overall (highest positive deviation from tier mean)
            top_performers = df_scores.nlargest(n, 'z_score')
        
        return top_performers
    
    def get_bottom_performers(self, n=10, start_date=None, end_date=None, by_tier=False):
        """
        Get bottom performing operators by Z-score (deviation from their tier mean)
        
        Args:
            n: Number of bottom performers to return
            start_date: Filter start date
            end_date: Filter end date
            by_tier: If True, return bottom n per tier; if False, return bottom n overall
        
        Returns:
            DataFrame with bottom performers
        """
        df_scores = self.calculate_operator_z_scores(start_date, end_date)
        
        if by_tier:
            # Get bottom n per tier
            bottom_performers = df_scores.groupby('operator_tier').apply(
                lambda x: x.nsmallest(n, 'z_score')
            ).reset_index(drop=True)
        else:
            # Get bottom n overall (lowest negative deviation from tier mean)
            bottom_performers = df_scores.nsmallest(n, 'z_score')
        
        return bottom_performers
    
    def get_underperformers_cross_tier(self, start_date=None, end_date=None):
        """
        Get all operators that underperform their tier mean (Z-score < 0)
        and rank them across tiers by Z-score.
        
        This allows comparing underperformers regardless of their tier,
        showing which operators deviate most negatively from their peer group.
        
        Returns:
            DataFrame with underperforming operators ranked by Z-score
        """
        df_scores = self.calculate_operator_z_scores(start_date, end_date)
        
        # Filter for underperformers (Z-score < 0)
        underperformers = df_scores[df_scores['z_score'] < 0].copy()
        
        # Sort by Z-score ascending (most underperforming first)
        underperformers = underperformers.sort_values('z_score')
        
        # Add cross-tier rank
        underperformers['cross_tier_rank'] = range(1, len(underperformers) + 1)
        
        return underperformers
    
    def get_operator_summary(self, start_date=None, end_date=None):
        """
        Get comprehensive summary of all operators with their Z-scores and rankings
        
        Returns:
            DataFrame with operator summaries including tier-based Z-scores
        """
        df_scores = self.calculate_operator_z_scores(start_date, end_date)
        
        # Since each operator now has one row (aggregated across game categories),
        # we can directly use the results
        operator_summary = df_scores[[
            'operator', 'operator_tier', 'GGR', 'z_score', 
            'percentile', 'performance_tier', 'game_category',
            'total_stake', 'total_payout', 'total_bets'
        ]].copy()
        
        operator_summary = operator_summary.rename(columns={'GGR': 'total_ggr'})
        
        # Sort by Z-score descending
        operator_summary = operator_summary.sort_values('z_score', ascending=False)
        
        # Add overall rank
        operator_summary['overall_rank'] = range(1, len(operator_summary) + 1)
        
        # Add rank within tier
        operator_summary['tier_rank'] = operator_summary.groupby('operator_tier')['z_score'].rank(ascending=False, method='dense').astype(int)
        
        return operator_summary
    
    def get_category_distribution(self, start_date=None, end_date=None):
        """
        Get distribution of operators and performance across game categories
        
        Returns:
            DataFrame with category metrics
        """
        df = self.get_date_range_data(start_date, end_date)
        
        category_dist = df.groupby('game_category').agg({
            'operator': 'nunique',
            'GGR': ['sum', 'mean', 'std'],
            'total_bets': 'sum',
            'total_stake': 'sum',
            'total_payout': 'sum'
        }).reset_index()
        
        category_dist.columns = ['game_category', 'operator_count', 'total_ggr', 
                                  'mean_ggr', 'std_ggr', 'total_bets', 
                                  'total_stake', 'total_payout']
        
        # Calculate market share
        category_dist['market_share'] = (category_dist['total_ggr'] / category_dist['total_ggr'].sum() * 100)
        
        return category_dist.sort_values('total_ggr', ascending=False)
