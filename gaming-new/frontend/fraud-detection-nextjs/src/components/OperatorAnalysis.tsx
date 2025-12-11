import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Users, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react'

// Mock data for demonstration
const mockOperatorData = [
  { 
    operator_id: 'OP_001', 
    risk_score: 0.89, 
    total_transactions: 12450, 
    high_risk_count: 234,
    status: 'Critical',
    change: 15.2
  },
  { 
    operator_id: 'OP_007', 
    risk_score: 0.72, 
    total_transactions: 8930, 
    high_risk_count: 89,
    status: 'High',
    change: -8.1
  },
  { 
    operator_id: 'OP_003', 
    risk_score: 0.65, 
    total_transactions: 15670, 
    high_risk_count: 156,
    status: 'High',
    change: 12.5
  },
  { 
    operator_id: 'OP_012', 
    risk_score: 0.43, 
    total_transactions: 22100, 
    high_risk_count: 78,
    status: 'Medium',
    change: -3.2
  },
  { 
    operator_id: 'OP_005', 
    risk_score: 0.31, 
    total_transactions: 18950, 
    high_risk_count: 45,
    status: 'Low',
    change: -1.8
  },
  { 
    operator_id: 'OP_009', 
    risk_score: 0.28, 
    total_transactions: 24560, 
    high_risk_count: 32,
    status: 'Low',
    change: 2.1
  },
]

const OperatorAnalysis: React.FC = () => {
  const operatorData = mockOperatorData.sort((a, b) => b.risk_score - a.risk_score)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Critical': return { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200' }
      case 'High': return { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-200' }
      case 'Medium': return { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' }
      default: return { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200' }
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 rounded-xl shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            <p className="text-sm">
              <span className="font-medium text-red-600">Risk Score:</span> {(data.risk_score * 100).toFixed(1)}%
            </p>
            <p className="text-sm">
              <span className="font-medium text-blue-600">Total Transactions:</span> {data.total_transactions.toLocaleString()}
            </p>
            <p className="text-sm">
              <span className="font-medium text-orange-600">High Risk:</span> {data.high_risk_count}
            </p>
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-8">
      {/* Chart Section */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 px-6 py-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl shadow-lg">
              <Users className="text-white" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Operator Risk Analysis</h2>
              <p className="text-gray-600 mt-1">Risk scores by gaming operator</p>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={operatorData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="operator_id" 
                  stroke="#6b7280"
                  fontSize={12}
                />
                <YAxis 
                  stroke="#6b7280"
                  fontSize={12}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="risk_score" 
                  fill="url(#barGradient)"
                  radius={[4, 4, 0, 0]}
                />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-bold text-gray-900">Detailed Operator Metrics</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Operator ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Total Transactions
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  High Risk Count
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Weekly Change
                </th>
                <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {operatorData.map((operator, index) => {
                const status = getStatusColor(operator.status)
                return (
                  <tr key={operator.operator_id} className="hover:bg-blue-50 transition-all duration-200">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-bold text-gray-900 text-lg">
                        {operator.operator_id}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <div className="flex-1 max-w-[100px]">
                          <div className="w-full bg-gray-200 rounded-full h-3">
                            <div 
                              className="h-3 rounded-full bg-gradient-to-r from-purple-500 to-violet-500"
                              style={{ width: `${operator.risk_score * 100}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-sm font-bold text-gray-700">
                          {(operator.risk_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${status.bg} ${status.text} border ${status.border}`}>
                        {operator.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-gray-900 font-medium">
                        {operator.total_transactions.toLocaleString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle size={16} className="text-red-500" />
                        <span className="font-semibold text-red-600">
                          {operator.high_risk_count}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`flex items-center space-x-1 ${operator.change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {operator.change >= 0 ? (
                          <TrendingUp size={16} />
                        ) : (
                          <TrendingDown size={16} />
                        )}
                        <span className="font-semibold">
                          {operator.change >= 0 ? '+' : ''}{operator.change}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button 
                        className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg text-sm font-medium hover:from-blue-600 hover:to-blue-700 transition-all duration-200 hover:scale-105"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default OperatorAnalysis