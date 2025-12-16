from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
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
        'transactions': operator_data['all_records'][:100],  # Show most recent 100 in table
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
    import random
    from datetime import datetime, timedelta
    
    # Get operator filter from query params
    operator_filter = request.GET.get('operator', 'all')
    
    # Mock operators list
    operators = [
        {'code': f'OP{str(i).zfill(3)}', 'name': f'Operator {i}'} 
        for i in range(1, 51)
    ]
    
    # Generate mock anomalous transactions
    game_types = ['Sports Betting', 'Slots', 'Roulette', 'Card Games', 
                  'Virtual Sports', 'Esports', 'Live Casino', 'Poker']
    
    anomalies = []
    anomaly_id = 1
    
    # Generate 150 anomalous transactions across operators
    for _ in range(150):
        operator = random.choice(operators)
        
        # Skip if filtering by specific operator
        if operator_filter != 'all' and operator['code'] != operator_filter:
            continue
            
        game_type = random.choice(game_types)
        
        # Generate anomalous transaction
        is_stake_anomaly = random.choice([True, False])
        
        if is_stake_anomaly:
            # High stake anomaly
            stakes = random.randint(8_000_000, 25_000_000)
            rtp = random.uniform(0.88, 0.97)
            payouts = round(stakes * rtp)
        else:
            # High payout / RTP anomaly
            stakes = random.randint(1_000_000, 5_000_000)
            rtp = random.uniform(0.985, 1.05)  # Unusually high RTP
            payouts = round(stakes * rtp)
        
        ggr = stakes - payouts
        
        # Generate random date within last 30 days
        days_ago = random.randint(0, 30)
        anomaly_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        anomalies.append({
            'id': anomaly_id,
            'operator_code': operator['code'],
            'operator_name': operator['name'],
            'game_type': game_type,
            'stakes': stakes,
            'payouts': payouts,
            'ggr': ggr,
            'rtp': rtp * 100,
            'date': anomaly_date,
            'anomaly_type': 'High Stake' if is_stake_anomaly else 'High Payout',
            'stake_flagged': is_stake_anomaly,
            'payout_flagged': not is_stake_anomaly,
        })
        anomaly_id += 1
    
    # Sort by date descending
    anomalies.sort(key=lambda x: x['date'], reverse=True)
    
    # Calculate summary statistics
    total_anomalies = len(anomalies)
    stake_anomalies = len([a for a in anomalies if a['stake_flagged']])
    payout_anomalies = len([a for a in anomalies if a['payout_flagged']])
    total_flagged_stakes = sum(a['stakes'] for a in anomalies if a['stake_flagged'])
    total_flagged_payouts = sum(a['payouts'] for a in anomalies if a['payout_flagged'])
    avg_stake_anomaly = total_flagged_stakes / stake_anomalies if stake_anomalies > 0 else 0
    avg_payout_anomaly = total_flagged_payouts / payout_anomalies if payout_anomalies > 0 else 0
    
    context = {
        'anomalies': anomalies[:50],  # Show first 50
        'operators': operators,
        'selected_operator': operator_filter,
        'total_anomalies': total_anomalies,
        'stake_anomalies': stake_anomalies,
        'payout_anomalies': payout_anomalies,
        'avg_stake_anomaly': avg_stake_anomaly,
        'avg_payout_anomaly': avg_payout_anomaly,
    }
    
    return render(request, 'dashboard/anomalies_list.html', context)
