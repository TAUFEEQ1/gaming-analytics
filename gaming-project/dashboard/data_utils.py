"""
Data utilities for reading and processing GGR forecast data
"""
import pyarrow.parquet as pq
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings


class GGRDataHandler:
    """Handler for GGR forecast parquet data"""
    
    def __init__(self):
        self.parquet_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'ggr_forecast.parquet'
        self._df = None
    
    @property
    def df(self):
        """Lazy load dataframe"""
        if self._df is None:
            self._df = pq.read_table(str(self.parquet_file)).to_pandas()
            self._df['date'] = pd.to_datetime(self._df['date'])
        return self._df
    
    def get_date_range_data(self, start_date=None, end_date=None):
        """
        Get data filtered by date range
        
        Args:
            start_date: Start date (datetime, date, or str)
            end_date: End date (datetime, date, or str)
        
        Returns:
            Filtered dataframe
        """
        df = self.df.copy()
        
        if start_date:
            # Convert to pandas Timestamp for comparison
            start_date = pd.Timestamp(start_date)
            df = df[df['date'] >= start_date]
        
        if end_date:
            # Convert to pandas Timestamp for comparison
            end_date = pd.Timestamp(end_date)
            df = df[df['date'] <= end_date]
        
        return df
    
    def get_kpis(self, start_date=None, end_date=None):
        """
        Calculate KPIs for the given date range
        
        Returns:
            dict: Dictionary with KPI values
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Get unique operators
        all_operators = set()
        for ops in df['operators_list']:
            if pd.notna(ops) and ops:
                all_operators.update(ops.split(','))
        
        return {
            'total_ggr': float(df['GGR'].sum()),
            'total_stake': float(df['total_stake'].sum()),
            'total_payout': float(df['total_payout'].sum()),
            'total_operators': len(all_operators),
            'total_bets': int(df['total_bets'].sum()),
            'total_anomalies': int(df['is_anomaly'].sum()),
        }
    
    def get_time_series_data(self, start_date=None, end_date=None):
        """
        Get time series data for charting (actual vs expected GGR)
        
        Returns:
            dict: Chart data with dates, actual_ggr, expected_ggr
        """
        df = self.get_date_range_data(start_date, end_date)
        
        return {
            'dates': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'actual_ggr': df['GGR'].tolist(),
            'expected_ggr': df['expected_GGR'].tolist(),
            'anomalies': df['is_anomaly'].tolist(),
        }
    
    def get_filter_dates(self, filter_type='all'):
        """
        Get start and end dates based on filter type
        
        Args:
            filter_type: 'today', 'week', 'month', 'all', 'custom'
        
        Returns:
            tuple: (start_date, end_date)
        """
        today = datetime.now().date()
        
        if filter_type == 'today':
            start_date = today
            end_date = today
        elif filter_type == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif filter_type == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        else:  # All data (default)
            start_date = self.df['date'].min().date()
            end_date = self.df['date'].max().date()
        
        return start_date, end_date
    
    def get_operators_list(self):
        """Get list of all unique operators"""
        all_operators = set()
        for ops in self.df['operators_list']:
            if pd.notna(ops) and ops:
                all_operators.update(ops.split(','))
        return sorted(all_operators)
    
    def get_anomalies_details(self, start_date=None, end_date=None):
        """
        Get detailed information about anomalies
        
        Returns:
            list: List of anomaly dictionaries with date, actual, expected, score
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Filter for anomalies only
        anomalies_df = df[df['is_anomaly'] == 1].copy()
        
        anomalies = []
        for _, row in anomalies_df.iterrows():
            anomalies.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'actual_ggr': float(row['GGR']),
                'expected_ggr': float(row['expected_GGR']),
                'anomaly_score': float(row['anomaly_score']),
                'variance': float(row['GGR'] - row['expected_GGR']),
                'variance_percent': float((row['GGR'] - row['expected_GGR']) / row['expected_GGR'] * 100) if row['expected_GGR'] != 0 else 0,
                'operators': row['operators_list'] if pd.notna(row['operators_list']) else 'N/A'
            })
        
        # Sort by date descending
        anomalies.sort(key=lambda x: x['date'], reverse=True)
        
        return anomalies
