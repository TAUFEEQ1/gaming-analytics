import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { TrendingUp } from 'lucide-react'

// Mock data for demonstration
const mockTrendsData = [
  { date: '2024-12-07', risk_score: 2.1, transactions: 8450 },
  { date: '2024-12-08', risk_score: 2.8, transactions: 9120 },
  { date: '2024-12-09', risk_score: 1.9, transactions: 7890 },
  { date: '2024-12-10', risk_score: 3.4, transactions: 10200 },
  { date: '2024-12-11', risk_score: 2.7, transactions: 9650 },
]

const TrendsChart: React.FC = () => {
  const trendsData = mockTrendsData

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 rounded-xl shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            <p className="text-sm">
              <span className="font-medium text-red-600">Risk Score:</span> {payload[0].value.toFixed(1)}%
            </p>
            <p className="text-sm">
              <span className="font-medium text-blue-600">Transactions:</span> {payload[1].value.toLocaleString()}
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 px-6 py-6 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl shadow-lg">
            <TrendingUp className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Risk Trends Analysis</h2>
            <p className="text-gray-600 mt-1">7-day fraud detection trends</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendsData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#6b7280"
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis 
                yAxisId="risk"
                orientation="left"
                stroke="#ef4444"
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
              />
              <YAxis 
                yAxisId="transactions"
                orientation="right"
                stroke="#3b82f6"
                fontSize={12}
                tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                yAxisId="risk"
                type="monotone"
                dataKey="risk_score"
                stroke="url(#riskGradient)"
                strokeWidth={3}
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8, stroke: '#ef4444', strokeWidth: 2 }}
              />
              <Line
                yAxisId="transactions"
                type="monotone"
                dataKey="transactions"
                stroke="url(#transactionGradient)"
                strokeWidth={3}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 6 }}
                activeDot={{ r: 8, stroke: '#3b82f6', strokeWidth: 2 }}
              />
              <defs>
                <linearGradient id="riskGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#ef4444" />
                  <stop offset="100%" stopColor="#f97316" />
                </linearGradient>
                <linearGradient id="transactionGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="flex items-center justify-center space-x-8 mt-6 pt-6 border-t border-gray-100">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gradient-to-r from-red-500 to-orange-500 rounded-full"></div>
            <span className="text-sm font-medium text-gray-700">Risk Score (%)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
            <span className="text-sm font-medium text-gray-700">Transaction Volume</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TrendsChart