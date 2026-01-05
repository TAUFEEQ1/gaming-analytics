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


@login_required
def deviation_analysis(request):
    """NLGRB vs URA Tax Deviation Analysis"""
    from .deviation_analysis_utils import DeviationAnalysisHandler
    
    # Initialize handler
    deviation_handler = DeviationAnalysisHandler()
    
    # Get time filter from query params (default: 'all')
    months_filter = request.GET.get('months', 'all')
    
    # Get operators summary (with optional time filter)
    operators_summary = deviation_handler.get_operators_summary(months_filter=months_filter)
    
    # Get overall summary statistics (with optional time filter)
    summary_stats = deviation_handler.get_summary_statistics(months_filter=months_filter)
    
    # Define time filter options
    time_filter_options = [
        ('3', 'Last 3 Months'),
        ('6', 'Last 6 Months'),
        ('12', 'Last 12 Months'),
        ('all', 'All Time'),
    ]
    
    context = {
        'operators': operators_summary,
        'summary_stats': summary_stats,
        'time_filter_options': time_filter_options,
        'selected_months': months_filter,
    }
    
    return render(request, 'dashboard/deviation_analysis.html', context)


@login_required
def deviation_detail(request, operator_name):
    """NLGRB vs URA Tax Deviation Detail View"""
    from .deviation_analysis_utils import DeviationAnalysisHandler
    from django.http import Http404
    
    # Initialize handler
    deviation_handler = DeviationAnalysisHandler()
    
    # Get time filter from query params
    months_filter = request.GET.get('months', 'all')
    
    # Get operator details
    operator_data = deviation_handler.get_operator_detail(operator_name, months_filter=months_filter)
    
    if not operator_data:
        raise Http404(f"Operator '{operator_name}' not found")
    
    # Format date range display
    date_range_display = f"{operator_data['date_range']['start'].strftime('%b %Y')} - {operator_data['date_range']['end'].strftime('%b %Y')}"
    
    # Prepare chart data - format dates for display
    chart_dates = [datetime.strptime(d, '%Y-%m-%d').strftime('%b %Y') for d in operator_data['time_series']['dates']]
    
    # Define time filter options
    time_filter_options = [
        ('3', 'Last 3 Months'),
        ('6', 'Last 6 Months'),
        ('12', 'Last 12 Months'),
        ('all', 'All Time'),
    ]
    
    context = {
        'operator': {
            'name': operator_data['operator_name'],
        },
        'months_count': operator_data['months_count'],
        'anomalies_count': operator_data['anomalies_count'],
        'anomaly_percentage': operator_data['anomaly_percentage'],
        'total_nlgrb': operator_data['total_nlgrb'],
        'total_ura': operator_data['total_ura'],
        'total_deviation': operator_data['total_deviation'],
        'total_abs_deviation': operator_data['total_abs_deviation'],
        'percentage_variance': operator_data['percentage_variance'],
        'avg_nlgrb': operator_data['avg_nlgrb'],
        'avg_ura': operator_data['avg_ura'],
        'avg_deviation': operator_data['avg_deviation'],
        'date_range_display': date_range_display,
        'chart_data': {
            'dates': json.dumps(chart_dates),
            'nlgrb': json.dumps(operator_data['time_series']['nlgrb']),
            'ura': json.dumps(operator_data['time_series']['ura']),
            'deviations': json.dumps(operator_data['time_series']['deviations']),
            'abs_deviations': json.dumps(operator_data['time_series']['abs_deviations']),
            'is_anomaly': json.dumps(operator_data['time_series']['is_anomaly']),
            'yoy_nlgrb': json.dumps(operator_data['time_series']['yoy_nlgrb']),
            'yoy_ura': json.dumps(operator_data['time_series']['yoy_ura']),
        },
        'monthly_records': operator_data['monthly_records'],
        'anomaly_records': operator_data['anomaly_records'][:10],  # Show most recent 10
        'time_filter_options': time_filter_options,
        'selected_months': months_filter,
    }
    
    return render(request, 'dashboard/deviation_detail.html', context)

