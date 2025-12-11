import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'
import { Shield, AlertTriangle } from 'lucide-react'

// Mock data for demonstration
const mockRiskData = [
  { name: 'Low Risk', value: 72, color: '#10b981', count: 33042 },
  { name: 'Medium Risk', value: 18, color: '#f59e0b', count: 8260 },
  { name: 'High Risk', value: 7, color: '#ef4444', count: 3212 },
  { name: 'Critical Risk', value: 3, color: '#dc2626', count: 1378 },
]

const RiskDistribution: React.FC = () => {
  const riskData = mockRiskData

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-4 rounded-xl shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{data.name}</p>
          <div className="space-y-1">
            <p className="text-sm">
              <span className="font-medium">Percentage:</span> {data.value}%
            </p>
            <p className="text-sm">
              <span className="font-medium">Transactions:</span> {data.count.toLocaleString()}
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
      <div className="bg-gradient-to-r from-purple-50 to-violet-50 px-6 py-6 border-b border-gray-200">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-gradient-to-r from-purple-500 to-violet-500 rounded-xl shadow-lg">
            <Shield className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Risk Distribution</h2>
            <p className="text-gray-600 mt-1">Transaction risk level breakdown</p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={riskData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={120}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {riskData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        
        {/* Legend */}
        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-gray-100">
          {riskData.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-gray-50 to-gray-100 hover:from-gray-100 hover:to-gray-200 transition-all duration-200">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <div>
                  <span className="text-sm font-semibold text-gray-900">{item.name}</span>
                  <div className="text-xs text-gray-600">{item.count.toLocaleString()} transactions</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">{item.value}%</div>
                {item.name.includes('Critical') && (
                  <AlertTriangle size={16} className="text-red-500 ml-auto" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default RiskDistribution