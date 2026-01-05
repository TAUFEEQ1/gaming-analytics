"""
Utilities for analyzing NLGRB vs URA tax deviation
"""
import pandas as pd
from pathlib import Path
from django.conf import settings
from datetime import datetime, timedelta


class DeviationAnalysisHandler:
    """Handler for analyzing NLGRB vs URA tax collection deviations"""
    
    def __init__(self):
        self.parquet_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'deviation_analysis_results.parquet'
        self._df = None
    
    @property
    def df(self):
        """Lazy load dataframe"""
        if self._df is None:
            self._df = pd.read_parquet(str(self.parquet_file))
            # Ensure Month_Year column is datetime
            if 'Month_Year' in self._df.columns:
                self._df['Month_Year'] = pd.to_datetime(self._df['Month_Year'])
        return self._df
    
    def _filter_by_months(self, df, months_filter):
        """
        Filter dataframe by months
        
        Args:
            df: DataFrame to filter
            months_filter: '3', '6', '12', or 'all'
        
        Returns:
            Filtered dataframe
        """
        if months_filter == 'all':
            return df
        
        try:
            months = int(months_filter)
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            return df[df['Month_Year'] >= cutoff_date]
        except (ValueError, TypeError):
            return df
    
    def get_operators_summary(self, months_filter='all'):
        """
        Get summary of all operators with deviation metrics
        
        Args:
            months_filter: Filter by months ('3', '6', '12', or 'all')
        
        Returns:
            list: List of dicts with operator summaries
        """
        df = self.df.copy()
        
        # Apply time filter
        df = self._filter_by_months(df, months_filter)
        
        # Group by operator
        operator_summaries = []
        
        for operator in df['Operator_Name'].unique():
            operator_df = df[df['Operator_Name'] == operator]
            
            # Aggregate metrics
            total_nlgrb = float(operator_df['NLGRB_Returns'].sum())
            total_ura = float(operator_df['URA_Collections'].sum())
            total_abs_deviation = float(operator_df['Abs_Residual'].sum())
            
            # Calculate percentage variance
            if total_nlgrb > 0:
                percentage_variance = ((total_ura - total_nlgrb) / total_nlgrb) * 100
            else:
                percentage_variance = 0.0
            
            # Count months and anomalies
            months_count = len(operator_df)
            anomalies_count = len(operator_df[operator_df['Is_Anomaly'] == True])
            
            operator_summaries.append({
                'operator_name': operator,
                'total_nlgrb': total_nlgrb,
                'total_ura': total_ura,
                'total_deviation': total_ura - total_nlgrb,  # Signed deviation
                'total_abs_deviation': total_abs_deviation,
                'percentage_variance': percentage_variance,
                'months_count': months_count,
                'anomalies_count': anomalies_count,
                'has_anomalies': anomalies_count > 0,
            })
        
        # Sort by absolute deviation descending
        operator_summaries.sort(key=lambda x: -x['total_abs_deviation'])
        
        return operator_summaries
    
    def get_summary_statistics(self, months_filter='all'):
        """
        Get overall summary statistics
        
        Args:
            months_filter: Filter by months ('3', '6', '12', or 'all')
        
        Returns:
            dict: Summary statistics
        """
        df = self.df.copy()
        
        # Apply time filter
        df = self._filter_by_months(df, months_filter)
        
        total_operators = df['Operator_Name'].nunique()
        total_nlgrb = float(df['NLGRB_Returns'].sum())
        total_ura = float(df['URA_Collections'].sum())
        total_abs_deviation = float(df['Abs_Residual'].sum())
        
        # Count operators with anomalies
        operators_with_anomalies = df[df['Is_Anomaly'] == True]['Operator_Name'].nunique()
        
        # Calculate overall percentage variance
        if total_nlgrb > 0:
            overall_percentage_variance = ((total_ura - total_nlgrb) / total_nlgrb) * 100
        else:
            overall_percentage_variance = 0.0
        
        return {
            'total_operators': total_operators,
            'total_nlgrb': total_nlgrb,
            'total_ura': total_ura,
            'total_abs_deviation': total_abs_deviation,
            'overall_percentage_variance': overall_percentage_variance,
            'operators_with_anomalies': operators_with_anomalies,
        }
    
    def get_operator_detail(self, operator_name, months_filter='all'):
        """
        Get detailed monthly breakdown for a specific operator
        
        Args:
            operator_name: Name of the operator
            months_filter: Filter by months ('3', '6', '12', or 'all')
        
        Returns:
            DataFrame: Filtered monthly data for the operator
        """
        df = self.df.copy()
        
        # Apply time filter
        df = self._filter_by_months(df, months_filter)
        
        # Filter by operator
        operator_df = df[df['Operator_Name'] == operator_name].copy()
        
        # Sort by date descending
        operator_df = operator_df.sort_values('Month_Year', ascending=False)
        
        return operator_df
