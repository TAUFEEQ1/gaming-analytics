from django.utils import timezone
from django.db import models
from decimal import Decimal
import pandas as pd
import re
import datetime
from difflib import SequenceMatcher
from .models import ExcelUpload, LGRBSubmission, URAPayment, WeeklyGamingTaxVariance, MonthlyWHTVariance


class OperatorNameStandardizer:
    """Standardize operator names for matching between LGRB and URA"""
    
    def __init__(self):
        self.common_variations = {
            # Keep specific test operator names distinct
            'TEST1': ['TEST1', 'TEST 1'],
            'TEST11': ['TEST11', 'TEST 11'],
            'TEST16': ['TEST16', 'TEST 16'],
            'TEST24': ['TEST24', 'TEST 24'],
            'TEST27': ['TEST27', 'TEST 27'],
            'TEST37': ['TEST37', 'TEST 37'],
            # Generic categories
            'BETTING': ['BETTING', 'BET', 'SPORTS', 'SPORT', 'GENERAL BETTING'],
            'CASINO': ['CASINO', 'CASINOS', 'GAMING'],
            'SLOT': ['SLOT', 'SLOTS', 'SLOT MACHINES', 'SLOT MACHINE'],
            'BINGO': ['BINGO', 'BINGO GAMES'],
            'LIMITED': ['LIMITED', 'LTD', 'LTD.', 'L.T.D'],
            'COMPANY': ['COMPANY', 'CO', 'CO.', 'CORP'],
            'UGANDA': ['UGANDA', 'UG', 'UGANDAN'],
        }
    
    def standardize_name(self, raw_name: str) -> str:
        """Standardize operator name for consistent matching"""
        if not raw_name:
            return ""
        
        # Convert to uppercase and remove special characters
        cleaned = re.sub(r'[^A-Za-z0-9\s]', '', raw_name).upper().strip()
        
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Apply common variations mapping
        words = cleaned.split()
        standardized_words = []
        
        # First check if the entire cleaned name matches any variation
        for standard, variations in self.common_variations.items():
            if cleaned in variations:
                return standard
        
        # If no full match, process word by word
        for word in words:
            # Find if word matches any variation group
            standardized = word
            for standard, variations in self.common_variations.items():
                if word in variations:
                    standardized = standard
                    break
            standardized_words.append(standardized)
        
        return ' '.join(standardized_words)
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two operator names"""
        std_name1 = self.standardize_name(name1)
        std_name2 = self.standardize_name(name2)
        return SequenceMatcher(None, std_name1, std_name2).ratio()
    
    def find_best_match(self, target_name: str, candidate_names: list, threshold: float = 0.8) -> tuple:
        """Find best matching operator name from candidates"""
        target_std = self.standardize_name(target_name)
        best_match = None
        best_score = 0
        
        for candidate in candidate_names:
            score = self.calculate_similarity(target_name, candidate)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        return best_match, best_score


class ExcelProcessor:
    """Process Excel files for URA and LGRB data"""
    
    def __init__(self):
        self.standardizer = OperatorNameStandardizer()
    
    def validate_excel_structure(self, file_path: str, expected_file_type: str) -> dict:
        """Validate Excel file structure and columns"""
        try:
            # Read Excel file (first sheet only)
            df = pd.read_excel(file_path, sheet_name=0)
            
            if expected_file_type == 'URA':
                required_columns = ['TIN', 'TAXPAYER NAME', 'TAX HEAD', 'BANK REALIZATION DATE', 'AMOUNT PAID']
            elif expected_file_type == 'LGRB':
                required_columns = ['Operator Name', 'Gaming Tax', 'Withholding Tax', 'Date']
            else:
                return {'valid': False, 'error': 'Unknown file type'}            
            # Check for required columns (case-insensitive)
            df_columns_upper = [col.upper().strip() for col in df.columns]
            required_columns_upper = [col.upper() for col in required_columns]
            
            missing_columns = []
            for req_col in required_columns_upper:
                if req_col not in df_columns_upper:
                    missing_columns.append(req_col)
            
            if missing_columns:
                return {
                    'valid': False, 
                    'error': f'Missing required columns: {missing_columns}',
                    'found_columns': list(df.columns)
                }
            
            return {
                'valid': True, 
                'record_count': len(df),
                'columns': list(df.columns)
            }
            
        except Exception as e:
            return {'valid': False, 'error': f'Excel processing error: {str(e)}'}
    
    def process_ura_excel(self, upload: ExcelUpload) -> dict:
        """Process URA Excel file and import records"""
        try:
            df = pd.read_excel(upload.file.path, sheet_name=0)
            
            # Standardize column names
            column_mapping = {}
            for col in df.columns:
                col_upper = col.upper().strip()
                if 'TIN' in col_upper:
                    column_mapping[col] = 'TIN'
                elif 'TAXPAYER NAME' in col_upper or 'TAXPAYER_NAME' in col_upper:
                    column_mapping[col] = 'TAXPAYER_NAME'
                elif 'TAX HEAD' in col_upper or 'TAX_HEAD' in col_upper:
                    column_mapping[col] = 'TAX_HEAD'
                elif 'BANK REALIZATION DATE' in col_upper or 'REALIZATION_DATE' in col_upper:
                    column_mapping[col] = 'BANK_REALIZATION_DATE'
                elif 'AMOUNT PAID' in col_upper or 'AMOUNT_PAID' in col_upper:
                    column_mapping[col] = 'AMOUNT_PAID'
                elif 'DEPARTMENT' in col_upper:
                    column_mapping[col] = 'DEPARTMENT'
                elif 'PRN' in col_upper:
                    column_mapping[col] = 'PRN'
                elif 'BANK' in col_upper and 'REALIZATION' not in col_upper:
                    column_mapping[col] = 'BANK'
                elif 'TAXPAYER TYPE' in col_upper or 'TAXPAYER_TYPE' in col_upper:
                    column_mapping[col] = 'TAXPAYER_TYPE'
                elif 'LOCATION' in col_upper:
                    column_mapping[col] = 'LOCATION_NAME'
                elif 'PMT MODE' in col_upper or 'PAYMENT_MODE' in col_upper:
                    column_mapping[col] = 'PMT_MODE'
            
            df = df.rename(columns=column_mapping)
            
            # Filter for Gaming Tax and Withholding Tax only
            valid_tax_heads = ['Gaming Tax', 'Withholding Tax']
            df = df[df['TAX_HEAD'].isin(valid_tax_heads)]
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Parse date
                    bank_date = pd.to_datetime(row['BANK_REALIZATION_DATE']).date()
                    
                    # Parse amount (remove commas and convert)
                    amount_str = str(row['AMOUNT_PAID']).replace(',', '').replace(' ', '')
                    amount = Decimal(amount_str)
                    
                    # Create URA payment record
                    URAPayment.objects.create(
                        upload=upload,
                        excel_row_number=index + 2,  # +2 for header row and 0-based index
                        tin=str(row['TIN']),
                        taxpayer_name=str(row['TAXPAYER_NAME']),
                        department=str(row.get('DEPARTMENT', '')),
                        prn=str(row.get('PRN', '')),
                        bank=str(row.get('BANK', '')),
                        taxpayer_type=str(row.get('TAXPAYER_TYPE', '')),
                        tax_head=row['TAX_HEAD'],
                        location_name=str(row.get('LOCATION_NAME', '')),
                        bank_realization_date=bank_date,
                        amount_paid=amount,
                        payment_mode=str(row.get('PMT_MODE', 'OTHER')),
                        standardized_taxpayer_name=self.standardizer.standardize_name(row['TAXPAYER_NAME'])
                    )
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def process_lgrb_excel(self, upload: ExcelUpload) -> dict:
        """Process LGRB Excel file and import records"""
        try:
            df = pd.read_excel(upload.file.path, sheet_name=0)
            
            # Standardize column names
            column_mapping = {}
            for col in df.columns:
                col_upper = col.upper().strip()
                if 'OPERATOR CATEGORY' in col_upper:
                    column_mapping[col] = 'OPERATOR_CATEGORY'
                elif 'OPERATOR NAME' in col_upper:
                    column_mapping[col] = 'OPERATOR_NAME'
                elif 'TIN' in col_upper and 'OPERATOR' not in col_upper:
                    column_mapping[col] = 'TIN'
                elif 'DATE' in col_upper:
                    column_mapping[col] = 'DATE'
                elif 'QUARTERS' in col_upper or 'QUARTER' in col_upper:
                    column_mapping[col] = 'QUARTERS'
                elif 'TOTAL SALES' in col_upper or 'TOTAL_SALES' in col_upper:
                    column_mapping[col] = 'TOTAL_SALES'
                elif 'TOTAL PAYOUTS' in col_upper or 'TOTAL_PAYOUTS' in col_upper:
                    column_mapping[col] = 'TOTAL_PAYOUTS'
                elif 'WIN/LOSS' in col_upper or 'WIN_LOSS' in col_upper:
                    column_mapping[col] = 'WIN_LOSS'
                elif 'WITHHOLDING TAX' in col_upper or 'WITHHOLDING_TAX' in col_upper:
                    column_mapping[col] = 'WITHHOLDING_TAX'
                elif 'GAMING TAX' in col_upper or 'GAMING_TAX' in col_upper:
                    column_mapping[col] = 'GAMING_TAX'
                elif 'TOTAL EXPECTED TAX' in col_upper or 'TOTAL_EXPECTED_TAX' in col_upper:
                    column_mapping[col] = 'TOTAL_EXPECTED_TAX'
            
            df = df.rename(columns=column_mapping)
            
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Parse date
                    submission_date = pd.to_datetime(row['DATE']).date()
                    
                    # Parse amounts (remove commas and convert)
                    total_sales = Decimal(str(row['TOTAL_SALES']).replace(',', '').replace(' ', ''))
                    total_payouts = Decimal(str(row['TOTAL_PAYOUTS']).replace(',', '').replace(' ', ''))
                    win_loss = Decimal(str(row['WIN_LOSS']).replace(',', '').replace(' ', ''))
                    withholding_tax = Decimal(str(row['WITHHOLDING_TAX']).replace(',', '').replace(' ', '').replace('-', '0'))
                    gaming_tax = Decimal(str(row['GAMING_TAX']).replace(',', '').replace(' ', ''))
                    total_expected_tax = Decimal(str(row['TOTAL_EXPECTED_TAX']).replace(',', '').replace(' ', ''))
                    
                    # Create LGRB submission record
                    LGRBSubmission.objects.create(
                        upload=upload,
                        excel_row_number=index + 2,
                        operator_category=row['OPERATOR_CATEGORY'],
                        operator_name=str(row['OPERATOR_NAME']),
                        operator_tin=str(row.get('TIN', '')),
                        submission_date=submission_date,
                        quarter=str(row['QUARTERS']),
                        total_sales=total_sales,
                        total_payouts=total_payouts,
                        win_loss=win_loss,
                        withholding_tax=withholding_tax,
                        gaming_tax=gaming_tax,
                        total_expected_tax=total_expected_tax,
                        standardized_operator_name=self.standardizer.standardize_name(row['OPERATOR_NAME'])
                    )
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return {
                'success': True,
                'imported_count': imported_count,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TaxVarianceCalculator:
    """Calculate tax variance between LGRB and URA data"""
    
    def __init__(self):
        self.standardizer = OperatorNameStandardizer()
    
    def get_wednesday_periods(self, start_date: datetime.date, end_date: datetime.date) -> list:
        """Generate Wednesday periods between start and end dates"""
        periods = []
        current = start_date
        
        # Find first Wednesday on or after start_date
        days_until_wednesday = (2 - current.weekday()) % 7  # 2 = Wednesday
        first_wednesday = current + datetime.timedelta(days=days_until_wednesday)
        
        wednesday = first_wednesday
        while wednesday <= end_date:
            # Period is previous Wednesday + 1 day to current Wednesday
            period_start = wednesday - datetime.timedelta(days=6)  # Previous Wednesday + 1
            period_end = wednesday
            
            # Extend the last Wednesday of each month to include end-of-month LGRB submissions
            # Check if this is the last Wednesday of the month by seeing if next Wednesday is in different month
            next_wednesday = wednesday + datetime.timedelta(days=7)
            if next_wednesday.month != wednesday.month:
                # This is the last Wednesday of the month, extend to month end
                from calendar import monthrange
                last_day = monthrange(wednesday.year, wednesday.month)[1]
                month_end = wednesday.replace(day=last_day)
                if month_end > period_end:
                    period_end = month_end
            
            periods.append({
                'wednesday': wednesday,
                'start': period_start,
                'end': period_end
            })
            wednesday += datetime.timedelta(days=7)
        
        return periods
    
    def calculate_gaming_tax_variance(self, start_date: datetime.date, end_date: datetime.date) -> dict:
        """Calculate weekly gaming tax variance for date range"""
        periods = self.get_wednesday_periods(start_date, end_date)
        results = []
        
        for period in periods:
            # Get LGRB submissions for this Wednesday period
            # LGRB submissions are typically end-of-month, so we map them to the appropriate Wednesday period
            lgrb_data = LGRBSubmission.objects.filter(
                submission_date__gte=period['start'],
                submission_date__lte=period['end']
            ).values('standardized_operator_name').annotate(
                total_gaming_tax=models.Sum('gaming_tax'),  # Sum across all categories for each operator
                submission_count=models.Count('id')
            )
            
            # Get URA payments for this period (exclusive start, inclusive end)
            ura_data = URAPayment.objects.filter(
                tax_head='Gaming Tax',
                bank_realization_date__gt=period['start'],
                bank_realization_date__lte=period['end']
            ).values('standardized_taxpayer_name').annotate(
                total_gaming_tax=models.Sum('amount_paid'),
                payment_count=models.Count('id')
            )
            
            # Convert to dictionaries for easier lookup
            lgrb_dict = {item['standardized_operator_name']: item for item in lgrb_data}
            ura_dict = {item['standardized_taxpayer_name']: item for item in ura_data}
            
            # Get all unique operators
            all_operators = set(lgrb_dict.keys()) | set(ura_dict.keys())
            
            for operator in all_operators:
                lgrb_amount = lgrb_dict.get(operator, {}).get('total_gaming_tax', Decimal('0'))
                ura_amount = ura_dict.get(operator, {}).get('total_gaming_tax', Decimal('0'))
                
                variance = ura_amount - lgrb_amount
                percentage_variance = None
                
                # Calculate percentage variance
                if lgrb_amount != 0:
                    percentage_variance = (variance / lgrb_amount) * 100
                
                # Determine special flags
                is_late_payment = (lgrb_amount == 0 and ura_amount > 0)
                is_early_payment = (ura_amount == 0 and lgrb_amount > 0)
                
                # Create or update variance record
                variance_record, created = WeeklyGamingTaxVariance.objects.update_or_create(
                    wednesday_date=period['wednesday'],
                    standardized_operator_name=operator,
                    defaults={
                        'period_start': period['start'],
                        'period_end': period['end'],
                        'operator_name': operator,  # Will be improved with reverse lookup
                        'lgrb_gaming_tax': lgrb_amount,
                        'lgrb_submission_count': lgrb_dict.get(operator, {}).get('submission_count', 0),
                        'ura_gaming_tax': ura_amount,
                        'ura_payment_count': ura_dict.get(operator, {}).get('payment_count', 0),
                        'absolute_variance': variance,
                        'percentage_variance': percentage_variance,
                        'is_possible_late_payment': is_late_payment,
                        'is_early_payment': is_early_payment,
                    }
                )
                
                results.append(variance_record)
        
        return {
            'success': True,
            'periods_analyzed': len(periods),
            'variance_records': len(results)
        }

    def calculate_monthly_wht_variance(self, start_date: datetime.date, end_date: datetime.date) -> dict:
        """Calculate monthly withholding tax variance for date range"""
        # Generate monthly periods between start and end dates
        months = []
        current = start_date.replace(day=1)  # Start of month
        
        while current <= end_date:
            # Get last day of current month
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1)
            else:
                next_month = current.replace(month=current.month + 1)
            
            month_end = next_month - datetime.timedelta(days=1)
            
            months.append({
                'year': current.year,
                'month': current.month,
                'start': current,
                'end': min(month_end, end_date)
            })
            
            current = next_month
            if current > end_date:
                break
        
        results = []
        
        for period in months:
            # Get LGRB withholding tax submissions for this month
            lgrb_data = LGRBSubmission.objects.filter(
                submission_date__year=period['year'],
                submission_date__month=period['month']
            ).values('standardized_operator_name').annotate(
                total_withholding_tax=models.Sum('withholding_tax'),
                submission_count=models.Count('id')
            )
            
            # Get URA withholding tax payments for this month
            ura_data = URAPayment.objects.filter(
                tax_head='Withholding Tax',
                bank_realization_date__year=period['year'],
                bank_realization_date__month=period['month']
            ).values('standardized_taxpayer_name').annotate(
                total_withholding_tax=models.Sum('amount_paid'),
                payment_count=models.Count('id')
            )
            
            # Convert to dictionaries for easier lookup
            lgrb_dict = {item['standardized_operator_name']: item for item in lgrb_data}
            ura_dict = {item['standardized_taxpayer_name']: item for item in ura_data}
            
            # Get all unique operators
            all_operators = set(lgrb_dict.keys()) | set(ura_dict.keys())
            
            for operator in all_operators:
                lgrb_amount = lgrb_dict.get(operator, {}).get('total_withholding_tax', Decimal('0'))
                ura_amount = ura_dict.get(operator, {}).get('total_withholding_tax', Decimal('0'))
                
                variance = ura_amount - lgrb_amount
                percentage_variance = None
                
                # Calculate percentage variance
                if lgrb_amount != 0:
                    percentage_variance = (variance / lgrb_amount) * 100
                
                # Determine special flags
                is_late_payment = (lgrb_amount == 0 and ura_amount > 0)
                is_early_payment = (ura_amount == 0 and lgrb_amount > 0)
                
                # Create or update variance record
                variance_record, created = MonthlyWHTVariance.objects.update_or_create(
                    month_year=period['start'],
                    standardized_operator_name=operator,
                    defaults={
                        'operator_name': operator,  # Will be improved with reverse lookup
                        'lgrb_withholding_tax': lgrb_amount,
                        'lgrb_submission_count': lgrb_dict.get(operator, {}).get('submission_count', 0),
                        'ura_withholding_tax': ura_amount,
                        'ura_payment_count': ura_dict.get(operator, {}).get('payment_count', 0),
                        'absolute_variance': variance,
                        'percentage_variance': percentage_variance,
                        'is_possible_late_payment': is_late_payment,
                        'is_early_payment': is_early_payment,
                    }
                )
                
                results.append(variance_record)
        
        return {
            'success': True,
            'months_analyzed': len(months),
            'variance_records': len(results)
        }