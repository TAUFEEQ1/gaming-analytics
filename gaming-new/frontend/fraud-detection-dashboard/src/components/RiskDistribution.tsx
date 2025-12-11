import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useFraud } from '../context/FraudContext';
import { PieChartIcon } from 'lucide-react';

const RiskDistribution: React.FC = () => {
  const { alerts } = useFraud();

  const getRiskLevel = (score: number) => {
    if (score >= 0.8) return 'Critical';
    if (score >= 0.6) return 'High';
    if (score >= 0.4) return 'Medium';
    return 'Low';
  };

  const riskDistribution = alerts.reduce((acc, alert) => {
    const level = getRiskLevel(alert.risk_score);
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const data = Object.entries(riskDistribution).map(([level, count]) => ({
    name: level,
    value: count,
    percentage: ((count / alerts.length) * 100).toFixed(1)
  }));

  const COLORS = {
    'Critical': '#dc2626',
    'High': '#ea580c',
    'Medium': '#d97706',
    'Low': '#16a34a'
  };

  const anomaliesByType = alerts.reduce((acc, alert) => {
    const type = alert.anomaly_type.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase());
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const typeData = Object.entries(anomaliesByType)
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <div className="font-semibold text-gray-900">{data.name}</div>
          <div className="text-sm text-gray-600">Count: {data.value}</div>
          <div className="text-sm text-gray-600">Percentage: {data.percentage}%</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-container">
      <div className="card-header">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <PieChartIcon className="text-purple-600" size={20} />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Risk Distribution Analysis</h2>
            <p className="text-sm text-gray-600">Alert classification and anomaly breakdown</p>
          </div>
        </div>
      </div>

      <div className="card-content">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
            <div className="p-4 bg-gray-100 rounded-full mb-4">
              <PieChartIcon className="text-gray-400" size={32} />
            </div>
            <div className="text-center">
              <h3 className="text-lg font-medium text-gray-900 mb-1">No Risk Data</h3>
              <p className="text-gray-500">Risk distribution analysis will appear here when alerts are available.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Risk Level Distribution */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Level Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {data.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={COLORS[entry.name as keyof typeof COLORS]}
                          stroke="#ffffff"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              {/* Enhanced Legend */}
              <div className="grid grid-cols-2 gap-3 mt-6">
                {data.map((entry) => (
                  <div key={entry.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-full shadow-sm"
                        style={{ backgroundColor: COLORS[entry.name as keyof typeof COLORS] }}
                      />
                      <span className="font-medium text-gray-900">{entry.name}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-900">{entry.value}</div>
                      <div className="text-xs text-gray-500">{entry.percentage}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Anomaly Types */}
            <div className="pt-6 border-t border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Anomaly Type Breakdown</h3>
              <div className="space-y-3">
                {typeData.map(({ type, count }, index) => (
                  <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 font-bold text-sm">{index + 1}</span>
                      </div>
                      <span className="font-medium text-gray-900">{type}</span>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="w-24 bg-gray-200 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300"
                          style={{ width: `${(count / Math.max(...typeData.map(d => d.count))) * 100}%` }}
                        />
                      </div>
                      <span className="font-bold text-gray-900 min-w-[2rem] text-right">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskDistribution;