import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { fetchFraudDetection, fetchRiskMetrics, fetchOperatorProfile, fetchTrends } from '../services/api';

interface FraudAlert {
  transaction_id: string;
  operator_id: string;
  risk_score: number;
  anomaly_type: string;
  timestamp: string;
  details: Record<string, any>;
}

interface RiskMetrics {
  total_transactions: number;
  high_risk_transactions: number;
  risk_percentage: number;
  total_stakes: number;
  total_payouts: number;
  total_ggr: number;
  operators_count: number;
  avg_win_rate: number;
  suspicious_operators: number;
}

interface TrendData {
  date: string;
  total_stakes: number;
  total_payouts: number;
  ggr: number;
  total_bets: number;
  active_operators: number;
}

interface FraudContextType {
  alerts: FraudAlert[];
  metrics: RiskMetrics | null;
  trends: TrendData[];
  loading: boolean;
  error: string | null;
  refreshData: () => void;
  getOperatorProfile: (operatorId: string) => Promise<any>;
}

const FraudContext = createContext<FraudContextType | undefined>(undefined);

interface FraudProviderProps {
  children: ReactNode;
}

export const FraudProvider: React.FC<FraudProviderProps> = ({ children }) => {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  const [trends, setTrends] = useState<TrendData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [alertsData, metricsData, trendsData] = await Promise.all([
        fetchFraudDetection(),
        fetchRiskMetrics(),
        fetchTrends()
      ]);
      
      setAlerts(alertsData);
      setMetrics(metricsData);
      setTrends(trendsData.trends || []);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data');
      console.error('Failed to fetch fraud data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getOperatorProfile = async (operatorId: string) => {
    try {
      return await fetchOperatorProfile(operatorId);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch operator profile');
      throw err;
    }
  };

  useEffect(() => {
    refreshData();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(refreshData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const contextValue: FraudContextType = {
    alerts,
    metrics,
    trends,
    loading,
    error,
    refreshData,
    getOperatorProfile
  };

  return (
    <FraudContext.Provider value={contextValue}>
      {children}
    </FraudContext.Provider>
  );
};

export const useFraud = (): FraudContextType => {
  const context = useContext(FraudContext);
  if (context === undefined) {
    throw new Error('useFraud must be used within a FraudProvider');
  }
  return context;
};