import React, { useState } from 'react';
import { useFraud } from '../context/FraudContext';
import MetricsCards from './MetricsCards';
import FraudAlertsTable from './FraudAlertsTable';
import TrendsChart from './TrendsChart';
import RiskDistribution from './RiskDistribution';
import OperatorAnalysis from './OperatorAnalysis';
import { RefreshCw, AlertTriangle, Shield, TrendingUp } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { loading, error, refreshData } = useFraud();
  const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'trends' | 'operators'>('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield },
    { id: 'alerts', label: 'Fraud Alerts', icon: AlertTriangle },
    { id: 'trends', label: 'Trends Analysis', icon: TrendingUp },
    { id: 'operators', label: 'Operator Profiles', icon: RefreshCw }
  ];

  return (
    <div className="dashboard">
      {/* Header Controls */}
      <div className="flex justify-between items-center mb-8">
        <div className="flex space-x-1 bg-white rounded-xl p-2 shadow-lg border border-gray-100">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg transform scale-105'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <Icon size={18} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
        
        <button
          onClick={refreshData}
          disabled={loading}
          className="export-button disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-gradient-to-r from-red-50 to-red-100 border-l-4 border-red-500 text-red-700 px-6 py-4 rounded-lg mb-8 shadow-sm">
          <div className="flex items-center space-x-3">
            <div className="p-1 bg-red-500 rounded-full">
              <AlertTriangle size={16} className="text-white" />
            </div>
            <div>
              <h4 className="font-medium">System Error</h4>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent mb-4"></div>
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Loading Analytics</h3>
            <p className="text-gray-600">Fetching fraud detection data...</p>
          </div>
        </div>
      )}

      {/* Tab Content */}
      {!loading && (
        <div className="space-y-8">
          {activeTab === 'overview' && (
            <div className="space-y-8">
              <MetricsCards />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <RiskDistribution />
                <TrendsChart />
              </div>
            </div>
          )}
          
          {activeTab === 'alerts' && <FraudAlertsTable />}
          
          {activeTab === 'trends' && (
            <div className="space-y-8">
              <TrendsChart />
              <RiskDistribution />
            </div>
          )}
          
          {activeTab === 'operators' && <OperatorAnalysis />}
        </div>
      )}
    </div>
  );
};

export default Dashboard;