import React from 'react';
import { useFraud } from '../context/FraudContext';
import { TrendingUp, TrendingDown, AlertTriangle, DollarSign, Users, Activity } from 'lucide-react';

const MetricsCards: React.FC = () => {
  const { metrics } = useFraud();

  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="card-container animate-pulse">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="h-10 w-10 bg-gray-200 rounded-lg"></div>
                <div className="h-4 w-4 bg-gray-200 rounded"></div>
              </div>
              <div className="h-4 bg-gray-200 rounded mb-3"></div>
              <div className="h-8 bg-gray-200 rounded"></div>
              <div className="h-3 bg-gray-200 rounded mt-3 w-3/4"></div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'UGX',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const cards = [
    {
      title: 'Total Transactions',
      value: metrics.total_transactions.toLocaleString(),
      icon: Activity,
      color: 'blue',
      trend: null
    },
    {
      title: 'High Risk Transactions',
      value: metrics.high_risk_transactions.toLocaleString(),
      icon: AlertTriangle,
      color: 'red',
      trend: metrics.risk_percentage > 10 ? 'up' : 'down'
    },
    {
      title: 'Risk Percentage',
      value: formatPercentage(metrics.risk_percentage),
      icon: TrendingUp,
      color: metrics.risk_percentage > 10 ? 'red' : 'green',
      trend: metrics.risk_percentage > 10 ? 'up' : 'down'
    },
    {
      title: 'Total Stakes',
      value: formatCurrency(metrics.total_stakes),
      icon: DollarSign,
      color: 'green',
      trend: null
    },
    {
      title: 'Total Payouts',
      value: formatCurrency(metrics.total_payouts),
      icon: DollarSign,
      color: 'blue',
      trend: null
    },
    {
      title: 'Active Operators',
      value: metrics.operators_count.toString(),
      icon: Users,
      color: 'purple',
      trend: null
    }
  ];

  const getIconColor = (color: string) => {
    const colors: Record<string, string> = {
      blue: 'text-white bg-gradient-to-r from-blue-500 to-blue-600',
      red: 'text-white bg-gradient-to-r from-red-500 to-red-600',
      green: 'text-white bg-gradient-to-r from-green-500 to-green-600',
      purple: 'text-white bg-gradient-to-r from-purple-500 to-purple-600'
    };
    return colors[color] || colors.blue;
  };

  const getTrendIcon = (trend: string | null) => {
    if (trend === 'up') return <TrendingUp size={16} className="text-red-500" />;
    if (trend === 'down') return <TrendingDown size={16} className="text-green-500" />;
    return null;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon;
        return (
          <div key={index} className="card-container relative overflow-hidden">
            <div className="card-content py-8 px-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl shadow-lg ${getIconColor(card.color)}`}>
                  <Icon size={24} />
                </div>
                <div className="flex items-center space-x-1">
                  {getTrendIcon(card.trend)}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-3">{card.title}</h3>
                <p className="text-3xl font-bold text-gray-900 mb-2 leading-tight break-words">{card.value}</p>
              </div>
              
              {card.title === 'High Risk Transactions' && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                    <span className="text-xs text-gray-600 font-medium">
                      {metrics.suspicious_operators} suspicious operators
                    </span>
                  </div>
                </div>
              )}

              {card.title === 'Risk Percentage' && (
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        metrics.risk_percentage > 10 ? 'bg-red-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(metrics.risk_percentage, 100)}%` }}
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
        );
      })}
    </div>
  );
};

export default MetricsCards;