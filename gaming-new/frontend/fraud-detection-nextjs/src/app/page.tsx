'use client'

import { useState } from 'react'
import { RefreshCw, AlertTriangle, Shield, TrendingUp, Activity, Users, DollarSign, Target } from 'lucide-react'
import MetricsCards from '@/components/MetricsCards'
import FraudAlertsTable from '@/components/FraudAlertsTable'
import TrendsChart from '@/components/TrendsChart'
import RiskDistribution from '@/components/RiskDistribution'
import OperatorAnalysis from '@/components/OperatorAnalysis'

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'trends' | 'operators'>('overview')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Shield, color: 'from-blue-500 to-cyan-500' },
    { id: 'alerts', label: 'Fraud Alerts', icon: AlertTriangle, color: 'from-red-500 to-orange-500' },
    { id: 'trends', label: 'Trends Analysis', icon: TrendingUp, color: 'from-green-500 to-emerald-500' },
    { id: 'operators', label: 'Operator Profiles', icon: Users, color: 'from-purple-500 to-violet-500' }
  ]

  const refreshData = async () => {
    setLoading(true)
    // Simulate API call
    setTimeout(() => setLoading(false), 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white shadow-2xl">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                Gaming Fraud Detection System
              </h1>
              <p className="text-blue-200 mt-2 text-lg">Government Regulatory Dashboard</p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Header Controls */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex space-x-2 bg-white/80 backdrop-blur-sm rounded-2xl p-2 shadow-xl border border-white/50">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-3 px-6 py-4 rounded-xl font-semibold transition-all duration-300 relative overflow-hidden group ${
                    activeTab === tab.id
                      ? `bg-gradient-to-r ${tab.color} text-white shadow-lg transform scale-105`
                      : 'text-gray-600 hover:bg-white/70 hover:text-gray-900 hover:shadow-md'
                  }`}
                >
                  <Icon size={20} className={activeTab === tab.id ? 'animate-pulse' : ''} />
                  <span className="relative z-10">{tab.label}</span>
                  {activeTab !== tab.id && (
                    <div className={`absolute inset-0 bg-gradient-to-r ${tab.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                  )}
                </button>
              )
            })}
          </div>
          
          <button
            onClick={refreshData}
            disabled={loading}
            className="flex items-center space-x-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold shadow-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 hover:shadow-xl"
          >
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Data</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-gradient-to-r from-red-50 to-red-100 border-l-4 border-red-500 text-red-700 px-6 py-4 rounded-xl mb-8 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-500 rounded-full">
                <AlertTriangle size={18} className="text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-lg">System Error</h4>
                <span className="text-sm">{error}</span>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="relative">
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200"></div>
              <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-600 border-t-transparent absolute top-0"></div>
            </div>
            <div className="text-center mt-6">
              <h3 className="text-xl font-bold text-gray-900 mb-2">Loading Analytics</h3>
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
      </main>
    </div>
  )
}
