from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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
        'total_ggr': 650.50,  # in millions
        'active_anomalies_count': 8,
        'tax_collected': 130.10,  # in millions
        'total_stake': 2.45,  # in billions
        'total_payouts': 1.95,  # in billions
        'total_operators': 104,
        
        # Game type statistics
        'game_type_stats': [
            {
                'type': 'Sports Betting',
                'avg_ggr': 45.20,
                'avg_rtp': 94.50,
                'rtp_std_dev': 2.1543
            },
            {
                'type': 'Casino Games',
                'avg_ggr': 38.75,
                'avg_rtp': 96.20,
                'rtp_std_dev': 1.8921
            },
            {
                'type': 'Slot Machines',
                'avg_ggr': 52.30,
                'avg_rtp': 92.80,
                'rtp_std_dev': 3.2145
            },
            {
                'type': 'Live Dealer',
                'avg_ggr': 28.90,
                'avg_rtp': 97.10,
                'rtp_std_dev': 1.3287
            },
        ],
        
        # Operators for triage table
        'operators_for_triage': [
            {'code': 'OP-001', 'ggr': 45.20, 'active_anomalies': 3},
            {'code': 'OP-002', 'ggr': 38.75, 'active_anomalies': 0},
            {'code': 'OP-003', 'ggr': 52.30, 'active_anomalies': 2},
            {'code': 'OP-004', 'ggr': 28.90, 'active_anomalies': 1},
            {'code': 'OP-005', 'ggr': 35.60, 'active_anomalies': 0},
            {'code': 'OP-006', 'ggr': 41.20, 'active_anomalies': 2},
            {'code': 'OP-007', 'ggr': 22.45, 'active_anomalies': 0},
            {'code': 'OP-008', 'ggr': 19.80, 'active_anomalies': 0},
        ],
        
        # Chart data as HTML (using Plotly or similar)
        'sector_ggr_line_chart': generate_sector_ggr_chart(),
        'top_operators_bar_chart': generate_top_operators_chart(),
        'bottom_operators_pie_chart': generate_bottom_operators_chart(),
    }
    
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
    """Generate top operators bar chart HTML"""
    return '''
    <div class="chart-container" style="position: relative; height: 300px;">
        <canvas id="topOperatorsChart"></canvas>
    </div>
    <script>
        const ctx2 = document.getElementById('topOperatorsChart').getContext('2d');
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: ['OP-003', 'OP-001', 'OP-006', 'OP-002', 'OP-005'],
                datasets: [{
                    label: 'GGR (Millions)',
                    data: [52.30, 45.20, 41.20, 38.75, 35.60],
                    backgroundColor: 'rgba(52, 152, 219, 0.8)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
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


def generate_bottom_operators_chart():
    """Generate bottom operators pie chart HTML"""
    return '''
    <div class="chart-container" style="position: relative; height: 250px; width: 100%;">
        <canvas id="bottomOperatorsChart"></canvas>
    </div>
    <script>
        const ctx3 = document.getElementById('bottomOperatorsChart').getContext('2d');
        new Chart(ctx3, {
            type: 'pie',
            data: {
                labels: ['OP-008', 'OP-007', 'OP-004', 'OP-005', 'OP-002'],
                datasets: [{
                    data: [19.80, 22.45, 28.90, 35.60, 38.75],
                    backgroundColor: [
                        'rgba(231, 76, 60, 0.8)',
                        'rgba(230, 126, 34, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(46, 204, 113, 0.8)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            padding: 10
                        }
                    }
                }
            }
        });
    </script>
    '''


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'dashboard/profile.html')


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
