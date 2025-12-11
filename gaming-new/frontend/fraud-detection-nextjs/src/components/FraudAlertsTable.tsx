import React, { useState } from 'react'
import { AlertTriangle, Eye, Filter, Download, TrendingUp } from 'lucide-react'

// Mock data for demonstration
const mockAlerts = [
  {
    transaction_id: 'tx_8f4a9b2c1d7e5g6h8i9j0k1l2m3n4o5p',
    operator_id: 'OP_001',
    risk_score: 0.92,
    anomaly_type: 'unusual_betting_pattern',
    timestamp: '2024-12-11T14:30:00Z'
  },
  {
    transaction_id: 'tx_7e3c5a1b9f2d4g8h5i6j7k8l9m0n1o2p',
    operator_id: 'OP_007',
    risk_score: 0.85,
    anomaly_type: 'suspicious_win_rate',
    timestamp: '2024-12-11T13:45:00Z'
  },
  {
    transaction_id: 'tx_6d2a8b4c5f1g9h3i7j4k6l8m9n2o5p7q',
    operator_id: 'OP_003',
    risk_score: 0.78,
    anomaly_type: 'high_frequency_betting',
    timestamp: '2024-12-11T12:15:00Z'
  },
  {
    transaction_id: 'tx_5c1a7b3e4d9f2g8h6i5j4k7l9m1n3o6p',
    operator_id: 'OP_012',
    risk_score: 0.71,
    anomaly_type: 'unusual_betting_pattern',
    timestamp: '2024-12-11T11:20:00Z'
  },
  {
    transaction_id: 'tx_4b9e6a2c8f1d5g7h4i3j6k5l8m9n2o4p',
    operator_id: 'OP_005',
    risk_score: 0.65,
    anomaly_type: 'velocity_anomaly',
    timestamp: '2024-12-11T10:35:00Z'
  }
]

