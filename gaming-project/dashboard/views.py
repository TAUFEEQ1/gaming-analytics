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
    """Operators list view"""
    # Mock operators data
    # TODO: Replace with actual database queries
    operators = []
    for i in range(1, 51):  # Generate 50 mock operators
        operators.append({
            'code': f'OP-{i:03d}',
            'name': f'Gaming Operator {i}',
            'ggr': round(15.0 + (i * 2.5), 2),
            'stake_anomalies': (i % 5),  # 0-4 anomalies
            'payout_anomalies': (i % 3),  # 0-2 anomalies
        })
    
    # Summary statistics
    total_operators = len(operators)
    total_ggr = sum(op['ggr'] for op in operators)
    operators_with_anomalies = len([op for op in operators if op['stake_anomalies'] > 0 or op['payout_anomalies'] > 0])
    operators_with_stake_anomalies = len([op for op in operators if op['stake_anomalies'] > 0])
    operators_with_payout_anomalies = len([op for op in operators if op['payout_anomalies'] > 0])
    avg_ggr = total_ggr / total_operators if total_operators > 0 else 0
    
    context = {
        'operators': operators,
        'total_operators': total_operators,
        'total_ggr': total_ggr,
        'operators_with_anomalies': operators_with_anomalies,
        'operators_with_stake_anomalies': operators_with_stake_anomalies,
        'operators_with_payout_anomalies': operators_with_payout_anomalies,
        'avg_ggr': avg_ggr,
    }
    
    return render(request, 'dashboard/operators_list.html', context)


@login_required
def performance_detail(request, operator_code):
    """Operator performance detail view"""
    from datetime import datetime, timedelta
    import random
    
    # Mock operator data
    operator = {
        'code': operator_code,
        'name': f'Gaming Operator {operator_code.replace("OP-", "")}',
    }
    
    # Mock metrics
    total_ggr = random.uniform(50000000, 150000000)
    total_stakes = random.uniform(200000000, 500000000)
    total_payouts = total_stakes - total_ggr
    
    # Generate realistic transaction data over 6 months (180 days)
    # Operators have 3-8 transactions per day on average
    days_range = 180
    start_date = datetime.now() - timedelta(days=days_range - 1)
    
    game_types = ['Sports Betting', 'Slots', 'Roulette', 'Card Games', 'Virtual Sports', 'Esports', 'Live Casino', 'Poker']
    transactions = []
    txn_counter = 1
    
    # Generate transactions ensuring at least 1 per day, with realistic volumes
    for day in range(days_range):
        current_date = start_date + timedelta(days=day)
        # More transactions on weekends
        is_weekend = current_date.weekday() >= 5
        daily_transactions = random.randint(5, 12) if is_weekend else random.randint(3, 8)
        
        for _ in range(daily_transactions):
            # More realistic stake amounts
            base_stake = random.uniform(300000, 3000000)
            # Add some high-value transactions occasionally
            if random.random() < 0.05:  # 5% chance of high-value transaction
                base_stake *= random.uniform(2, 5)
            
            # RTP varies by game type
            game_type = random.choice(game_types)
            if game_type == 'Sports Betting':
                rtp = random.uniform(0.92, 0.97)
            elif game_type in ['Slots', 'Virtual Sports']:
                rtp = random.uniform(0.88, 0.95)
            else:
                rtp = random.uniform(0.94, 0.98)
            
            payout = base_stake * rtp
            ggr = base_stake - payout
            
            # More realistic anomaly detection
            # Check for unusually high stakes or suspicious RTP
            stake_flagged = base_stake > 8000000 or random.random() < 0.08
            payout_flagged = rtp > 0.985 or rtp < 0.85 or random.random() < 0.06
            
            transactions.append({
                'id': f'TXN-{txn_counter:05d}',
                'game_type': game_type,
                'stakes': base_stake,
                'payouts': payout,
                'ggr': ggr,
                'date': current_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                'stake_flagged': stake_flagged,
                'payout_flagged': payout_flagged,
                'has_anomaly': stake_flagged or payout_flagged
            })
            txn_counter += 1
    
    # Sort by date descending for table display
    transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Aggregate transactions by date for chart
    from collections import defaultdict
    daily_data = defaultdict(lambda: {'stakes': 0, 'payouts': 0, 'ggr': 0})
    
    for txn in transactions:
        date_key = txn['date'].strftime('%d %b')
        daily_data[date_key]['stakes'] += txn['stakes']
        daily_data[date_key]['payouts'] += txn['payouts']
        daily_data[date_key]['ggr'] += txn['ggr']
    
    # Rebuild chart data from aggregated transactions
    dates = [(start_date + timedelta(days=i)).strftime('%d %b') for i in range(days_range)]
    ggr_data = [round(daily_data[date]['ggr'], 0) for date in dates]
    stakes_data = [round(daily_data[date]['stakes'], 0) for date in dates]
    payouts_data = [round(daily_data[date]['payouts'], 0) for date in dates]
    
    # Calculate date range display
    date_range_display = f"{start_date.strftime('%d %b %Y')} - {datetime.now().strftime('%d %b %Y')}"
    
    # Update totals from actual transaction data
    total_ggr = sum(txn['ggr'] for txn in transactions)
    total_stakes = sum(txn['stakes'] for txn in transactions)
    total_payouts = sum(txn['payouts'] for txn in transactions)
    
    context = {
        'operator': operator,
        'total_ggr': total_ggr,
        'total_stakes': total_stakes,
        'total_payouts': total_payouts,
        'date_range_display': date_range_display,
        'total_transactions': len(transactions),
        'chart_data': {
            'dates': json.dumps(dates),
            'ggr': json.dumps(ggr_data),
            'stakes': json.dumps(stakes_data),
            'payouts': json.dumps(payouts_data),
        },
        'transactions': transactions[:30],  # Show most recent 30 in table
    }
    
    return render(request, 'dashboard/operator_detail.html', context)


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
