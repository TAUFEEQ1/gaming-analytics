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
            filter_type: 'today', 'week', 'month', 'q1', 'q2', 'q3', 'q4', 'all', 'custom'
        
        Returns:
            tuple: (start_date, end_date)
        """
        today = datetime.now().date()
        current_year = today.year
        
        if filter_type == 'today':
            start_date = today
            end_date = today
        elif filter_type == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif filter_type == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        elif filter_type == 'q1':
            start_date = datetime(current_year, 1, 1).date()
            end_date = datetime(current_year, 3, 31).date()
        elif filter_type == 'q2':
            start_date = datetime(current_year, 4, 1).date()
            end_date = datetime(current_year, 6, 30).date()
        elif filter_type == 'q3':
            start_date = datetime(current_year, 7, 1).date()
            end_date = datetime(current_year, 9, 30).date()
        elif filter_type == 'q4':
            start_date = datetime(current_year, 10, 1).date()
            end_date = datetime(current_year, 12, 31).date()
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


class AnomalyDataHandler:
    """Handler for anomaly detection parquet data"""
    
    def __init__(self):
        self.combined_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'combined_anomalies_full_detail.parquet'
        self.anomalies_only_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'anomalies_only_full_detail.parquet'
        self._df = None
        self._anomalies_df = None
    
    @property
    def df(self):
        """Lazy load full dataset (all records)"""
        if self._df is None:
            self._df = pq.read_table(str(self.combined_file)).to_pandas()
            self._df['date'] = pd.to_datetime(self._df['date'])
        return self._df
    
    @property
    def anomalies_df(self):
        """Lazy load anomalies only dataset"""
        if self._anomalies_df is None:
            self._anomalies_df = pq.read_table(str(self.anomalies_only_file)).to_pandas()
            self._anomalies_df['date'] = pd.to_datetime(self._anomalies_df['date'])
        return self._anomalies_df
    
    def get_date_range_data(self, start_date=None, end_date=None, anomalies_only=False):
        """
        Get data filtered by date range
        
        Args:
            start_date: Start date (datetime, date, or str)
            end_date: End date (datetime, date, or str)
            anomalies_only: If True, use anomalies-only dataset
        
        Returns:
            Filtered dataframe
        """
        df = self.anomalies_df.copy() if anomalies_only else self.df.copy()
        
        if start_date:
            start_date = pd.Timestamp(start_date)
            df = df[df['date'] >= start_date]
        
        if end_date:
            end_date = pd.Timestamp(end_date)
            df = df[df['date'] <= end_date]
        
        return df
    
    def get_filter_dates(self, filter_type='all'):
        """
        Get start and end dates based on filter type
        
        Args:
            filter_type: 'today', 'week', 'month', 'q1', 'q2', 'q3', 'q4', 'all', 'custom'
        
        Returns:
            tuple: (start_date, end_date)
        """
        today = datetime.now().date()
        current_year = today.year
        
        if filter_type == 'today':
            start_date = today
            end_date = today
        elif filter_type == 'week':
            start_date = today - timedelta(days=7)
            end_date = today
        elif filter_type == 'month':
            start_date = today - timedelta(days=30)
            end_date = today
        elif filter_type == 'q1':
            start_date = datetime(current_year, 1, 1).date()
            end_date = datetime(current_year, 3, 31).date()
        elif filter_type == 'q2':
            start_date = datetime(current_year, 4, 1).date()
            end_date = datetime(current_year, 6, 30).date()
        elif filter_type == 'q3':
            start_date = datetime(current_year, 7, 1).date()
            end_date = datetime(current_year, 9, 30).date()
        elif filter_type == 'q4':
            start_date = datetime(current_year, 10, 1).date()
            end_date = datetime(current_year, 12, 31).date()
        else:  # All data (default)
            start_date = self.df['date'].min().date()
            end_date = self.df['date'].max().date()
        
        return start_date, end_date
    
    def get_operators_summary(self, start_date=None, end_date=None):
        """
        Get summary statistics for all operators
        
        Returns:
            list: List of operator dictionaries with aggregated stats
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Group by operator
        operator_groups = df.groupby('operator').agg({
            'total_stake': 'sum',
            'total_payout': 'sum',
            'is_anomaly_stake': 'sum',
            'is_anomaly_payout': 'sum',
            'is_anomaly_combined': 'sum',
            'operator_tier': 'first',
            'date': 'count'  # Number of records
        }).reset_index()
        
        # Calculate GGR
        operator_groups['ggr'] = operator_groups['total_stake'] - operator_groups['total_payout']
        
        # Rename columns
        operator_groups.rename(columns={
            'is_anomaly_stake': 'stake_anomalies',
            'is_anomaly_payout': 'payout_anomalies',
            'is_anomaly_combined': 'total_anomalies',
            'date': 'record_count'
        }, inplace=True)
        
        # Convert to list of dicts
        operators = operator_groups.to_dict('records')
        
        # Sort by GGR descending
        operators.sort(key=lambda x: x['ggr'], reverse=True)
        
        return operators
    
    def get_operator_detail(self, operator_code, start_date=None, end_date=None):
        """
        Get detailed records for a specific operator
        
        Args:
            operator_code: Operator code (e.g., 'INT', 'MAS')
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            dict: Operator details including time series and anomaly records
        """
        df = self.get_date_range_data(start_date, end_date)
        
        # Filter for specific operator
        operator_df = df[df['operator'] == operator_code].copy()
        
        if operator_df.empty:
            return None
        
        # Calculate GGR
        operator_df['ggr'] = operator_df['total_stake'] - operator_df['total_payout']
        
        # Sort by date
        operator_df = operator_df.sort_values('date')
        
        # Get summary stats
        total_stake = float(operator_df['total_stake'].sum())
        total_payout = float(operator_df['total_payout'].sum())
        total_ggr = total_stake - total_payout
        
        # Get time series data
        time_series = {
            'dates': operator_df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'stakes': operator_df['total_stake'].tolist(),
            'payouts': operator_df['total_payout'].tolist(),
            'ggr': operator_df['ggr'].tolist()
        }
        
        # Get anomaly records
        anomalies = operator_df[operator_df['is_anomaly_combined'] == 1].copy()
        anomaly_records = []
        
        for _, row in anomalies.iterrows():
            anomaly_records.append({
                'date': row['date'],
                'anomaly_type': row['anomaly_type'],
                'total_stake': float(row['total_stake']),
                'total_payout': float(row['total_payout']),
                'ggr': float(row['ggr']),
                'stake_flagged': row['is_anomaly_stake'] == 1,
                'payout_flagged': row['is_anomaly_payout'] == 1,
                'stake_deviation_pct': float(row['stake_deviation_pct']) if pd.notna(row['stake_deviation_pct']) else None,
                'payout_deviation_pct': float(row['payout_deviation_pct']) if pd.notna(row['payout_deviation_pct']) else None,
                'stake_predicted': float(row['stake_predicted']) if pd.notna(row['stake_predicted']) else None,
                'payout_predicted': float(row['payout_predicted']) if pd.notna(row['payout_predicted']) else None,
            })
        
        # Sort anomalies by date descending
        anomaly_records.sort(key=lambda x: x['date'], reverse=True)
        
        # Get all daily records for table
        all_records = []
        for _, row in operator_df.iterrows():
            all_records.append({
                'date': row['date'],
                'total_stake': float(row['total_stake']),
                'total_payout': float(row['total_payout']),
                'ggr': float(row['ggr']),
                'stake_flagged': row['is_anomaly_stake'] == 1,
                'payout_flagged': row['is_anomaly_payout'] == 1,
                'has_anomaly': row['is_anomaly_combined'] == 1,
                'anomaly_type': row['anomaly_type'] if row['is_anomaly_combined'] == 1 else 'Normal'
            })
        
        # Sort all records by date descending
        all_records.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'operator': operator_code,
            'operator_tier': operator_df['operator_tier'].iloc[0],
            'total_stake': total_stake,
            'total_payout': total_payout,
            'total_ggr': total_ggr,
            'record_count': len(operator_df),
            'anomaly_count': int(operator_df['is_anomaly_combined'].sum()),
            'stake_anomaly_count': int(operator_df['is_anomaly_stake'].sum()),
            'payout_anomaly_count': int(operator_df['is_anomaly_payout'].sum()),
            'time_series': time_series,
            'anomaly_records': anomaly_records,
            'all_records': all_records,
            'date_range': {
                'start': operator_df['date'].min(),
                'end': operator_df['date'].max()
            }
        }
