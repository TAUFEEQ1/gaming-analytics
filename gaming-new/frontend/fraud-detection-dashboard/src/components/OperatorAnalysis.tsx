import React, { useState } from 'react';
import { useFraud } from '../context/FraudContext';
import { Users, AlertTriangle, DollarSign, TrendingUp, Search } from 'lucide-react';

const OperatorAnalysis: React.FC = () => {
  const { alerts, getOperatorProfile } = useFraud();
  const [selectedOperator, setSelectedOperator] = useState<string>('');
  const [operatorDetails, setOperatorDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Get operator statistics from alerts
  const operatorStats = alerts.reduce((acc, alert) => {
    const operatorId = alert.operator_id;
    if (!acc[operatorId]) {
      acc[operatorId] = {
        operatorId,
        totalAlerts: 0,
        avgRiskScore: 0,
        highRiskAlerts: 0,
        anomalyTypes: new Set()
      };
    }
    
    acc[operatorId].totalAlerts++;
    acc[operatorId].avgRiskScore += alert.risk_score;
    if (alert.risk_score >= 0.6) acc[operatorId].highRiskAlerts++;
    acc[operatorId].anomalyTypes.add(alert.anomaly_type);
    
    return acc;
  }, {} as Record<string, any>);

  // Calculate averages and convert to array
  const operatorList = Object.values(operatorStats).map((op: any) => ({
    ...op,
    avgRiskScore: op.avgRiskScore / op.totalAlerts,
    anomalyTypesCount: op.anomalyTypes.size,
    anomalyTypes: Array.from(op.anomalyTypes)
  })).sort((a: any, b: any) => b.avgRiskScore - a.avgRiskScore);

  const handleOperatorSelect = async (operatorId: string) => {
    if (operatorId === selectedOperator) return;
    
    setSelectedOperator(operatorId);
    setLoading(true);
    
    try {
      const profile = await getOperatorProfile(operatorId);
      setOperatorDetails(profile);
    } catch (error) {
      console.error('Failed to fetch operator profile:', error);
      setOperatorDetails(null);
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevelColor = (score: number) => {
    if (score >= 0.8) return 'bg-red-500';
    if (score >= 0.6) return 'bg-orange-500';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'UGX',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: 'compact'
    }).format(value);
  };

  return (
    <div className="space-y-6">
      {/* Operator List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Users className="text-purple-600" size={20} />
            <h2 className="text-lg font-semibold text-gray-900">Operator Risk Analysis</h2>
            <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
              {operatorList.length} operators
            </span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Operator ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Alerts
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  High Risk Alerts
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Risk Score
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Anomaly Types
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {operatorList.map((operator: any, index) => (
                <tr 
                  key={operator.operatorId} 
                  className={`${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'} ${
                    selectedOperator === operator.operatorId ? 'ring-2 ring-blue-500' : ''
                  }`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {operator.operatorId}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                      {operator.totalAlerts}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    <span className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs">
                      {operator.highRiskAlerts}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="flex-1">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${getRiskLevelColor(operator.avgRiskScore)}`}
                            style={{ width: `${operator.avgRiskScore * 100}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs font-medium w-12 text-right">
                        {(operator.avgRiskScore * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {operator.anomalyTypesCount} types
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <button
                      onClick={() => handleOperatorSelect(operator.operatorId)}
                      className="text-blue-600 hover:text-blue-900 flex items-center space-x-1"
                    >
                      <Search size={14} />
                      <span>Details</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Operator Details */}
      {selectedOperator && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">
              Operator Profile: {selectedOperator}
            </h3>
          </div>

          <div className="p-4">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Loading operator details...</span>
              </div>
            ) : operatorDetails ? (
              <div className="space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-blue-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <DollarSign className="text-blue-600" size={16} />
                      <span className="text-sm font-medium text-blue-900">Total Stakes</span>
                    </div>
                    <div className="text-xl font-bold text-blue-900">
                      {formatCurrency(operatorDetails.total_stakes)}
                    </div>
                  </div>

                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <DollarSign className="text-green-600" size={16} />
                      <span className="text-sm font-medium text-green-900">Total Payouts</span>
                    </div>
                    <div className="text-xl font-bold text-green-900">
                      {formatCurrency(operatorDetails.total_payouts)}
                    </div>
                  </div>

                  <div className="bg-yellow-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <TrendingUp className="text-yellow-600" size={16} />
                      <span className="text-sm font-medium text-yellow-900">Win Rate</span>
                    </div>
                    <div className="text-xl font-bold text-yellow-900">
                      {(operatorDetails.win_rate * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div className="bg-purple-50 rounded-lg p-4">
                    <div className="flex items-center space-x-2 mb-2">
                      <AlertTriangle className="text-purple-600" size={16} />
                      <span className="text-sm font-medium text-purple-900">Transactions</span>
                    </div>
                    <div className="text-xl font-bold text-purple-900">
                      {operatorDetails.total_transactions.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Risk Indicators */}
                <div className="bg-gray-50 rounded-xl p-6">
                  <h4 className="text-lg font-bold text-gray-900 mb-4 flex items-center space-x-2">
                    <AlertTriangle className="text-orange-500" size={20} />
                    <span>Risk Assessment Matrix</span>
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(operatorDetails.risk_indicators || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                        <span className="text-sm font-semibold text-gray-700">
                          {key.replace('_', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
                        </span>
                        <span className={`status-badge ${
                          value ? 'critical' : 'low'
                        }`}>
                          {value ? 'Flagged' : 'Clear'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="flex flex-col items-center space-y-3">
                  <div className="p-4 bg-red-100 rounded-full">
                    <AlertTriangle className="text-red-500" size={32} />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Failed to Load Details</h3>
                    <p className="text-gray-500">Unable to retrieve operator profile. Please try again.</p>
                  </div>
                  <button
                    onClick={() => handleOperatorSelect(selectedOperator)}
                    className="action-button primary"
                  >
                    Retry
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default OperatorAnalysis;