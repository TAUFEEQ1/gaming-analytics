from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
import json
from decimal import Decimal
from .data_utils import GGRDataHandler
from .models import ExcelUpload, LGRBSubmission, URAPayment, WeeklyGamingTaxVariance, MonthlyWHTVariance, AuditLog
from .tax_utils import ExcelProcessor, TaxVarianceCalculator


def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Main dashboard view with real parquet data"""
    from .operator_performance_utils import OperatorPerformanceHandler
    
    # Initialize data handlers
    data_handler = GGRDataHandler()
    perf_handler = OperatorPerformanceHandler()
    
    # Get filter period from query params (default: all)
    filter_type = request.GET.get('filter', 'all')
    
    # Determine filter period display text
    filter_period_map = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'q1': 'Q1',
        'q2': 'Q2',
        'q3': 'Q3',
        'q4': 'Q4',
        'all': 'All Time',
        'custom': 'Custom'
    }
    filter_period = filter_period_map.get(filter_type, 'All Time')
    
    # Get date range based on filter
    if filter_type == 'custom':
        # Get custom dates from query params
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            filter_period = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        else:
            # Fallback to default if custom dates not provided
            start_date, end_date = data_handler.get_filter_dates('all')
    else:
        start_date, end_date = data_handler.get_filter_dates(filter_type)
    
    # Get KPIs from real data
    kpis = data_handler.get_kpis(start_date, end_date)
    
    # Get time series data for chart
    time_series = data_handler.get_time_series_data(start_date, end_date)
    
    # Get anomalies details
    anomalies_details = data_handler.get_anomalies_details(start_date, end_date)
    
    # Get operator performance data
    top_performers = perf_handler.get_top_performers(n=5, start_date=start_date, end_date=end_date)
    bottom_performers = perf_handler.get_bottom_performers(n=5, start_date=start_date, end_date=end_date)
    
    context = {
        'filter_period': filter_period,
        'total_ggr': kpis['total_ggr'],
        'total_stake': kpis['total_stake'],
        'total_payouts': kpis['total_payout'],
        'total_operators': kpis['total_operators'],
        'total_bets': kpis['total_bets'],
        'total_anomalies': kpis['total_anomalies'],
        
        # Time series chart data (actual vs expected GGR)
        'chart_data': json.dumps(time_series),
        
        # Anomalies details for modal
        'anomalies_details': anomalies_details,
        
        # Operator performance data
        'top_performers': top_performers.to_dict('records'),
        'bottom_performers': bottom_performers.to_dict('records'),
        
    }
    
    # Get game category statistics from operator performance data
    category_distribution = perf_handler.get_category_distribution(start_date, end_date)
    
    # Convert to list of dicts and format for template
    game_categories = []
    for _, row in category_distribution.iterrows():
        game_categories.append({
            'category': row['game_category'].replace('RRI_', '').replace('_', ' ').title(),
            'total_ggr': row['total_ggr'],
            'operator_count': int(row['operator_count']),
            'market_share': row['market_share']
        })
    
    context['game_categories'] = game_categories
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'dashboard/profile.html')


@login_required
def operators_list(request):
    """Operators list view with real anomaly data"""
    from .data_utils import AnomalyDataHandler
    
    # Initialize data handler
    anomaly_handler = AnomalyDataHandler()
    
    # Get filter period from query params (default: all)
    filter_type = request.GET.get('filter', 'all')
    
    # Get date range based on filter
    if filter_type == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            start_date, end_date = anomaly_handler.get_filter_dates('all')
    else:
        start_date, end_date = anomaly_handler.get_filter_dates(filter_type)
    
    # Get operators summary
    operators = anomaly_handler.get_operators_summary(start_date, end_date)
    
    # Summary statistics
    total_operators = len(operators)
    total_ggr = sum(op['ggr'] for op in operators)
    operators_with_anomalies = len([op for op in operators if op['total_anomalies'] > 0])
    operators_with_stake_anomalies = len([op for op in operators if op['stake_anomalies'] > 0])
    operators_with_payout_anomalies = len([op for op in operators if op['payout_anomalies'] > 0])
    avg_ggr = total_ggr / total_operators if total_operators > 0 else 0
    
    # Convert GGR to millions for display
    for op in operators:
        op['ggr_millions'] = op['ggr'] / 1_000_000
    
    # Determine filter period display text
    filter_period_map = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'q1': 'Q1',
        'q2': 'Q2',
        'q3': 'Q3',
        'q4': 'Q4',
        'all': 'All Time',
        'custom': 'Custom'
    }
    filter_period = filter_period_map.get(filter_type, 'All Time')
    
    if filter_type == 'custom' and start_date and end_date:
        filter_period = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
    
    context = {
        'operators': operators,
        'total_operators': total_operators,
        'total_ggr': total_ggr,
        'operators_with_anomalies': operators_with_anomalies,
        'operators_with_stake_anomalies': operators_with_stake_anomalies,
        'operators_with_payout_anomalies': operators_with_payout_anomalies,
        'avg_ggr': avg_ggr,
        'filter_period': filter_period,
        'current_filter': filter_type,
    }
    
    return render(request, 'dashboard/operators_list.html', context)


@login_required
def performance_detail(request, operator_code):
    """Operator performance detail view with real anomaly data"""
    from .data_utils import AnomalyDataHandler
    
    # Initialize data handler
    anomaly_handler = AnomalyDataHandler()
    
    # Get filter period from query params (default: all)
    filter_type = request.GET.get('filter', 'all')
    
    # Get date range based on filter
    if filter_type == 'custom':
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            start_date, end_date = anomaly_handler.get_filter_dates('all')
    else:
        start_date, end_date = anomaly_handler.get_filter_dates(filter_type)
    
    # Get operator details
    operator_data = anomaly_handler.get_operator_detail(operator_code, start_date, end_date)
    
    if not operator_data:
        # Operator not found
        from django.http import Http404
        raise Http404(f"Operator '{operator_code}' not found")
    
    # Format date range display
    date_range_display = f"{operator_data['date_range']['start'].strftime('%d %b %Y')} - {operator_data['date_range']['end'].strftime('%d %b %Y')}"
    
    # Prepare chart data
    chart_dates = [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b') for d in operator_data['time_series']['dates']]
    
    # Determine filter period display text
    filter_period_map = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'q1': 'Q1',
        'q2': 'Q2',
        'q3': 'Q3',
        'q4': 'Q4',
        'all': 'All Time',
        'custom': 'Custom'
    }
    filter_period = filter_period_map.get(filter_type, 'All Time')
    
    if filter_type == 'custom' and start_date and end_date:
        filter_period = f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
    
    context = {
        'operator': {
            'code': operator_data['operator'],
            'name': operator_data['operator'],
            'tier': operator_data['operator_tier']
        },
        'total_ggr': operator_data['total_ggr'],
        'total_stakes': operator_data['total_stake'],
        'total_payouts': operator_data['total_payout'],
        'date_range_display': date_range_display,
        'total_transactions': operator_data['record_count'],
        'total_anomalies': operator_data['anomaly_count'],
        'stake_anomalies': operator_data['stake_anomaly_count'],
        'payout_anomalies': operator_data['payout_anomaly_count'],
        'chart_data': {
            'dates': json.dumps(chart_dates),
            'ggr': json.dumps(operator_data['time_series']['ggr']),
            'stakes': json.dumps(operator_data['time_series']['stakes']),
            'payouts': json.dumps(operator_data['time_series']['payouts']),
        },
        'transactions': operator_data['all_records'],  # Show all records in table (DataTables will handle pagination)
        'anomaly_records': operator_data['anomaly_records'][:20],  # Show most recent 20 anomalies in sidebar
        'filter_period': filter_period,
        'current_filter': filter_type,
    }
    
    return render(request, 'dashboard/operator_detail.html', context)


@login_required
def excluded_operators_list(request):
    """Excluded operators list view with rule-based flagging"""
    from .data_utils import ExcludedDataHandler
    
    # Initialize handler
    excluded_handler = ExcludedDataHandler()
    
    # Get excluded operators summary with flags
    operators = excluded_handler.get_excluded_operators_summary()
    
    # Summary statistics
    total_excluded = len(operators)
    missing_operators = len([op for op in operators if op['is_missing_operator']])
    fully_inactive = len([op for op in operators if op['zero_stake_days'] == op['record_count']])
    
    # Count by severity
    danger_count = len([op for op in operators if op['severity'] == 'danger'])
    warning_count = len([op for op in operators if op['severity'] == 'warning'])
    info_count = len([op for op in operators if op['severity'] == 'info'])
    
    context = {
        'operators': operators,
        'total_excluded': total_excluded,
        'missing_operators': missing_operators,
        'fully_inactive': fully_inactive,
        'danger_count': danger_count,
        'warning_count': warning_count,
        'info_count': info_count,
    }
    
    return render(request, 'dashboard/excluded_operators_list.html', context)


@login_required
def excluded_operator_detail(request, operator_code):
    """Excluded operator detail view with rule-based analysis"""
    from .data_utils import ExcludedDataHandler
    
    # Initialize handler
    excluded_handler = ExcludedDataHandler()
    
    # Get operator details
    operator_data = excluded_handler.get_excluded_operator_detail(operator_code)
    
    if not operator_data:
        # Operator not found
        from django.http import Http404
        raise Http404(f"Excluded operator '{operator_code}' not found")
    
    # Format date range display
    date_range_display = f"{operator_data['date_range']['start'].strftime('%d %b %Y')} - {operator_data['date_range']['end'].strftime('%d %b %Y')}"
    
    # Prepare chart data
    chart_dates = operator_data['time_series']['dates']  # Keep as ISO format for ApexCharts
    
    context = {
        'operator': {
            'code': operator_data['operator'],
            'name': operator_data['operator'],
        },
        'total_ggr': operator_data['total_ggr'],
        'total_stakes': operator_data['total_stake'],
        'total_payouts': operator_data['total_payout'],
        'record_count': operator_data['record_count'],
        'zero_stake_days': operator_data['zero_stake_days'],
        'zero_payout_days': operator_data['zero_payout_days'],
        'is_missing_operator': operator_data['is_missing_operator'],
        'avg_stake': operator_data['avg_stake'],
        'avg_payout': operator_data['avg_payout'],
        'date_range_display': date_range_display,
        'has_activity': operator_data.get('has_activity', False),
        'activity_context': operator_data.get('activity_context'),
        'chart_data': {
            'dates': json.dumps(chart_dates),
            'ggr': json.dumps(operator_data['time_series']['ggr']),
            'stakes': json.dumps(operator_data['time_series']['stakes']),
            'payouts': json.dumps(operator_data['time_series']['payouts']),
            'is_excluded': json.dumps(operator_data['time_series'].get('is_excluded', [True] * len(chart_dates)))
        },
        'daily_records': operator_data['daily_records'][:100],  # Show most recent 100
        'analysis': operator_data['analysis'],
    }
    
    return render(request, 'dashboard/excluded_operator_detail.html', context)


@login_required
def anomalies_list(request):
    """Anomalies list view with filtering by operator"""
    from .data_utils import AnomalyDataHandler
    
    # Get operator filter from query params
    operator_filter = request.GET.get('operator', 'all')
    
    # Load real anomaly data
    handler = AnomalyDataHandler()
    anomalies_df = handler.anomalies_df.copy()
    
    # Get unique operators from the data
    unique_operators = sorted(anomalies_df['operator'].unique())
    operators = [
        {'code': op, 'name': op}
        for op in unique_operators
    ]
    
    # Filter by operator if specified
    if operator_filter != 'all':
        anomalies_df = anomalies_df[anomalies_df['operator'] == operator_filter]
    
    # Convert to list of dicts for template
    anomalies = []
    for _, row in anomalies_df.iterrows():
        stakes = float(row.get('total_stake', 0))
        payouts = float(row.get('total_payout', 0))
        ggr = stakes - payouts
        rtp = (payouts / stakes * 100) if stakes > 0 else 0
        
        # Determine anomaly flags based on thresholds
        stake_flagged = bool(row.get('is_anomaly_stake', 0))
        payout_flagged = bool(row.get('is_anomaly_payout', 0))
        
        # Get game type from available fields (prefer dominant_game_category)
        game_type = row.get('dominant_game_category', row.get('dominant_game_type', row.get('game_type', 'Unknown')))
        # Clean up game type display (remove RRI_ prefix if present)
        if isinstance(game_type, str) and game_type.startswith('RRI_'):
            game_type = game_type.replace('RRI_', '').replace('_', ' ').title()
        
        anomalies.append({
            'operator_code': row.get('operator', ''),
            'operator_name': row.get('operator', ''),
            'operator_tier': row.get('operator_tier', 'N/A'),
            'game_type': game_type,
            'stakes': stakes,
            'payouts': payouts,
            'ggr': ggr,
            'rtp': rtp,
            'date': row.get('date'),
            'stake_flagged': stake_flagged,
            'payout_flagged': payout_flagged,
            'anomaly_type': row.get('anomaly_type', 'Unknown'),
            # Stake details
            'stake_predicted': float(row.get('stake_predicted', 0)),
            'stake_deviation': float(row.get('stake_deviation', 0)),
            'stake_deviation_pct': float(row.get('stake_deviation_pct', 0)),
            'anomaly_score_stake': float(row.get('anomaly_score_stake', 0)),
            # Payout details
            'payout_predicted': float(row.get('payout_predicted', 0)),
            'payout_deviation': float(row.get('payout_deviation', 0)),
            'payout_deviation_pct': float(row.get('payout_deviation_pct', 0)),
            'anomaly_score_payout': float(row.get('anomaly_score_payout', 0)),
            # Game details
            'dominant_stake_category': row.get('dominant_stake_category', ''),
            'dominant_payout_category': row.get('dominant_payout_category', ''),
            'top_games': row.get('top_games', ''),
        })
    
    # Sort by date descending
    anomalies.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate summary statistics
    total_anomalies = len(anomalies)
    stake_anomalies = len([a for a in anomalies if a['stake_flagged']])
    payout_anomalies = len([a for a in anomalies if a['payout_flagged']])
    
    # Calculate stake average (filter out negative stakes which are data errors)
    positive_stake_anomalies = [a for a in anomalies if a['stake_flagged'] and a['stakes'] > 0]
    total_flagged_stakes = sum(a['stakes'] for a in positive_stake_anomalies)
    avg_stake_anomaly = total_flagged_stakes / len(positive_stake_anomalies) if positive_stake_anomalies else 0
    
    # Calculate payout average (filter out negative payouts which represent refunds/chargebacks)
    positive_payout_anomalies = [a for a in anomalies if a['payout_flagged'] and a['payouts'] > 0]
    total_flagged_payouts = sum(a['payouts'] for a in positive_payout_anomalies)
    avg_payout_anomaly = total_flagged_payouts / len(positive_payout_anomalies) if positive_payout_anomalies else 0
    
    context = {
        'anomalies': anomalies,
        'operators': operators,
        'selected_operator': operator_filter,
        'total_anomalies': total_anomalies,
        'stake_anomalies': stake_anomalies,
        'payout_anomalies': payout_anomalies,
        'avg_stake_anomaly': avg_stake_anomaly,
        'avg_payout_anomaly': avg_payout_anomaly,
    }
    
    return render(request, 'dashboard/anomalies_list.html', context)


# Tax Variance Analysis Views

@login_required
def tax_variance_upload(request):
    """Upload Excel files for tax variance analysis"""
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        file_type = request.POST.get('file_type')
        
        # Validate file type
        if not uploaded_file.name.lower().endswith('.xlsx'):
            messages.error(request, 'Only Excel (.xlsx) files are allowed.')
            return redirect('tax_variance_upload')
        
        # Validate file type selection
        if file_type not in ['URA', 'LGRB']:
            messages.error(request, 'Please select a valid file type.')
            return redirect('tax_variance_upload')
        
        # Validate Excel structure before saving
        processor = ExcelProcessor()
        
        # Save file temporarily to validate
        temp_upload = ExcelUpload(
            file=uploaded_file,
            original_filename=uploaded_file.name,
            file_type=file_type,
            uploaded_by=request.user,
            file_size=uploaded_file.size
        )
        temp_upload.save()
        
        validation_result = processor.validate_excel_structure(temp_upload.file.path, file_type)
        
        if not validation_result['valid']:
            # Delete the invalid file
            temp_upload.delete()
            messages.error(request, f"Excel validation failed: {validation_result['error']}")
            return redirect('tax_variance_upload')
        
        # File is valid, process it
        if file_type == 'URA':
            result = processor.process_ura_excel(temp_upload)
        else:
            result = processor.process_lgrb_excel(temp_upload)
        
        if result['success']:
            # Mark as processed
            temp_upload.processed = True
            temp_upload.processed_at = timezone.now()
            temp_upload.records_imported = result['imported_count']
            temp_upload.save()
            
            # Log audit trail
            AuditLog.objects.create(
                user=request.user,
                action='file_upload',
                resource_type='excel_upload',
                resource_id=str(temp_upload.id),
                ip_address=request.META.get('REMOTE_ADDR'),
                details={
                    'filename': uploaded_file.name,
                    'file_type': file_type,
                    'file_size': uploaded_file.size,
                    'records_imported': result['imported_count']
                }
            )
            
            messages.success(
                request,
                f'File "{uploaded_file.name}" uploaded successfully! '
                f'{result["imported_count"]} records imported.'
            )
            
            if result.get('errors'):
                messages.warning(
                    request,
                    f'{len(result["errors"])} rows had errors and were skipped.'
                )
        else:
            # Processing failed, delete file
            temp_upload.delete()
            messages.error(request, f'File processing failed: {result["error"]}')
        
        return redirect('tax_variance_dashboard')
    
    # Get recent uploads for display
    recent_uploads = ExcelUpload.objects.filter(
        uploaded_by=request.user
    ).order_by('-uploaded_at')[:10]
    
    context = {
        'recent_uploads': recent_uploads
    }
    
    return render(request, 'dashboard/tax_variance_upload.html', context)


@login_required
def tax_variance_dashboard(request):
    """Main tax variance dashboard"""
    # Get filter parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    operator_filter = request.GET.get('operator', 'all')
    
    # Default date range (last 4 weeks)
    if not start_date_str or not end_date_str:
        end_date = date.today()
        start_date = end_date - timedelta(weeks=4)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # Get Gaming Tax variance data (weekly)
    gaming_variance_query = WeeklyGamingTaxVariance.objects.filter(
        wednesday_date__gte=start_date,
        wednesday_date__lte=end_date
    ).order_by('-wednesday_date', 'operator_name')
    
    if operator_filter != 'all':
        gaming_variance_query = gaming_variance_query.filter(
            standardized_operator_name__icontains=operator_filter
        )
    
    gaming_variance_data = list(gaming_variance_query)
    
    # Get WHT variance data (monthly)
    wht_variance_query = MonthlyWHTVariance.objects.filter(
        month_year__gte=start_date.replace(day=1),
        month_year__lte=end_date
    ).order_by('-month_year', 'operator_name')
    
    if operator_filter != 'all':
        wht_variance_query = wht_variance_query.filter(
            standardized_operator_name__icontains=operator_filter
        )
    
    wht_variance_data = list(wht_variance_query)
    
    # Calculate Gaming Tax summary statistics
    total_gaming_variances = len(gaming_variance_data)
    late_payments = len([v for v in gaming_variance_data if v.is_possible_late_payment])
    early_payments = len([v for v in gaming_variance_data if v.is_early_payment])
    significant_gaming_variances = len([v for v in gaming_variance_data if v.percentage_variance and abs(v.percentage_variance) > 10])
    
    # Gaming Tax totals
    total_lgrb_gaming = sum(v.lgrb_gaming_tax for v in gaming_variance_data)
    total_ura_gaming = sum(v.ura_gaming_tax for v in gaming_variance_data)
    total_gaming_variance = total_ura_gaming - total_lgrb_gaming
    
    # Calculate WHT summary statistics
    total_wht_variances = len(wht_variance_data)
    significant_wht_variances = len([v for v in wht_variance_data if v.percentage_variance and abs(v.percentage_variance) > 10])
    
    # WHT totals
    total_lgrb_wht = sum(v.lgrb_withholding_tax for v in wht_variance_data)
    total_ura_wht = sum(v.ura_withholding_tax for v in wht_variance_data)
    total_wht_variance = total_ura_wht - total_lgrb_wht
    
    # Get unique operators for filter dropdown (from both tax types)
    gaming_operators = WeeklyGamingTaxVariance.objects.values_list(
        'standardized_operator_name', 'operator_name'
    ).distinct()
    
    wht_operators = MonthlyWHTVariance.objects.values_list(
        'standardized_operator_name', 'operator_name'
    ).distinct()
    
    # Combine and deduplicate operators
    all_operators = list(set(list(gaming_operators) + list(wht_operators)))
    all_operators.sort(key=lambda x: x[1])  # Sort by operator name
    
    # Get recent uploads summary
    recent_ura_uploads = ExcelUpload.objects.filter(
        file_type='URA', 
        processed=True
    ).order_by('-uploaded_at')[:3]
    
    recent_lgrb_uploads = ExcelUpload.objects.filter(
        file_type='LGRB', 
        processed=True
    ).order_by('-uploaded_at')[:3]
    
    context = {
        'gaming_variance_data': gaming_variance_data,
        'wht_variance_data': wht_variance_data,
        'start_date': start_date,
        'end_date': end_date,
        'operator_filter': operator_filter,
        'operators': all_operators,
        'gaming_summary': {
            'total_variances': total_gaming_variances,
            'late_payments': late_payments,
            'early_payments': early_payments,
            'significant_variances': significant_gaming_variances,
            'total_lgrb': total_lgrb_gaming,
            'total_ura': total_ura_gaming,
            'total_variance': total_gaming_variance,
        },
        'wht_summary': {
            'total_variances': total_wht_variances,
            'significant_variances': significant_wht_variances,
            'total_lgrb': total_lgrb_wht,
            'total_ura': total_ura_wht,
            'total_variance': total_wht_variance,
        },
        'recent_ura_uploads': recent_ura_uploads,
        'recent_lgrb_uploads': recent_lgrb_uploads,
    }
    
    return render(request, 'dashboard/tax_variance_dashboard.html', context)


@login_required
def calculate_tax_variance(request):
    """Calculate tax variance for specified date range"""
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        
        if not start_date_str or not end_date_str:
            messages.error(request, 'Please provide both start and end dates.')
            return redirect('tax_variance_dashboard')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            calculator = TaxVarianceCalculator()
            
            # Calculate Gaming Tax variance (weekly)
            gaming_result = calculator.calculate_gaming_tax_variance(start_date, end_date)
            
            # Calculate Withholding Tax variance (monthly) 
            wht_result = calculator.calculate_monthly_wht_variance(start_date, end_date)
            
            if gaming_result['success'] and wht_result['success']:
                # Log audit trail
                AuditLog.objects.create(
                    user=request.user,
                    action='calculate_variance',
                    resource_type='tax_variance',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={
                        'start_date': start_date_str,
                        'end_date': end_date_str,
                        'gaming_periods_analyzed': gaming_result['periods_analyzed'],
                        'gaming_variance_records': gaming_result['variance_records'],
                        'wht_periods_analyzed': wht_result['periods_analyzed'],
                        'wht_variance_records': wht_result['variance_records']
                    }
                )
                
                messages.success(
                    request,
                    f'Tax variance calculated successfully! '
                    f'Gaming Tax: {gaming_result["periods_analyzed"]} weeks analyzed, '
                    f'{gaming_result["variance_records"]} records created. '
                    f'WHT: {wht_result["periods_analyzed"]} months analyzed, '
                    f'{wht_result["variance_records"]} records created.'
                )
            else:
                error_msg = []
                if not gaming_result['success']:
                    error_msg.append('Gaming Tax variance calculation failed')
                if not wht_result['success']:
                    error_msg.append('WHT variance calculation failed')
                messages.error(request, '. '.join(error_msg) + '.')
        
        except ValueError as e:
            messages.error(request, f'Invalid date format: {e}')
        except Exception as e:
            messages.error(request, f'Error calculating variance: {e}')
    
    return redirect('tax_variance_dashboard')


@login_required
def operator_tax_detail(request, operator_name):
    """Detailed tax analysis for specific operator"""
    # Get variance data for operator
    variance_data = WeeklyGamingTaxVariance.objects.filter(
        standardized_operator_name=operator_name
    ).order_by('-wednesday_date')
    
    if not variance_data:
        messages.error(request, f'No tax data found for operator: {operator_name}')
        return redirect('tax_variance_dashboard')
    
    # Get LGRB submissions for this operator
    lgrb_data = LGRBSubmission.objects.filter(
        standardized_operator_name=operator_name
    ).order_by('-submission_date')
    
    # Get URA payments for this operator
    ura_data = URAPayment.objects.filter(
        standardized_taxpayer_name=operator_name,
        tax_head='Gaming Tax'
    ).order_by('-bank_realization_date')
    
    # Calculate operator summary
    operator_summary = {
        'total_variance_records': variance_data.count(),
        'late_payment_flags': variance_data.filter(is_possible_late_payment=True).count(),
        'early_payment_flags': variance_data.filter(is_early_payment=True).count(),
        'total_lgrb_amount': sum(v.lgrb_gaming_tax for v in variance_data),
        'total_ura_amount': sum(v.ura_gaming_tax for v in variance_data),
        'lgrb_submission_count': lgrb_data.count(),
        'ura_payment_count': ura_data.count(),
    }
    
    operator_summary['total_variance'] = (
        operator_summary['total_ura_amount'] - operator_summary['total_lgrb_amount']
    )
    
    context = {
        'operator_name': operator_name,
        'variance_data': variance_data[:50],  # Show recent 50 records
        'lgrb_data': lgrb_data[:20],  # Show recent 20 submissions
        'ura_data': ura_data[:20],  # Show recent 20 payments
        'operator_summary': operator_summary,
    }
    
    return render(request, 'dashboard/operator_tax_detail.html', context)

@login_required
def return_variance(request):
    """Operator Tax Return Submissions Analysis"""
    from .returns_utils import ReturnsAnalysisHandler
    
    # Initialize handler
    returns_handler = ReturnsAnalysisHandler()
    
    # Get category filter from query params
    category_filter = request.GET.get('category', 'all')
    
    # Get operators summary (with optional category filter)
    operators_summary = returns_handler.get_operators_summary(category_filter=category_filter)
    
    # Get overall summary statistics (with optional category filter)
    summary_stats = returns_handler.get_summary_statistics(category_filter=category_filter)
    
    # Get category breakdown (always show all categories)
    category_breakdown = returns_handler.get_category_breakdown()
    
    # Get list of all unique categories for filter dropdown
    all_categories = [cat['category'] for cat in category_breakdown]
    
    context = {
        'operators': operators_summary,
        'summary_stats': summary_stats,
        'category_breakdown': category_breakdown,
        'all_categories': all_categories,
        'selected_category': category_filter,
    }
    
    return render(request, 'dashboard/return_variance.html', context)

@login_required
def return_variance_detail(request, operator_name):
    """Operator Return Variance Detail View"""
    from .returns_utils import ReturnsAnalysisHandler
    
    # Initialize handler
    returns_handler = ReturnsAnalysisHandler()
    
    # Get operator details
    operator_data = returns_handler.get_operator_detail(operator_name)
    
    if not operator_data:
        from django.http import Http404
        raise Http404(f"Operator '{operator_name}' not found")
    
    # Format date range display
    date_range_display = f"{operator_data['date_range']['start'].strftime('%d %b %Y')} - {operator_data['date_range']['end'].strftime('%d %b %Y')}"
    
    # Prepare chart data
    chart_dates = [datetime.strptime(d, '%Y-%m-%d').strftime('%d %b %Y') for d in operator_data['time_series']['dates']]
    
    context = {
        'operator': {
            'name': operator_data['operator_name'],
            'category': operator_data['category'],
        },
        'total_submissions': operator_data['total_submissions'],
        'total_anomalies': operator_data['total_anomalies'],
        'anomaly_percentage': operator_data['anomaly_percentage'],
        'total_actual_tax': operator_data['total_actual_tax'],
        'total_predicted_tax': operator_data['total_predicted_tax'],
        'total_sales': operator_data['total_sales'],
        'total_payouts': operator_data['total_payouts'],
        'avg_actual_tax': operator_data['avg_actual_tax'],
        'avg_predicted_tax': operator_data['avg_predicted_tax'],
        'avg_sales': operator_data['avg_sales'],
        'avg_payouts': operator_data['avg_payouts'],
        'date_range_display': date_range_display,
        'chart_data': {
            'dates': json.dumps(chart_dates),
            'actual_tax': json.dumps(operator_data['time_series']['actual_tax']),
            'predicted_tax': json.dumps(operator_data['time_series']['predicted_tax']),
            'sales': json.dumps(operator_data['time_series']['sales']),
            'payouts': json.dumps(operator_data['time_series']['payouts']),
        },
        'submissions': operator_data['submissions'],
        'anomaly_records': operator_data['anomaly_records'][:20],  # Show most recent 20
    }
    
    return render(request, 'dashboard/return_variance_detail.html', context) 