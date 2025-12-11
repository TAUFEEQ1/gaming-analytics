import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useFraud } from '../context/FraudContext';
import { TrendingUp } from 'lucide-react';

const TrendsChart: React.FC = () => {
  const { trends } = useFraud();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'UGX',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: 'compact'
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{formatDate(label)}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between space-x-4">
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-sm text-gray-600">{entry.name}:</span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {entry.name === 'Active Operators' || entry.name === 'Total Bets' 
                  ? entry.value.toLocaleString()
                  : formatCurrency(entry.value)
                }
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-container">
      <div className="card-header">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <TrendingUp className="text-blue-600" size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Financial Trends Analysis</h2>
            <p className="text-sm text-gray-600">Daily performance metrics and growth patterns</p>
          </div>
        </div>
      </div>
      
      <div className="card-content">
        {trends.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
            <div className="p-4 bg-gray-100 rounded-full mb-4">
              <TrendingUp className="text-gray-400" size={32} />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-1">No Trend Data</h3>
              <p className="text-gray-500">Trend analysis will appear here when data is available.</p>
            </div>
          </div>
        ) : (
          <>
            <div className="h-80 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={formatDate}
                    stroke="#6b7280"
                    fontSize={12}
                    tick={{ fill: '#6b7280' }}
                  />
                  <YAxis 
                    tickFormatter={formatCurrency}
                    stroke="#6b7280"
                    fontSize={12}
                    tick={{ fill: '#6b7280' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  
                  <Line
                    type="monotone"
                    dataKey="total_stakes"
                    stroke="#3b82f6"
                    strokeWidth={3}
                    name="Total Stakes"
                    dot={{ fill: '#3b82f6', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8, stroke: '#3b82f6', strokeWidth: 2, fill: '#ffffff' }}
                  />
                  
                  <Line
                    type="monotone"
                    dataKey="total_payouts"
                    stroke="#10b981"
                    strokeWidth={3}
                    name="Total Payouts"
                    dot={{ fill: '#10b981', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8, stroke: '#10b981', strokeWidth: 2, fill: '#ffffff' }}
                  />
                  
                  <Line
                    type="monotone"
                    dataKey="ggr"
                    stroke="#f59e0b"
                    strokeWidth={3}
                    name="GGR"
                    dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
                    activeDot={{ r: 8, stroke: '#f59e0b', strokeWidth: 2, fill: '#ffffff' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-6 border-t border-gray-100">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <div className="text-xs font-semibold text-blue-900 uppercase tracking-wide mb-1">Avg Daily Stakes</div>
                <div className="text-xl font-bold text-blue-600">
                  {formatCurrency(trends.reduce((sum, item) => sum + item.total_stakes, 0) / trends.length)}
                </div>
              </div>
              
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <div className="text-xs font-semibold text-green-900 uppercase tracking-wide mb-1">Avg Daily Payouts</div>
                <div className="text-xl font-bold text-green-600">
                  {formatCurrency(trends.reduce((sum, item) => sum + item.total_payouts, 0) / trends.length)}
                </div>
              </div>
              
              <div className="bg-yellow-50 rounded-lg p-4 text-center">
                <div className="text-xs font-semibold text-yellow-900 uppercase tracking-wide mb-1">Avg Daily GGR</div>
                <div className="text-xl font-bold text-yellow-600">
                  {formatCurrency(trends.reduce((sum, item) => sum + item.ggr, 0) / trends.length)}
                </div>
              </div>
              
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <div className="text-xs font-semibold text-purple-900 uppercase tracking-wide mb-1">Avg Active Operators</div>
                <div className="text-xl font-bold text-purple-600">
                  {Math.round(trends.reduce((sum, item) => sum + item.active_operators, 0) / trends.length)}
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TrendsChart;