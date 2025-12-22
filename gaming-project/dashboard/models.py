from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import datetime


class ExcelUpload(models.Model):
    """Track uploaded Excel files for tax variance analysis"""
    FILE_TYPES = [
        ('URA', 'URA Tax Payments'),
        ('LGRB', 'LGRB Submissions'),
    ]
    
    file = models.FileField(upload_to='tax_uploads/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    records_imported = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_type', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.file_type}) - {self.uploaded_at.strftime('%Y-%m-%d')}"


class LGRBSubmission(models.Model):
    """Store LGRB tax submissions from Excel uploads"""
    OPERATOR_CATEGORIES = [
        ('GENERAL BETTING', 'General Betting'),
        ('CASINOS', 'Casinos'),
        ('SPORTS BETTING', 'Sports Betting'),
        ('LOTTERY', 'Lottery'),
        ('OTHER', 'Other'),
    ]
    
    upload = models.ForeignKey(ExcelUpload, on_delete=models.CASCADE, related_name='lgrb_submissions')
    excel_row_number = models.PositiveIntegerField(help_text="Row number in original Excel file")
    
    operator_category = models.CharField(max_length=50, choices=OPERATOR_CATEGORIES)
    operator_name = models.CharField(max_length=255)
    operator_tin = models.CharField(max_length=50, blank=True, null=True)
    submission_date = models.DateField()
    quarter = models.CharField(max_length=10)
    
    total_sales = models.DecimalField(max_digits=15, decimal_places=2)
    total_payouts = models.DecimalField(max_digits=15, decimal_places=2)
    win_loss = models.DecimalField(max_digits=15, decimal_places=2)
    withholding_tax = models.DecimalField(max_digits=15, decimal_places=2)
    gaming_tax = models.DecimalField(max_digits=15, decimal_places=2)
    total_expected_tax = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Standardized operator name for matching
    standardized_operator_name = models.CharField(max_length=255, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['submission_date', 'operator_name']
        indexes = [
            models.Index(fields=['submission_date', 'standardized_operator_name']),
            models.Index(fields=['standardized_operator_name']),
            models.Index(fields=['submission_date']),
        ]
    
    def __str__(self):
        return f"{self.operator_name} ({self.operator_category}) - {self.submission_date}"


class URAPayment(models.Model):
    """Store URA tax payments from Excel uploads"""
    TAX_HEADS = [
        ('Gaming Tax', 'Gaming Tax'),
        ('Withholding Tax', 'Withholding Tax'),
        ('PAYE', 'PAYE'),
    ]
    
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('ELECTRONIC', 'Electronic Transfer'),
        ('OTHER', 'Other'),
    ]
    
    upload = models.ForeignKey(ExcelUpload, on_delete=models.CASCADE, related_name='ura_payments')
    excel_row_number = models.PositiveIntegerField(help_text="Row number in original Excel file")
    
    tin = models.CharField(max_length=50, db_index=True)
    taxpayer_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    prn = models.CharField(max_length=50)
    bank = models.CharField(max_length=100)
    taxpayer_type = models.CharField(max_length=50)
    tax_head = models.CharField(max_length=50, choices=TAX_HEADS)
    location_name = models.CharField(max_length=100)
    bank_realization_date = models.DateField(db_index=True)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    
    # Standardized taxpayer name for matching with LGRB
    standardized_taxpayer_name = models.CharField(max_length=255, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['bank_realization_date', 'taxpayer_name']
        indexes = [
            models.Index(fields=['bank_realization_date', 'standardized_taxpayer_name']),
            models.Index(fields=['standardized_taxpayer_name']),
            models.Index(fields=['tax_head', 'bank_realization_date']),
        ]
    
    def __str__(self):
        return f"{self.taxpayer_name} - {self.tax_head} - {self.bank_realization_date} - {self.amount_paid}"


class WeeklyGamingTaxVariance(models.Model):
    """Store weekly gaming tax variance analysis results"""
    # Wednesday period (previous Wednesday exclusive, current Wednesday inclusive)
    wednesday_date = models.DateField(db_index=True, help_text="Wednesday ending the period")
    period_start = models.DateField(help_text="Previous Wednesday + 1 day")
    period_end = models.DateField(help_text="Current Wednesday")
    
    # Operator information
    operator_name = models.CharField(max_length=255)
    standardized_operator_name = models.CharField(max_length=255, db_index=True)
    
    # LGRB aggregated amounts
    lgrb_gaming_tax = models.DecimalField(max_digits=15, decimal_places=2)
    lgrb_submission_count = models.PositiveIntegerField(help_text="Number of LGRB submissions aggregated")
    
    # URA aggregated amounts
    ura_gaming_tax = models.DecimalField(max_digits=15, decimal_places=2)
    ura_payment_count = models.PositiveIntegerField(help_text="Number of URA payments aggregated")
    
    # Variance calculations
    absolute_variance = models.DecimalField(max_digits=15, decimal_places=2, help_text="URA - LGRB")
    percentage_variance = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="(URA - LGRB) / LGRB * 100")
    
    # Special flags
    is_possible_late_payment = models.BooleanField(default=False, help_text="LGRB = 0 but URA > 0")
    is_early_payment = models.BooleanField(default=False, help_text="URA = 0 but LGRB > 0")
    
    # Analysis metadata
    analysis_date = models.DateTimeField(auto_now_add=True)
    analysis_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-wednesday_date', 'operator_name']
        unique_together = ['wednesday_date', 'standardized_operator_name']
        indexes = [
            models.Index(fields=['wednesday_date', 'standardized_operator_name']),
            models.Index(fields=['is_possible_late_payment']),
            models.Index(fields=['is_early_payment']),
        ]
    
    def __str__(self):
        return f"{self.operator_name} - Week of {self.wednesday_date} - Variance: {self.absolute_variance}"


class MonthlyWHTVariance(models.Model):
    """Store monthly withholding tax variance analysis results"""
    # Calendar month period
    month_year = models.DateField(db_index=True, help_text="First day of the month")
    
    # Operator information
    operator_name = models.CharField(max_length=255)
    standardized_operator_name = models.CharField(max_length=255, db_index=True)
    
    # LGRB aggregated amounts
    lgrb_withholding_tax = models.DecimalField(max_digits=15, decimal_places=2)
    lgrb_submission_count = models.PositiveIntegerField()
    
    # URA aggregated amounts
    ura_withholding_tax = models.DecimalField(max_digits=15, decimal_places=2)
    ura_payment_count = models.PositiveIntegerField()
    
    # Variance calculations
    absolute_variance = models.DecimalField(max_digits=15, decimal_places=2)
    percentage_variance = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    
    # Special flags
    is_possible_late_payment = models.BooleanField(default=False)
    is_early_payment = models.BooleanField(default=False)
    
    # Analysis metadata
    analysis_date = models.DateTimeField(auto_now_add=True)
    analysis_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-month_year', 'operator_name']
        unique_together = ['month_year', 'standardized_operator_name']
        indexes = [
            models.Index(fields=['month_year', 'standardized_operator_name']),
        ]
    
    def __str__(self):
        return f"{self.operator_name} - {self.month_year.strftime('%Y-%m')} - WHT Variance: {self.absolute_variance}"


class AuditLog(models.Model):
    """Audit trail for user actions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=100, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