const FraudAlertsTable: React.FC = () => {
  const alerts = mockAlerts
  const [filterType, setFilterType] = useState<string>('all')
  const [sortField, setSortField] = useState<'risk_score' | 'timestamp'>('risk_score')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  const filteredAlerts = alerts
    .filter(alert => filterType === 'all' || alert.anomaly_type === filterType)
    .sort((a, b) => {
      let aValue = a[sortField]
      let bValue = b[sortField]
      
      if (sortField === 'timestamp') {
        aValue = new Date(aValue).getTime()
        bValue = new Date(bValue).getTime()
      }
      
      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1
      } else {
        return aValue < bValue ? 1 : -1
      }
    })

  const uniqueTypes = [...new Set(alerts.map(alert => alert.anomaly_type))]

  const getRiskLevel = (score: number) => {
    if (score >= 0.8) return { label: 'Critical', color: 'from-red-500 to-red-600', textColor: 'text-red-700', bgColor: 'bg-red-100' }
    if (score >= 0.6) return { label: 'High', color: 'from-orange-500 to-orange-600', textColor: 'text-orange-700', bgColor: 'bg-orange-100' }
    if (score >= 0.4) return { label: 'Medium', color: 'from-yellow-500 to-yellow-600', textColor: 'text-yellow-700', bgColor: 'bg-yellow-100' }
    return { label: 'Low', color: 'from-green-500 to-green-600', textColor: 'text-green-700', bgColor: 'bg-green-100' }
  }

  const exportToCSV = () => {
    const csvContent = [
      ['Transaction ID', 'Operator ID', 'Risk Score', 'Anomaly Type', 'Timestamp'],
      ...filteredAlerts.map(alert => [
        alert.transaction_id,
        alert.operator_id,
        alert.risk_score.toFixed(3),
        alert.anomaly_type,
        alert.timestamp
      ])
    ].map(row => row.join(',')).join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fraud_alerts_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-red-50 to-orange-50 px-6 py-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-r from-red-500 to-red-600 rounded-xl shadow-lg">
              <AlertTriangle className="text-white" size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                <span>Fraud Detection Alerts</span>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="text-red-500 animate-pulse" size={20} />
                </div>
              </h2>
              <p className="text-gray-600 mt-1">Real-time anomaly detection results</p>
            </div>
            <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg">
              {filteredAlerts.length} active alerts
            </span>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-3 bg-white/70 backdrop-blur-sm rounded-xl px-4 py-3 shadow-md border border-gray-200">
              <Filter size={18} className="text-gray-500" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-transparent focus:outline-none text-sm min-w-[120px] font-medium text-gray-700"
              >
                <option value="all">All Types</option>
                {uniqueTypes.map(type => (
                  <option key={type} value={type}>
                    {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </option>
                ))}
              </select>
            </div>
            
            <button
              onClick={exportToCSV}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 hover:scale-105"
            >
              <Download size={18} />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gradient-to-r from-gray-50 to-gray-100">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Transaction ID
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Operator
              </th>
              <th 
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors duration-200"
                onClick={() => {
                  if (sortField === 'risk_score') {
                    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc')
                  } else {
                    setSortField('risk_score')
                    setSortDirection('desc')
                  }
                }}
              >
                <div className="flex items-center space-x-2">
                  <span>Risk Score</span>
                  <span className={`transition-colors duration-200 ${sortField === 'risk_score' ? 'text-blue-600' : 'text-gray-400'}`}>
                    {sortField === 'risk_score' ? (sortDirection === 'desc' ? '↓' : '↑') : '↕'}
                  </span>
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Risk Level
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Anomaly Type
              </th>
              <th 
                className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-200 transition-colors duration-200"
                onClick={() => {
                  if (sortField === 'timestamp') {
                    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc')
                  } else {
                    setSortField('timestamp')
                    setSortDirection('desc')
                  }
                }}
              >
                <div className="flex items-center space-x-2">
                  <span>Timestamp</span>
                  <span className={`transition-colors duration-200 ${sortField === 'timestamp' ? 'text-blue-600' : 'text-gray-400'}`}>
                    {sortField === 'timestamp' ? (sortDirection === 'desc' ? '↓' : '↑') : '↕'}
                  </span>
                </div>
              </th>
              <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAlerts.map((alert, index) => {
              const riskLevel = getRiskLevel(alert.risk_score)
              return (
                <tr key={alert.transaction_id} className="hover:bg-blue-50 transition-all duration-200 group">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-mono text-sm bg-gradient-to-r from-gray-100 to-gray-200 px-3 py-2 rounded-lg border border-gray-300">
                      {alert.transaction_id.substring(0, 8)}
                      <span className="text-gray-500">...</span>
                      {alert.transaction_id.substring(alert.transaction_id.length - 4)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-bold text-gray-900 text-lg">
                      {alert.operator_id}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-3">
                      <div className="flex-1 max-w-[120px]">
                        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                          <div 
                            className={`h-3 rounded-full transition-all duration-500 bg-gradient-to-r ${riskLevel.color} shadow-sm`}
                            style={{ width: `${alert.risk_score * 100}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-sm font-bold text-gray-700 min-w-[50px] text-right">
                        {(alert.risk_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${riskLevel.bgColor} ${riskLevel.textColor} border border-current/20`}>
                      {riskLevel.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-gray-900 font-medium bg-gradient-to-r from-blue-50 to-indigo-50 px-3 py-2 rounded-lg">
                      {alert.anomaly_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-gray-600">
                      <div className="text-sm font-medium">
                        {new Date(alert.timestamp).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button 
                      className="p-3 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-blue-600 rounded-xl transition-all duration-200 hover:scale-110 hover:shadow-md"
                      title="View Details"
                    >
                      <Eye size={18} />
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {filteredAlerts.length === 0 && (
        <div className="text-center py-16">
          <div className="flex flex-col items-center space-y-4">
            <div className="p-6 bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl">
              <AlertTriangle className="text-gray-400" size={40} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">No alerts found</h3>
              <p className="text-gray-500">No fraud alerts match the selected criteria.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default FraudAlertsTable