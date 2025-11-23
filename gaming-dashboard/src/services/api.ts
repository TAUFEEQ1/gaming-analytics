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
}

export const apiService = new ApiService()
