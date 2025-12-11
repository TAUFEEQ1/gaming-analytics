import React from 'react'
import { TrendingUp, TrendingDown, AlertTriangle, DollarSign, Users, Activity } from 'lucide-react'

// Mock data for demonstration
const mockMetrics = {
  total_transactions: 45892,
  high_risk_transactions: 1247,
  risk_percentage: 2.7,
  total_stakes: 8945672,
  total_payouts: 7834521,
  operators_count: 23,
  suspicious_operators: 3
}

const MetricsCards: React.FC = () => {
  const metrics = mockMetrics

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value)
  }

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  const cards = [
    {
      title: 'Total Transactions',
      value: metrics.total_transactions.toLocaleString(),
      icon: Activity,
      color: 'from-blue-500 to-cyan-500',
      bgColor: 'from-blue-50 to-cyan-50',
      trend: null
    },
    {
      title: 'High Risk Transactions',
      value: metrics.high_risk_transactions.toLocaleString(),
      icon: AlertTriangle,
      color: 'from-red-500 to-orange-500',
      bgColor: 'from-red-50 to-orange-50',
      trend: metrics.risk_percentage > 10 ? 'up' : 'down'
    },
    {
      title: 'Risk Percentage',
      value: formatPercentage(metrics.risk_percentage),
      icon: TrendingUp,
      color: metrics.risk_percentage > 10 ? 'from-red-500 to-orange-500' : 'from-green-500 to-emerald-500',
      bgColor: metrics.risk_percentage > 10 ? 'from-red-50 to-orange-50' : 'from-green-50 to-emerald-50',
      trend: metrics.risk_percentage > 10 ? 'up' : 'down'
    },
    {
      title: 'Total Stakes',
      value: formatCurrency(metrics.total_stakes),
      icon: DollarSign,
      color: 'from-green-500 to-emerald-500',
      bgColor: 'from-green-50 to-emerald-50',
      trend: null
    },
    {
      title: 'Total Payouts',
      value: formatCurrency(metrics.total_payouts),
      icon: DollarSign,
      color: 'from-purple-500 to-violet-500',
      bgColor: 'from-purple-50 to-violet-50',
      trend: null
    },
    {
      title: 'Active Operators',
      value: metrics.operators_count.toString(),
      icon: Users,
      color: 'from-indigo-500 to-purple-500',
      bgColor: 'from-indigo-50 to-purple-50',
      trend: null
    }
  ]

  const getTrendIcon = (trend: string | null) => {
    if (trend === 'up') return <TrendingUp size={16} className="text-red-500" />
    if (trend === 'down') return <TrendingDown size={16} className="text-green-500" />
    return null
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon
        return (
          <div 
            key={index} 
            className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${card.bgColor} p-6 shadow-lg border border-white/50 backdrop-blur-sm hover:shadow-xl transition-all duration-300 hover:scale-105 group`}
          >
            {/* Animated background effect */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl shadow-lg bg-gradient-to-r ${card.color} text-white`}>
                  <Icon size={24} />
                </div>
                <div className="flex items-center space-x-1">
                  {getTrendIcon(card.trend)}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-2">{card.title}</h3>
                <p className="text-2xl font-bold text-gray-900 mb-1">{card.value}</p>
              </div>
              
              {card.title === 'High Risk Transactions' && (
                <div className="mt-3 pt-3 border-t border-gray-200/50">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
                    <span className="text-xs text-gray-600 font-medium">
                      {metrics.suspicious_operators} suspicious operators
                    </span>
                  </div>
                </div>
              )}

              {card.title === 'Risk Percentage' && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 bg-gradient-to-r ${
                        metrics.risk_percentage > 10 ? 'from-red-400 to-red-500' : 'from-green-400 to-green-500'
                      }`}
                      style={{ width: `${Math.min(metrics.risk_percentage * 10, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            
            {/* Subtle background pattern */}
            <div className="absolute top-0 right-0 w-20 h-20 transform rotate-12 translate-x-6 -translate-y-6 opacity-5">
              <Icon size={80} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default MetricsCards