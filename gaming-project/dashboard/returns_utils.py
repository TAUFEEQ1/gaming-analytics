"""
Utilities for analyzing operator tax return submissions
"""
import pandas as pd
from pathlib import Path
from django.conf import settings


class ReturnsAnalysisHandler:
    """Handler for analyzing operator tax return submissions from predictions data"""
    
    def __init__(self):
        self.parquet_file = Path(settings.BASE_DIR) / 'dashboard' / 'data' / 'predictions_denormalized_full.parquet'
        self._df = None
    
    @property
    def df(self):
        """Lazy load dataframe"""
        if self._df is None:
            self._df = pd.read_parquet(str(self.parquet_file))
            # Ensure Date column is datetime
            if 'Date' in self._df.columns:
                self._df['Date'] = pd.to_datetime(self._df['Date'])
        return self._df
    
    def get_operators_summary(self, category_filter='all'):
        """
        Get summary of all operators with submission counts and anomalies
        
        Returns anomalies only for Modified_Z_Score <= -2 (submissions that are too low)
        
        Args:
            category_filter: Filter by category ('all' for no filter)
        
        Returns:
            list: List of dicts with operator summaries
        """
        df = self.df.copy()
        
        # Apply category filter if specified
        if category_filter != 'all':
            df = df[df['Category'] == category_filter]
        
        # Group by operator
        operator_summaries = []
        
        for operator in df['Operator_Name'].unique():
            operator_df = df[df['Operator_Name'] == operator]
            
            # Count total submissions
            total_submissions = len(operator_df)
            
            # Count anomalies (Modified_Z_Score <= -2)
            anomalies_count = len(operator_df[operator_df['Modified_Z_Score'] <= -2])
            
            # Get category (use the most frequent category for this operator)
            category = operator_df['Category'].mode()[0] if len(operator_df) > 0 else 'Unknown'
            
            # Calculate total gaming tax
            total_gaming_tax = float(operator_df['Actual_Gaming_Tax'].sum())
            
            # Get average gaming tax
            avg_gaming_tax = float(operator_df['Actual_Gaming_Tax'].mean())
            
            operator_summaries.append({
                'operator_name': operator,
                'category': category,
                'no_of_submissions': total_submissions,
                'anomalies': anomalies_count,
                'total_gaming_tax': total_gaming_tax,
                'avg_gaming_tax': avg_gaming_tax,
                'has_anomalies': anomalies_count > 0,
            })
        
        # Sort by number of anomalies descending, then by operator name
        operator_summaries.sort(key=lambda x: (-x['anomalies'], x['operator_name']))
        
        return operator_summaries
    
    def get_summary_statistics(self, category_filter='all'):
        """
        Get overall summary statistics
        
        Args:
            category_filter: Filter by category ('all' for no filter)
        
        Returns:
            dict: Summary statistics
        """
        df = self.df.copy()
        
        # Apply category filter if specified
        if category_filter != 'all':
            df = df[df['Category'] == category_filter]
        
        total_operators = df['Operator_Name'].nunique()
        total_submissions = len(df)
        total_anomalies = len(df[df['Modified_Z_Score'] <= -2])
        operators_with_anomalies = df[df['Modified_Z_Score'] <= -2]['Operator_Name'].nunique()
        
        # Anomaly percentage
        anomaly_percentage = (total_anomalies / total_submissions * 100) if total_submissions > 0 else 0
        
        # Total gaming tax
        total_gaming_tax = float(df['Actual_Gaming_Tax'].sum())
        
        # Gaming tax from anomalous submissions
        anomalous_tax = float(df[df['Modified_Z_Score'] <= -2]['Actual_Gaming_Tax'].sum())
        
        return {
            'total_operators': total_operators,
            'total_submissions': total_submissions,
            'total_anomalies': total_anomalies,
            'operators_with_anomalies': operators_with_anomalies,
            'anomaly_percentage': anomaly_percentage,
            'total_gaming_tax': total_gaming_tax,
            'anomalous_tax': anomalous_tax,
        }
    
    def get_category_breakdown(self):
        """
        Get breakdown of submissions and anomalies by category
        
        Returns:
            list: List of dicts with category breakdowns
        """
        df = self.df.copy()
        
        category_data = []
        
        for category in df['Category'].unique():
            category_df = df[df['Category'] == category]
            
            total_submissions = len(category_df)
            anomalies_count = len(category_df[category_df['Modified_Z_Score'] <= -2])
            operators_count = category_df['Operator_Name'].nunique()
            
            category_data.append({
                'category': category,
                'operators_count': operators_count,
                'total_submissions': total_submissions,
                'anomalies': anomalies_count,
                'anomaly_percentage': (anomalies_count / total_submissions * 100) if total_submissions > 0 else 0,
            })
        
        # Sort by category name
        category_data.sort(key=lambda x: x['category'])
        
        return category_data
    
    def get_operator_detail(self, operator_name):
        """
        Get detailed data for a specific operator
        
        Args:
            operator_name: Name of the operator
        
        Returns:
            dict: Operator detail data including time series and submissions
        """
        df = self.df.copy()
        
        # Filter for this operator
        operator_df = df[df['Operator_Name'] == operator_name]
        
        if len(operator_df) == 0:
            return None
        
        # Sort by date
        operator_df = operator_df.sort_values('Date')
        
        # Get operator info
        category = operator_df['Category'].iloc[0]
        
        # Calculate summary statistics
        total_submissions = len(operator_df)
        total_anomalies = len(operator_df[operator_df['Modified_Z_Score'] <= -2])
        
        total_actual_tax = float(operator_df['Actual_Gaming_Tax'].sum())
        total_predicted_tax = float(operator_df['Predicted_Gaming_Tax'].sum())
        total_sales = float(operator_df['Avg_Total_Sales'].sum())
        total_payouts = float(operator_df['Avg_Total_Payout'].sum())
        
        avg_actual_tax = float(operator_df['Actual_Gaming_Tax'].mean())
        avg_predicted_tax = float(operator_df['Predicted_Gaming_Tax'].mean())
        avg_sales = float(operator_df['Avg_Total_Sales'].mean())
        avg_payouts = float(operator_df['Avg_Total_Payout'].mean())
        
        # Date range
        date_range = {
            'start': operator_df['Date'].min(),
            'end': operator_df['Date'].max()
        }
        
        # Prepare time series data for charts
        time_series = {
            'dates': operator_df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'actual_tax': operator_df['Actual_Gaming_Tax'].tolist(),
            'predicted_tax': operator_df['Predicted_Gaming_Tax'].tolist(),
            'sales': operator_df['Avg_Total_Sales'].tolist(),
            'payouts': operator_df['Avg_Total_Payout'].tolist(),
        }
        
        # Get all submission records
        submissions = []
        for _, row in operator_df.iterrows():
            is_anomaly = row['Modified_Z_Score'] <= -2
            
            submissions.append({
                'date': row['Date'],
                'month_year': row['Month_Year'],
                'actual_tax': float(row['Actual_Gaming_Tax']),
                'predicted_tax': float(row['Predicted_Gaming_Tax']),
                'residuals': float(row['Denormalized_Residuals']),
                'abs_residuals': float(row['Abs_Denormalized_Residuals']),
                'modified_z_score': float(row['Modified_Z_Score']),
                'sales': float(row['Avg_Total_Sales']),
                'payouts': float(row.get('Avg_Total_Payout', 0)),
                'is_anomaly': is_anomaly,
                'model_type': row.get('Model_Type', 'Unknown'),
            })
        
        # Get anomaly records only
        anomaly_records = [s for s in submissions if s['is_anomaly']]
        # Sort anomalies by date descending
        anomaly_records.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'operator_name': operator_name,
            'category': category,
            'total_submissions': total_submissions,
            'total_anomalies': total_anomalies,
            'anomaly_percentage': (total_anomalies / total_submissions * 100) if total_submissions > 0 else 0,
            'total_actual_tax': total_actual_tax,
            'total_predicted_tax': total_predicted_tax,
            'total_sales': total_sales,
            'total_payouts': total_payouts,
            'avg_actual_tax': avg_actual_tax,
            'avg_predicted_tax': avg_predicted_tax,
            'avg_sales': avg_sales,
            'avg_payouts': avg_payouts,
            'date_range': date_range,
            'time_series': time_series,
            'submissions': submissions,
            'anomaly_records': anomaly_records,
        }
