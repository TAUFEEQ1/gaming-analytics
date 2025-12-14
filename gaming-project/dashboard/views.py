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
    
    # Initialize data handler
    data_handler = GGRDataHandler()
    
    # Get filter period from query params (default: all)
    filter_type = request.GET.get('filter', 'all')
    
    # Determine filter period display text
    filter_period_map = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'all': 'All Time',
        'custom': 'Custom'
    }
    filter_period = filter_period_map.get(filter_type, 'All Time')
    
    # Get date range based on filter
    start_date, end_date = data_handler.get_filter_dates(filter_type)
    
    # Get KPIs from real data
    kpis = data_handler.get_kpis(start_date, end_date)
    
    # Get time series data for chart
    time_series = data_handler.get_time_series_data(start_date, end_date)
    
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
        
        # Chart data as HTML (using Plotly or similar)
        'sector_ggr_line_chart': generate_sector_ggr_chart(),
        'top_operators_bar_chart': generate_top_operators_chart(),
        'bottom_operators_pie_chart': generate_bottom_operators_chart(),
    }
    
    # Game type statistics with pagination
    all_game_types = [
        {
            'type': 'Sports',
            'avg_ggr': 45.20,
            'avg_rtp': 94.50,
            'rtp_std_dev': 2.1543
        },
        {
            'type': 'Esports',
            'avg_ggr': 32.15,
            'avg_rtp': 93.80,
            'rtp_std_dev': 2.4521
        },
        {
            'type': 'Card Games',
            'avg_ggr': 38.75,
            'avg_rtp': 96.20,
            'rtp_std_dev': 1.8921
        },
        {
            'type': 'General Betting',
            'avg_ggr': 28.90,
            'avg_rtp': 95.10,
            'rtp_std_dev': 2.0143
        },
        {
            'type': 'Virtual Sports',
            'avg_ggr': 25.60,
            'avg_rtp': 92.30,
            'rtp_std_dev': 3.1287
        },
        {
            'type': 'Roulette',
            'avg_ggr': 41.50,
            'avg_rtp': 97.30,
            'rtp_std_dev': 1.5432
        },
        {
            'type': 'Slots',
            'avg_ggr': 52.30,
            'avg_rtp': 92.80,
            'rtp_std_dev': 3.2145
        },
    ]
    
    # Paginate game types (4 per page)
    game_page_number = request.GET.get('game_page', 1)
    game_paginator = Paginator(all_game_types, 4)  # Show 4 game types per page
    game_types_page = game_paginator.get_page(game_page_number)
    context['game_type_stats'] = game_types_page
    
    return render(request, 'dashboard/dashboard.html', context)


def generate_sector_ggr_chart():
    """Generate sector GGR trend chart HTML"""
    # TODO: Replace with actual Plotly or Chart.js implementation
    return '''
    <div class="chart-container" style="position: relative; height: 300px;">
        <canvas id="sectorGGRChart"></canvas>
    </div>
    <script>
        const ctx = document.getElementById('sectorGGRChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                datasets: [{
                    label: 'Expected',
                    data: [450, 480, 500, 520],
                    borderColor: 'rgba(44, 62, 80, 1)',
                    backgroundColor: 'rgba(44, 62, 80, 0.1)',
                    tension: 0.3
                }, {
                    label: 'Actual',
                    data: [425, 465, 495, 485],
                    borderColor: 'rgba(26, 188, 156, 1)',
                    backgroundColor: 'rgba(26, 188, 156, 0.1)',
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + 'M';
                            }
                        }
                    }
                }
            }
        });
    </script>
    '''


def generate_top_operators_chart():
    """Generate top operators radial bar chart HTML"""
    return '''
    <div id="topOperatorsChart"></div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof ApexCharts !== 'undefined') {
                var options = {
                    series: [88, 76, 69, 65, 60],
                    chart: {
                        height: 300,
                        type: 'radialBar',
                    },
                    plotOptions: {
                        radialBar: {
                            dataLabels: {
                                name: {
                                    fontSize: '14px',
                                    fontWeight: 600,
                                },
                                value: {
                                    fontSize: '12px',
                                    formatter: function(val) {
                                        return val.toFixed(0) + '%';
                                    }
                                },
                                total: {
                                    show: true,
                                    label: 'Average',
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    formatter: function (w) {
                                        return '71%';
                                    }
                                }
                            },
                            hollow: {
                                size: '50%',
                            }
                        }
                    },
                    labels: ['OP-003 (52.3M)', 'OP-001 (45.2M)', 'OP-006 (41.2M)', 'OP-002 (38.8M)', 'OP-005 (35.6M)'],
                    colors: ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c'],
                    legend: {
                        show: true,
                        position: 'bottom',
                        fontSize: '11px',
                        labels: {
                            colors: '#6c757d'
                        },
                        markers: {
                            width: 10,
                            height: 10
                        }
                    }
                };

                var chart = new ApexCharts(document.querySelector("#topOperatorsChart"), options);
                chart.render();
            }
        });
    </script>
    '''


def generate_bottom_operators_chart():
    """Generate bottom operators pie chart HTML"""
    return '''
    <div class="chart-container" style="position: relative; height: 300px; width: 100%;">
        <canvas id="bottomOperatorsChart"></canvas>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const ctx3 = document.getElementById('bottomOperatorsChart');
            if (ctx3) {
                new Chart(ctx3.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['OP-008', 'OP-007', 'OP-004', 'OP-005', 'OP-002'],
                        datasets: [{
                            label: 'GGR (Millions)',
                            data: [19.80, 22.45, 28.90, 35.60, 38.75],
                            backgroundColor: [
                                'rgba(231, 76, 60, 0.8)',
                                'rgba(230, 126, 34, 0.8)',
                                'rgba(241, 196, 15, 0.8)',
                                'rgba(52, 152, 219, 0.8)',
                                'rgba(46, 204, 113, 0.8)'
                            ],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    boxWidth: 12,
                                    padding: 10,
                                    font: {
                                        size: 11
                                    }
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return context.label + ': ' + context.parsed + 'M';
                                    }
                                }
                            }
                        }
                    }
                });
            }
        });
    </script>
    '''


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
