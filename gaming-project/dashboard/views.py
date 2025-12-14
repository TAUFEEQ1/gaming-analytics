from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json


def home(request):
    """Home page view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Main dashboard view"""
    
    # Get filter period from query params (default: week)
    filter_type = request.GET.get('filter', 'week')
    
    # Determine filter period display text
    filter_period_map = {
        'today': 'Today',
        'week': 'This Week',
        'month': 'This Month',
        'custom': 'Custom'
    }
    filter_period = filter_period_map.get(filter_type, 'This Week')
    
    # Mock data for dashboard statistics
    # TODO: Replace with actual database queries
    context = {
        'filter_period': filter_period,
        'total_ggr': 650_500_000,  # 650.5 million
        'total_stake': 2_450_000_000,  # 2.45 billion
        'total_payouts': 1_950_000_000,  # 1.95 billion
        'total_operators': 104,
        'total_bets': 125_000,  # 125 thousand bets
        'total_anomalies': 8,
        
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
    avg_ggr = total_ggr / total_operators if total_operators > 0 else 0
    
    context = {
        'operators': operators,
        'total_operators': total_operators,
        'total_ggr': total_ggr,
        'operators_with_anomalies': operators_with_anomalies,
        'avg_ggr': avg_ggr,
    }
    
    return render(request, 'dashboard/operators_list.html', context)


@login_required
def performance_detail(request, operator_code):
    """Operator performance detail view"""
    # TODO: Fetch actual operator data from database
    context = {
        'operator_code': operator_code,
        'operator_name': f'Operator {operator_code}',
        # Add more operator details here
    }
    return render(request, 'dashboard/performance_detail.html', context)
