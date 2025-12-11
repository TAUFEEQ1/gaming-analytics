import React, { useState } from 'react';
import { useFraud } from '../context/FraudContext';
import { AlertTriangle, Eye, Filter, Download } from 'lucide-react';

const FraudAlertsTable: React.FC = () => {
  const { alerts } = useFraud();
  const [filterType, setFilterType] = useState<string>('all');
  const [sortField, setSortField] = useState<'risk_score' | 'timestamp'>('risk_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const filteredAlerts = alerts
    .filter(alert => filterType === 'all' || alert.anomaly_type === filterType)
    .sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];
      
      if (sortField === 'timestamp') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }
      
      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const uniqueTypes = [...new Set(alerts.map(alert => alert.anomaly_type))];

  const getRiskLevel = (score: number) => {
    if (score >= 0.8) return { label: 'Critical', color: 'bg-red-100 text-red-800' };
    if (score >= 0.6) return { label: 'High', color: 'bg-orange-100 text-orange-800' };
    if (score >= 0.4) return { label: 'Medium', color: 'bg-yellow-100 text-yellow-800' };
    return { label: 'Low', color: 'bg-green-100 text-green-800' };
  };


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
    ].map(row => row.join(',')).join('\\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fraud_alerts_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="card-container">
      {/* Header */}
      <div className="card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="text-red-600" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Fraud Detection Alerts</h2>
              <p className="text-sm text-gray-600">Real-time anomaly detection results</p>
            </div>
            <span className="status-badge critical">
              {filteredAlerts.length} active alerts
            </span>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <Filter size={16} className="text-gray-500" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="filter-input text-sm min-w-[120px]"
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
              className="export-button"
            >
              <Download size={16} />
              <span>Export CSV</span>
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="professional-table w-full">
          <thead className="professional-table-header">
            <tr>
              <th>
                Transaction ID
              </th>
              <th>
                Operator
              </th>
              <th 
                className="sortable"
                onClick={() => {
                  if (sortField === 'risk_score') {
                    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
                  } else {
                    setSortField('risk_score');
                    setSortDirection('desc');
                  }
                }}
              >
                <div className="flex items-center">
                  Risk Score
                  <span className={`sort-indicator ${sortField === 'risk_score' ? 'active' : ''}`}>
                    {sortField === 'risk_score' ? (sortDirection === 'desc' ? '↓' : '↑') : '↕'}
                  </span>
                </div>
              </th>
              <th>
                Risk Level
              </th>
              <th>
                Anomaly Type
              </th>
              <th 
                className="sortable"
                onClick={() => {
                  if (sortField === 'timestamp') {
                    setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
                  } else {
                    setSortField('timestamp');
                    setSortDirection('desc');
                  }
                }}
              >
                <div className="flex items-center">
                  Timestamp
                  <span className={`sort-indicator ${sortField === 'timestamp' ? 'active' : ''}`}>
                    {sortField === 'timestamp' ? (sortDirection === 'desc' ? '↓' : '↑') : '↕'}
                  </span>
                </div>
              </th>
              <th>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredAlerts.map((alert, index) => {
              const riskLevel = getRiskLevel(alert.risk_score);
              const riskClass = riskLevel.label.toLowerCase();
              return (
                <tr key={alert.transaction_id}>
                  <td>
                    <div className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                      {alert.transaction_id.substring(0, 8)}
                      <span className="text-gray-400">...</span>
                      {alert.transaction_id.substring(alert.transaction_id.length - 4)}
                    </div>
                  </td>
                  <td>
                    <div className="font-semibold text-gray-900">
                      {alert.operator_id}
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center space-x-3">
                      <div className="flex-1">
                        <div className="progress-bar">
                          <div 
                            className={`progress-bar-fill ${riskClass}`}
                            style={{ width: `${alert.risk_score * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <span className="text-sm font-bold text-gray-700 min-w-[50px] text-right">
                        {(alert.risk_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${riskClass}`}>
                      {riskLevel.label}
                    </span>
                  </td>
                  <td>
                    <span className="text-gray-900 font-medium">
                      {alert.anomaly_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </td>
                  <td>
                    <div className="text-gray-600">
                      <div className="text-sm font-medium">
                        {new Date(alert.timestamp).toLocaleDateString()}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </td>
                  <td>
                    <button className="action-button secondary" title="View Details">
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filteredAlerts.length === 0 && (
        <div className="text-center py-12">
          <div className="flex flex-col items-center space-y-3">
            <div className="p-4 bg-gray-100 rounded-full">
              <AlertTriangle className="text-gray-400" size={32} />
            </div>
            <div>
              <h3 className="text-lg font-medium text-gray-900">No alerts found</h3>
              <p className="text-gray-500">No fraud alerts match the selected criteria.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FraudAlertsTable;