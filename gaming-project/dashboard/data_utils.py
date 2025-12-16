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


class ExcludedDataHandler:
    """Handler for excluded operators and zero stake data"""
    
    def __init__(self):
        self.excluded_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'excluded_operators_and_zero_stakes.parquet'
        self.summary_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'excluded_operators_summary.parquet'
        self._df = None
        self._summary_df = None
    
    @property
    def df(self):
        """Lazy load excluded data"""
        if self._df is None:
            self._df = pq.read_table(str(self.excluded_file)).to_pandas()
            self._df['date'] = pd.to_datetime(self._df['date'])
        return self._df
    
    @property
    def summary_df(self):
        """Lazy load summary data"""
        if self._summary_df is None:
            self._summary_df = pq.read_table(str(self.summary_file)).to_pandas()
        return self._summary_df
    
    def get_excluded_operators_summary(self):
        """Get summary of all excluded operators with statistics"""
        df = self.summary_df.copy()
        
        # Load main anomaly data to check which operators have non-zero activity
        try:
            anomaly_handler = AnomalyDataHandler()
            main_df = anomaly_handler.df.copy()
            operators_with_activity = set(main_df['operator'].unique())
            # Get record counts from main data for each operator
            main_record_counts = main_df.groupby('operator').size().to_dict()
            # Get unique date counts (not record counts, since dates may overlap)
            main_unique_dates = main_df.groupby('operator')['date'].nunique().to_dict()
        except:
            operators_with_activity = set()
            main_record_counts = {}
            main_unique_dates = {}
        
        # Sort by record count descending
        df = df.sort_values('Record_Count', ascending=False)
        
        # Add rule-based flags
        operators = []
        for _, row in df.iterrows():
            operator_code = row['operator']
            has_main_activity = operator_code in operators_with_activity
            excluded_records = int(row['Record_Count'])
            main_unique_date_count = main_unique_dates.get(operator_code, 0)
            
            operator_data = {
                'operator': operator_code,
                'record_count': int(row['Record_Count']),
                'total_stake': float(row['Total_Stake']),
                'avg_stake': float(row['Avg_Stake']),
                'total_payout': float(row['Total_Payout']),
                'avg_payout': float(row['Avg_Payout']),
                'zero_stake_days': int(row['Zero_Stake_Days']),
                'zero_payout_days': int(row['Zero_Payout_Days']),
                'is_missing_operator': bool(row['Is_Missing_Operator']),
                'has_main_activity': has_main_activity,
                'active_days': main_unique_date_count  # Days with non-zero activity
            }
            
            # Rule-based flagging system
            flags = []
            severity = 'info'
            
            # Rule 1: Missing from anomaly detection (truly missing, no activity anywhere)
            if operator_data['is_missing_operator'] and not has_main_activity:
                flags.append('Not in anomaly detection')
                severity = 'warning'
            
            # Rule 2: All excluded records are zero (but may have activity in main data)
            if operator_data['zero_stake_days'] == operator_data['record_count']:
                if has_main_activity:
                    flags.append('Has non-zero activity')
                    severity = 'info'
                else:
                    flags.append('All days inactive')
                    severity = 'danger'
            
            # Rule 3: Majority zero stakes
            inactive_ratio = operator_data['zero_stake_days'] / operator_data['record_count'] if operator_data['record_count'] > 0 else 0
            if inactive_ratio > 0.8 and inactive_ratio < 1.0:
                flags.append(f'{int(inactive_ratio * 100)}% inactive')
                if severity == 'info':
                    severity = 'warning'
            
            # Rule 4: Zero payouts but has stakes (suspicious)
            if operator_data['total_stake'] > 0 and operator_data['total_payout'] == 0:
                flags.append('Zero payouts with stakes')
                severity = 'danger'
            
            # Rule 5: Insufficient data
            if operator_data['record_count'] < 10:
                flags.append('Insufficient data (<10 days)')
                if severity == 'info':
                    severity = 'warning'
            
            operator_data['flags'] = flags
            operator_data['severity'] = severity
            operator_data['flag_count'] = len(flags)
            
            operators.append(operator_data)
        
        return operators
    
    def get_excluded_operator_detail(self, operator_code):
        """Get detailed records for a specific excluded operator with context from main data"""
        df = self.df.copy()
        
        # Filter for specific operator
        operator_df = df[df['operator'] == operator_code].copy()
        
        if operator_df.empty:
            return None
        
        # Sort by date
        operator_df = operator_df.sort_values('date')
        
        # Get summary stats from summary file
        summary = self.summary_df[self.summary_df['operator'] == operator_code]
        if summary.empty:
            return None
        
        summary_row = summary.iloc[0]
        
        # Always try to join with main anomaly data for context
        combined_df = operator_df.copy()
        activity_context = None
        has_activity = False
        
        try:
            # Load main anomaly data
            anomaly_handler = AnomalyDataHandler()
            main_df = anomaly_handler.df.copy()
            
            # Filter for this operator
            main_operator_df = main_df[main_df['operator'] == operator_code].copy()
            
            if not main_operator_df.empty:
                # Operator exists in main data - has non-zero activity
                has_activity = True
                
                # Calculate GGR for main data
                main_operator_df['ggr'] = main_operator_df['total_stake'] - main_operator_df['total_payout']
                main_operator_df['is_excluded'] = False
                
                # Mark excluded data
                operator_df['is_excluded'] = True
                operator_df['ggr'] = operator_df['total_stake'] - operator_df['total_payout']
                
                # Combine both datasets
                combined_df = pd.concat([
                    main_operator_df[['date', 'total_stake', 'total_payout', 'ggr', 'is_excluded']],
                    operator_df[['date', 'total_stake', 'total_payout', 'ggr', 'is_excluded', 'is_zero_stake', 'is_zero_payout']]
                ]).sort_values('date')
                
                # Fill missing columns
                combined_df['is_zero_stake'] = combined_df.get('is_zero_stake', False)
                combined_df['is_zero_payout'] = combined_df.get('is_zero_payout', False)
                combined_df['is_zero_stake'] = combined_df['is_zero_stake'].fillna(False)
                combined_df['is_zero_payout'] = combined_df['is_zero_payout'].fillna(False)
                
                # Analyze zero periods
                activity_context = self._analyze_zero_periods(combined_df)
            else:
                # Operator only exists in excluded data - no non-zero activity
                has_activity = False
                operator_df['ggr'] = operator_df['total_stake'] - operator_df['total_payout']
                operator_df['is_excluded'] = True
                combined_df = operator_df
        except Exception as e:
            # If join fails, continue with excluded data only
            has_activity = False
            operator_df['ggr'] = operator_df['total_stake'] - operator_df['total_payout']
            operator_df['is_excluded'] = True
            combined_df = operator_df
        
        # Get time series data
        time_series = {
            'dates': combined_df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'stakes': combined_df['total_stake'].tolist(),
            'payouts': combined_df['total_payout'].tolist(),
            'ggr': combined_df['ggr'].tolist(),
            'is_excluded': combined_df['is_excluded'].tolist() if 'is_excluded' in combined_df.columns else [True] * len(combined_df)
        }
        
        # Get daily records - keep ALL records including duplicates on same date
        # Sort by date descending, then by is_excluded (show active first, then excluded)
        combined_df_sorted = combined_df.sort_values(['date', 'is_excluded'], ascending=[False, True])
        
        daily_records = []
        for _, row in combined_df_sorted.head(100).iterrows():
            daily_records.append({
                'date': row['date'],
                'total_stake': float(row['total_stake']),
                'total_payout': float(row['total_payout']),
                'ggr': float(row['ggr']),
                'is_zero_stake': bool(row.get('is_zero_stake', False)),
                'is_zero_payout': bool(row.get('is_zero_payout', False)),
                'is_excluded': bool(row.get('is_excluded', True)),
                'exclusion_reason': row.get('exclusion_reason', 'N/A'),
                'stake_to_payout_ratio': float(row['stake_to_payout_ratio']) if pd.notna(row.get('stake_to_payout_ratio')) else None
            })
        
        # Calculate metrics from combined data - aggregate by date to avoid double counting
        # Group by date and sum stakes/payouts for days that have both excluded and active entries
        daily_totals = combined_df.groupby('date').agg({
            'total_stake': 'sum',
            'total_payout': 'sum'
        }).reset_index()
        
        total_records = len(daily_totals)  # Unique dates
        total_stake = daily_totals['total_stake'].sum()
        total_payout = daily_totals['total_payout'].sum()
        total_ggr = total_stake - total_payout
        zero_stake_days = (daily_totals['total_stake'] == 0).sum()
        zero_payout_days = (daily_totals['total_payout'] == 0).sum()
        avg_stake = daily_totals['total_stake'].mean()
        avg_payout = daily_totals['total_payout'].mean()
        
        # Rule-based analysis using aggregated daily data
        analysis = self._analyze_excluded_operator(operator_df, summary_row, daily_totals)
        
        return {
            'operator': operator_code,
            'total_stake': float(total_stake),
            'total_payout': float(total_payout),
            'total_ggr': float(total_ggr),
            'record_count': int(total_records),
            'zero_stake_days': int(zero_stake_days),
            'zero_payout_days': int(zero_payout_days),
            'is_missing_operator': bool(summary_row['Is_Missing_Operator']),
            'avg_stake': float(avg_stake),
            'avg_payout': float(avg_payout),
            'has_activity': has_activity,
            'time_series': time_series,
            'daily_records': daily_records,
            'date_range': {
                'start': combined_df['date'].min(),
                'end': combined_df['date'].max()
            },
            'analysis': analysis,
            'activity_context': activity_context
        }
    
    def _analyze_zero_periods(self, df):
        """Analyze zero stake periods in context with non-zero data"""
        df = df.sort_values('date')
        
        # Find transitions between zero and non-zero stakes
        df['is_zero'] = df['total_stake'] == 0
        df['prev_is_zero'] = df['is_zero'].shift(1)
        
        transitions = []
        
        # Find when activity started (zero -> non-zero)
        activity_starts = df[(df['prev_is_zero'] == True) & (df['is_zero'] == False)]
        for _, row in activity_starts.iterrows():
            transitions.append({
                'type': 'activity_started',
                'date': row['date'].strftime('%Y-%m-%d'),
                'description': 'Activity resumed'
            })
        
        # Find when activity stopped (non-zero -> zero)
        activity_stops = df[(df['prev_is_zero'] == False) & (df['is_zero'] == True)]
        for _, row in activity_stops.iterrows():
            transitions.append({
                'type': 'activity_stopped',
                'date': row['date'].strftime('%Y-%m-%d'),
                'description': 'Activity went to zero'
            })
        
        # Sort transitions by date
        transitions.sort(key=lambda x: x['date'])
        
        # Calculate statistics
        zero_days = len(df[df['is_zero']])
        total_days = len(df)
        non_zero_days = total_days - zero_days
        
        return {
            'transitions': transitions,
            'zero_days': zero_days,
            'non_zero_days': non_zero_days,
            'total_days': total_days,
            'zero_percentage': (zero_days / total_days * 100) if total_days > 0 else 0
        }
    
    def _analyze_excluded_operator(self, operator_df, summary_row, daily_totals=None):
        """Rule-based analysis of excluded operator"""
        analysis = {
            'flags': [],
            'recommendations': [],
            'severity': 'info',
            'metrics': {}
        }
        
        # Use daily aggregated data for accurate metrics if available, otherwise use excluded data summary
        if daily_totals is not None:
            record_count = len(daily_totals)  # Unique dates
            zero_stake_days = (daily_totals['total_stake'] == 0).sum()
            zero_payout_days = (daily_totals['total_payout'] == 0).sum()
            total_stake = daily_totals['total_stake'].sum()
            total_payout = daily_totals['total_payout'].sum()
        else:
            record_count = int(summary_row['Record_Count'])
            zero_stake_days = int(summary_row['Zero_Stake_Days'])
            zero_payout_days = int(summary_row['Zero_Payout_Days'])
            total_stake = float(summary_row['Total_Stake'])
            total_payout = float(summary_row['Total_Payout'])
        
        is_missing = bool(summary_row['Is_Missing_Operator'])
        
        # Calculate metrics from actual data
        inactive_ratio = zero_stake_days / record_count if record_count > 0 else 0
        zero_payout_ratio = zero_payout_days / record_count if record_count > 0 else 0
        
        analysis['metrics']['inactive_ratio'] = round(inactive_ratio * 100, 1)
        analysis['metrics']['zero_payout_ratio'] = round(zero_payout_ratio * 100, 1)
        analysis['metrics']['active_days'] = record_count - zero_stake_days
        
        # Rule 1: Missing from anomaly detection
        if is_missing:
            analysis['flags'].append({
                'type': 'warning',
                'title': 'Not in Anomaly Detection',
                'description': 'This operator is not included in ML-based anomaly detection models.',
                'reason': 'May lack sufficient historical data or tier classification.'
            })
            analysis['recommendations'].append('Review operator tier assignment and historical data availability.')
            analysis['severity'] = 'warning'
        
        # Rule 2: Completely inactive
        if inactive_ratio == 1.0:
            analysis['flags'].append({
                'type': 'danger',
                'title': 'Completely Inactive',
                'description': f'All {record_count} days have zero stakes.',
                'reason': 'Operator may be dormant, in testing, or experiencing system issues.'
            })
            analysis['recommendations'].append('Verify operator status - consider marking as inactive or removing from monitoring.')
            analysis['severity'] = 'danger'
        
        # Rule 3: Mostly inactive
        elif inactive_ratio > 0.8:
            analysis['flags'].append({
                'type': 'warning',
                'title': f'Mostly Inactive ({analysis["metrics"]["inactive_ratio"]}%)',
                'description': f'{zero_stake_days} of {record_count} days have zero stakes.',
                'reason': 'Sporadic or minimal activity detected.'
            })
            analysis['recommendations'].append('Monitor for consistent activity before including in anomaly detection.')
            if analysis['severity'] == 'info':
                analysis['severity'] = 'warning'
        
        # Rule 4: Zero payouts with stakes (suspicious)
        if total_stake > 0 and total_payout == 0:
            analysis['flags'].append({
                'type': 'danger',
                'title': 'Zero Payouts with Stakes',
                'description': f'Stakes: UGX {total_stake:,.0f}, but zero payouts recorded.',
                'reason': 'Possible data quality issue or all bets lost (highly unlikely).'
            })
            analysis['recommendations'].append('Investigate data quality and payout recording mechanisms.')
            analysis['severity'] = 'danger'
        
        # Rule 5: Insufficient historical data
        if record_count < 10:
            analysis['flags'].append({
                'type': 'info',
                'title': 'Insufficient Historical Data',
                'description': f'Only {record_count} days of data available.',
                'reason': 'Anomaly detection models require at least 10 days of data for reliable predictions.'
            })
            analysis['recommendations'].append('Wait for more data accumulation before including in anomaly detection.')
        
        # Rule 6: All payouts are zero
        if zero_payout_ratio == 1.0:
            analysis['flags'].append({
                'type': 'warning',
                'title': 'All Days Have Zero Payouts',
                'description': f'All {record_count} days have zero payout amounts.',
                'reason': 'May indicate data collection or reporting issues.'
            })
            analysis['recommendations'].append('Check payout data collection and reporting configuration.')
        
        # Rule 7: Recent activity check
        latest_date = operator_df['date'].max()
        days_since_activity = (pd.Timestamp.now() - latest_date).days
        analysis['metrics']['days_since_last_record'] = days_since_activity
        
        if days_since_activity > 30:
            analysis['flags'].append({
                'type': 'info',
                'title': 'No Recent Data',
                'description': f'Last data recorded {days_since_activity} days ago.',
                'reason': 'Operator may have ceased operations or stopped reporting.'
            })
        
        # Default if no flags
        if not analysis['flags']:
            analysis['flags'].append({
                'type': 'success',
                'title': 'Under Review',
                'description': 'Operator is excluded but no critical issues detected.',
                'reason': 'May be pending tier classification or data validation.'
            })
            analysis['recommendations'].append('Monitor for data quality and consistency improvements.')
        
        return analysis
