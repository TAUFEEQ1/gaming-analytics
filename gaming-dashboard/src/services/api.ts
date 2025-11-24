const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface Anomaly {
  x: string | Date
  y: number
  index: number
  zScore: number
}

export interface ChartBounds {
  upper: number[]
  lower: number[]
  mean: number[]
}

export interface ChartData {
  timestamps: string[]
  values: number[]
  anomalies: Anomaly[]
  bounds: ChartBounds
}

export interface StakesPayoutsResponse {
  chartType: 'stakes' | 'payouts'
  data: ChartData
  mean: number
  std: number
}

export interface Stats {
  totalRecords: number
  totalStakes: number
  totalPayouts: number
  averageStake: number
  averagePayout: number
  stakeAnomalies: number
  payoutAnomalies: number
}

export interface AnomalyRecord {
  time: string
  stake: number
  payout: number
  stake_global_z: number
  payout_global_z: number
  isStakeAnomaly: boolean
  isPayoutAnomaly: boolean
}

export interface AnomaliesResponse {
  anomalies: AnomalyRecord[]
  total: number
  stakeAnomalies: number
  payoutAnomalies: number
}

export interface Notification {
  id: number
  timestamp: string
  anomaly_type: string
  severity: string
  value: number
  z_score: number
  message: string
  is_read: boolean
  created_at: string
}

export interface NotificationsResponse {
  notifications: Notification[]
  total: number
  unread: number
}

// Composite Metrics Types
export interface CompositeChartData {
  timestamps: string[]
  rounds: number[]
  stakeZScores: number[]
  payoutZScores: number[]
  houseNetZScores: number[]
  dbAnomalies: number[]
  anomalyIndices: number[]
}

export interface DBSCANNotification {
  id: number
  type: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  timestamp: string
  metrics: {
    stakeZScore: number
    payoutZScore: number
    houseNetZScore: number
  }
  message: string
}

export interface DBSCANTableRecord {
  id: number
  round: number
  time: string
  stake: number
  payout: number
  houseNet: number
  stakeZScore: number
  payoutZScore: number
  houseNetZScore: number
  dbAnomaly: number
  dbCluster: number
  severity: string
  gamers: number
  skins: number
}

export interface CompositeStats {
  dbscanAnomalies: number
  avgHouseNet: number
  totalRounds: number
  normalPoints: number
  clusterCount: number
}

class ApiService {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async getStakesPayoutsChart(
    chartType: 'stakes' | 'payouts',
    startDate?: string,
    endDate?: string
  ): Promise<StakesPayoutsResponse> {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const queryString = params.toString()
    
    const response = await fetch(
      `${this.baseUrl}/api/analytics/stakes-payouts/${chartType}${queryString ? `?${queryString}` : ''}`
    )
    if (!response.ok) {
      throw new Error(`Failed to fetch ${chartType} data`)
    }
    return response.json()
  }

  async getStats(): Promise<Stats> {
    const response = await fetch(`${this.baseUrl}/api/stats/summary`)
    if (!response.ok) {
      throw new Error('Failed to fetch stats')
    }
    return response.json()
  }

  async getAnomalies(
    threshold: number = 3,
    limit: number = 100
  ): Promise<AnomaliesResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/anomalies?threshold=${threshold}&limit=${limit}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch anomalies')
    }
    return response.json()
  }

  async getNotifications(
    unreadOnly: boolean = false,
    limit: number = 20,
    offset: number = 0
  ): Promise<NotificationsResponse> {
    const params = new URLSearchParams()
    if (unreadOnly) params.append('unread_only', 'true')
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())
    
    const response = await fetch(
      `${this.baseUrl}/api/notifications/?${params.toString()}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch notifications')
    }
    return response.json()
  }

  async markNotificationRead(id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/notifications/${id}/read`,
      { method: 'PATCH' }
    )
    if (!response.ok) {
      throw new Error('Failed to mark notification as read')
    }
  }

  async markAllNotificationsRead(): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/notifications/mark-all-read`,
      { method: 'PATCH' }
    )
    if (!response.ok) {
      throw new Error('Failed to mark all notifications as read')
    }
  }

  async deleteNotification(id: number): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/notifications/${id}`,
      { method: 'DELETE' }
    )
    if (!response.ok) {
      throw new Error('Failed to delete notification')
    }
  }

  // Composite Metrics APIs
  async getCompositeChartData(
    limit: number = 100,
    startDate?: string,
    endDate?: string
  ): Promise<CompositeChartData> {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    const response = await fetch(
      `${this.baseUrl}/api/composite/chart-data?${params.toString()}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch composite chart data')
    }
    return response.json()
  }

  async getDBSCANNotifications(
    limit: number = 5,
    startDate?: string,
    endDate?: string
  ): Promise<DBSCANNotification[]> {
    const params = new URLSearchParams({ limit: limit.toString() })
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    const response = await fetch(
      `${this.baseUrl}/api/composite/notifications?${params.toString()}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch DBSCAN notifications')
    }
    return response.json()
  }

  async getDBSCANTable(
    limit: number = 20,
    showAnomaliesOnly: boolean = false,
    startDate?: string,
    endDate?: string
  ): Promise<DBSCANTableRecord[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      show_anomalies_only: showAnomaliesOnly.toString()
    })
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    
    const response = await fetch(
      `${this.baseUrl}/api/composite/table?${params.toString()}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch DBSCAN table data')
    }
    return response.json()
  }

  async getCompositeStats(
    startDate?: string,
    endDate?: string
  ): Promise<CompositeStats> {
    const params = new URLSearchParams()
    if (startDate) params.append('start_date', startDate)
    if (endDate) params.append('end_date', endDate)
    const queryString = params.toString()
    
    const response = await fetch(
      `${this.baseUrl}/api/composite/stats${queryString ? `?${queryString}` : ''}`
    )
    if (!response.ok) {
      throw new Error('Failed to fetch composite stats')
    }
    return response.json()
  }
}

export const apiService = new ApiService()
