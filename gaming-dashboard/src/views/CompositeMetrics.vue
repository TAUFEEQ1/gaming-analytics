<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import Avatar from 'primevue/avatar'
import Badge from 'primevue/badge'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Divider from 'primevue/divider'
import CompositeMetricsChart from '@/components/CompositeMetricsChart.vue'
import StatCard from '@/components/StatCard.vue'

const router = useRouter()
const searchQuery = ref('')
const currentMonth = ref('March 2019')
const activeSection = ref('composite')

// DBSCAN Anomaly notifications
const anomalyNotifications = ref([
  {
    id: 1,
    type: 'multivariate',
    severity: 'critical',
    timestamp: new Date(Date.now() - 3600000),
    metrics: {
      stakeZScore: 3.8,
      payoutZScore: 4.1,
      houseNetZScore: -3.2
    },
    message: 'Multi-variate anomaly cluster detected'
  },
  {
    id: 2,
    type: 'multivariate',
    severity: 'high',
    timestamp: new Date(Date.now() - 7200000),
    metrics: {
      stakeZScore: -2.9,
      payoutZScore: 3.5,
      houseNetZScore: 4.2
    },
    message: 'Unusual pattern in composite metrics'
  },
  {
    id: 3,
    type: 'multivariate',
    severity: 'high',
    timestamp: new Date(Date.now() - 10800000),
    metrics: {
      stakeZScore: 3.2,
      payoutZScore: 3.4,
      houseNetZScore: -3.8
    },
    message: 'DBSCAN cluster outlier identified'
  },
  {
    id: 4,
    type: 'multivariate',
    severity: 'medium',
    timestamp: new Date(Date.now() - 14400000),
    metrics: {
      stakeZScore: 2.8,
      payoutZScore: -3.1,
      houseNetZScore: 3.3
    },
    message: 'Composite anomaly detected'
  }
])

const formatTimeAgo = (date: Date) => {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// Composite stats
const stats = ref([
  {
    title: 'DBSCAN Anomalies',
    value: '23',
    subtitle: 'Multi-variate outliers',
    trend: 'up' as 'up' | 'down',
    icon: 'pi-exclamation-triangle'
  },
  {
    title: 'Avg House Net',
    value: '$-42.30',
    subtitle: 'Per round average',
    trend: 'down' as 'up' | 'down',
    icon: 'pi-chart-line'
  },
  {
    title: 'Total Rounds',
    value: '12,547',
    subtitle: 'Rounds analyzed',
    trend: 'up' as 'up' | 'down',
    icon: 'pi-sync'
  },
  {
    title: 'Cluster Confidence',
    value: '94.2%',
    subtitle: 'DBSCAN accuracy',
    trend: 'up' as 'up' | 'down',
    icon: 'pi-check-circle'
  }
])

// DBSCAN Anomaly table data
const dbscanAnomalyData = ref([
  {
    id: 1,
    round: 1542,
    time: new Date('2024-03-28 14:32:15'),
    stake: 2547.80,
    payout: 1850.50,
    houseNet: -697.30,
    stakeZScore: 3.8,
    payoutZScore: 2.1,
    houseNetZScore: -3.2,
    dbAnomaly: 1,
    severity: 'critical'
  },
  {
    id: 2,
    round: 1489,
    time: new Date('2024-03-28 14:15:42'),
    stake: 1125.40,
    payout: 2450.20,
    houseNet: 1324.80,
    stakeZScore: -0.8,
    payoutZScore: 4.2,
    houseNetZScore: 4.5,
    dbAnomaly: 1,
    severity: 'critical'
  },
  {
    id: 3,
    round: 1456,
    time: new Date('2024-03-28 13:58:20'),
    stake: 950.00,
    payout: 780.50,
    houseNet: -169.50,
    stakeZScore: 0.2,
    payoutZScore: -0.5,
    houseNetZScore: 0.3,
    dbAnomaly: 0,
    severity: 'normal'
  },
  {
    id: 4,
    round: 1423,
    time: new Date('2024-03-28 13:45:10'),
    stake: 2350.60,
    payout: 1950.75,
    houseNet: -399.85,
    stakeZScore: 3.5,
    payoutZScore: 3.1,
    houseNetZScore: -2.8,
    dbAnomaly: 1,
    severity: 'high'
  },
  {
    id: 5,
    round: 1398,
    time: new Date('2024-03-28 13:30:55'),
    stake: 1050.00,
    payout: 850.30,
    houseNet: -199.70,
    stakeZScore: 0.5,
    payoutZScore: -0.2,
    houseNetZScore: 0.1,
    dbAnomaly: 0,
    severity: 'normal'
  },
  {
    id: 6,
    round: 1375,
    time: new Date('2024-03-28 13:12:33'),
    stake: 850.25,
    payout: 2200.40,
    houseNet: 1350.15,
    stakeZScore: -0.9,
    payoutZScore: 3.9,
    houseNetZScore: 4.3,
    dbAnomaly: 1,
    severity: 'critical'
  },
  {
    id: 7,
    round: 1342,
    time: new Date('2024-03-28 12:55:18'),
    stake: 2100.60,
    payout: 1750.80,
    houseNet: -349.80,
    stakeZScore: 3.1,
    payoutZScore: 2.5,
    houseNetZScore: -2.5,
    dbAnomaly: 1,
    severity: 'high'
  },
  {
    id: 8,
    round: 1318,
    time: new Date('2024-03-28 12:40:05'),
    stake: 920.50,
    payout: 780.20,
    houseNet: -140.30,
    stakeZScore: 0.1,
    payoutZScore: -0.4,
    houseNetZScore: 0.2,
    dbAnomaly: 0,
    severity: 'normal'
  },
  {
    id: 9,
    round: 1289,
    time: new Date('2024-03-28 12:22:47'),
    stake: 1050.75,
    payout: 1980.50,
    houseNet: 929.75,
    stakeZScore: 0.3,
    payoutZScore: 3.4,
    houseNetZScore: 3.7,
    dbAnomaly: 1,
    severity: 'high'
  },
  {
    id: 10,
    round: 1265,
    time: new Date('2024-03-28 12:05:30'),
    stake: 2450.90,
    payout: 1650.40,
    houseNet: -800.50,
    stakeZScore: 3.7,
    payoutZScore: 1.8,
    houseNetZScore: -3.5,
    dbAnomaly: 1,
    severity: 'critical'
  },
  {
    id: 11,
    round: 1238,
    time: new Date('2024-03-28 11:50:12'),
    stake: 980.30,
    payout: 820.60,
    houseNet: -159.70,
    stakeZScore: 0.2,
    payoutZScore: -0.3,
    houseNetZScore: 0.1,
    dbAnomaly: 0,
    severity: 'normal'
  },
  {
    id: 12,
    round: 1215,
    time: new Date('2024-03-28 11:35:45'),
    stake: 2800.50,
    payout: 1950.25,
    houseNet: -850.25,
    stakeZScore: 4.1,
    payoutZScore: 2.9,
    houseNetZScore: -3.8,
    dbAnomaly: 1,
    severity: 'critical'
  }
])

const formatDateTime = (date: Date) => {
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'danger'
    case 'high': return 'warning'
    case 'medium': return 'info'
    case 'normal': return 'success'
    default: return 'secondary'
  }
}

const getZScoreClass = (zScore: number) => {
  const abs = Math.abs(zScore)
  if (abs >= 3) return 'zscore-critical'
  if (abs >= 2) return 'zscore-high'
  return 'zscore-normal'
}
</script>

<template>
  <div class="dashboard-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-text">DN</span>
      </div>
      <nav class="nav-menu">
        <button 
          :class="['nav-item', { active: activeSection === 'dashboard' }]"
          @click="router.push('/')"
        >
          <i class="pi pi-chart-bar"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'composite' }]"
          @click="activeSection = 'composite'"
        >
          <i class="pi pi-sitemap"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'reports' }]"
          @click="activeSection = 'reports'"
        >
          <i class="pi pi-file"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'alerts' }]"
          @click="activeSection = 'alerts'"
        >
          <i class="pi pi-bell"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'settings' }]"
          @click="activeSection = 'settings'"
        >
          <i class="pi pi-cog"></i>
        </button>
      </nav>
      <div class="nav-footer">
        <button class="nav-item">
          <i class="pi pi-sign-out"></i>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Header -->
      <header class="top-header">
        <div class="header-left">
          <h1 class="page-title">Composite Metrics</h1>
          <h2 class="page-subtitle">Multi-Variate Anomaly Analysis</h2>
        </div>
        <div class="header-center">
          <IconField iconPosition="left">
            <InputIcon class="pi pi-search" />
            <InputText 
              v-model="searchQuery" 
              placeholder="Searching for" 
              class="search-input"
            />
          </IconField>
        </div>
        <div class="header-right">
          <div class="user-profile">
            <div class="user-info">
              <span class="user-name">Mike Edward</span>
              <span class="user-email">edward@mike.com</span>
              <span class="user-plan">Standard Plan</span>
            </div>
            <div class="user-avatar">
              <Avatar 
                label="ME" 
                size="large" 
                shape="circle" 
                class="avatar-circle"
              />
              <Badge value="" severity="success" class="status-badge" />
            </div>
          </div>
        </div>
      </header>

      <!-- Content Area -->
      <div class="content-area">
        <div class="content-scroll">
          <!-- Report Header -->
          <div class="report-header">
            <div class="report-title">
              <span class="report-label">Report {{ currentMonth }}</span>
            </div>
            <div class="legend">
              <span class="legend-item">
                <span class="legend-dot" style="background: #3B82F6;"></span>
                Stake Z-Score
              </span>
              <span class="legend-item">
                <span class="legend-dot" style="background: #10B981;"></span>
                Payout Z-Score
              </span>
              <span class="legend-item">
                <span class="legend-dot" style="background: #F59E0B;"></span>
                House Net Z-Score
              </span>
              <span class="legend-item">
                <span class="legend-dot" style="background: #EF4444;"></span>
                DBSCAN Anomaly
              </span>
            </div>
          </div>

          <!-- Composite Metrics Chart -->
          <Card class="main-chart-card">
            <template #content>
              <CompositeMetricsChart />
            </template>
          </Card>

          <!-- Stats Grid -->
          <div class="stats-grid">
            <StatCard 
              v-for="stat in stats" 
              :key="stat.title"
              :title="stat.title"
              :value="stat.value"
              :subtitle="stat.subtitle"
              :trend="stat.trend"
              :icon="stat.icon"
            />
          </div>

          <!-- DBSCAN Anomalies Table -->
          <Card class="anomalies-table-card">
            <template #title>
              <div class="table-header">
                <div>
                  <i class="pi pi-sitemap"></i>
                  DBSCAN Anomaly Detection
                </div>
                <span class="table-count">{{ dbscanAnomalyData.length }} records</span>
              </div>
            </template>
            <template #content>
              <DataTable 
                :value="dbscanAnomalyData" 
                :paginator="true" 
                :rows="5"
                :rowsPerPageOptions="[5, 10, 20]"
                paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink RowsPerPageDropdown"
                class="anomalies-table"
                stripedRows
              >
                <Column field="round" header="Round" sortable>
                  <template #body="slotProps">
                    <span class="round-cell">#{{ slotProps.data.round }}</span>
                  </template>
                </Column>
                <Column field="time" header="Time" sortable>
                  <template #body="slotProps">
                    <span class="time-cell">{{ formatDateTime(slotProps.data.time) }}</span>
                  </template>
                </Column>
                <Column field="stake" header="Stake" sortable>
                  <template #body="slotProps">
                    <span class="value-cell">${{ slotProps.data.stake.toFixed(2) }}</span>
                  </template>
                </Column>
                <Column field="payout" header="Payout" sortable>
                  <template #body="slotProps">
                    <span class="value-cell">${{ slotProps.data.payout.toFixed(2) }}</span>
                  </template>
                </Column>
                <Column field="houseNet" header="House Net" sortable>
                  <template #body="slotProps">
                    <span :class="['value-cell', slotProps.data.houseNet > 0 ? 'positive' : 'negative']">
                      ${{ slotProps.data.houseNet.toFixed(2) }}
                    </span>
                  </template>
                </Column>
                <Column field="stakeZScore" header="Stake Z" sortable>
                  <template #body="slotProps">
                    <span :class="['zscore-cell', getZScoreClass(slotProps.data.stakeZScore)]">
                      {{ slotProps.data.stakeZScore > 0 ? '+' : '' }}{{ slotProps.data.stakeZScore.toFixed(1) }}
                    </span>
                  </template>
                </Column>
                <Column field="payoutZScore" header="Payout Z" sortable>
                  <template #body="slotProps">
                    <span :class="['zscore-cell', getZScoreClass(slotProps.data.payoutZScore)]">
                      {{ slotProps.data.payoutZScore > 0 ? '+' : '' }}{{ slotProps.data.payoutZScore.toFixed(1) }}
                    </span>
                  </template>
                </Column>
                <Column field="houseNetZScore" header="House Net Z" sortable>
                  <template #body="slotProps">
                    <span :class="['zscore-cell', getZScoreClass(slotProps.data.houseNetZScore)]">
                      {{ slotProps.data.houseNetZScore > 0 ? '+' : '' }}{{ slotProps.data.houseNetZScore.toFixed(1) }}
                    </span>
                  </template>
                </Column>
                <Column field="dbAnomaly" header="DB Anomaly" sortable>
                  <template #body="slotProps">
                    <Tag 
                      :value="slotProps.data.dbAnomaly === 1 ? 'Anomaly' : 'Normal'" 
                      :severity="slotProps.data.dbAnomaly === 1 ? 'danger' : 'success'"
                      :icon="slotProps.data.dbAnomaly === 1 ? 'pi pi-exclamation-triangle' : 'pi pi-check'"
                    />
                  </template>
                </Column>
              </DataTable>
            </template>
          </Card>
        </div>

        <!-- Right Sidebar -->
        <aside class="right-sidebar">
          <div class="notifications-header">
            <h3>DBSCAN Alerts</h3>
            <Badge :value="anomalyNotifications.length" severity="danger" />
          </div>
          
          <div class="notifications-list">
            <div 
              v-for="notification in anomalyNotifications" 
              :key="notification.id"
              :class="['notification-item', notification.severity]"
            >
              <div class="notification-header">
                <div class="notification-type">
                  <i class="pi pi-sitemap"></i>
                  <span class="type-label">Multi-Variate</span>
                </div>
                <span class="notification-time">{{ formatTimeAgo(notification.timestamp) }}</span>
              </div>
              
              <div class="notification-body">
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-details">
                  <div class="detail-row">
                    <span class="detail-label">Stake Z-Score:</span>
                    <span :class="['detail-value', 'z-score', { negative: notification.metrics.stakeZScore < 0 }]">
                      {{ notification.metrics.stakeZScore > 0 ? '+' : '' }}{{ notification.metrics.stakeZScore.toFixed(1) }}
                    </span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Payout Z-Score:</span>
                    <span :class="['detail-value', 'z-score', { negative: notification.metrics.payoutZScore < 0 }]">
                      {{ notification.metrics.payoutZScore > 0 ? '+' : '' }}{{ notification.metrics.payoutZScore.toFixed(1) }}
                    </span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">House Net Z:</span>
                    <span :class="['detail-value', 'z-score', { negative: notification.metrics.houseNetZScore < 0 }]">
                      {{ notification.metrics.houseNetZScore > 0 ? '+' : '' }}{{ notification.metrics.houseNetZScore.toFixed(1) }}
                    </span>
                  </div>
                </div>
              </div>
              
              <Divider />
              <div class="notification-footer">
                <Button label="View Details" link size="small" severity="info" />
                <Button icon="pi pi-times" text rounded size="small" severity="secondary" />
              </div>
            </div>
          </div>
        </aside>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  height: 100vh;
  background: #F8FAFC;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 84px;
  background: white;
  border-right: 1px solid #E2E8F0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem 0;
  flex-shrink: 0;
}

.logo {
  margin-bottom: 3rem;
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 700;
  color: #5B8DEE;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex: 1;
}

.nav-item {
  width: 48px;
  height: 48px;
  border: none;
  background: transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94A3B8;
  font-size: 1.25rem;
  position: relative;
}

.nav-item:hover {
  background: #F1F5F9;
  color: #5B8DEE;
}

.nav-item.active {
  color: #5B8DEE;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: -1.5rem;
  width: 4px;
  height: 100%;
  background: #5B8DEE;
  border-radius: 0 4px 4px 0;
}

.nav-footer {
  margin-top: auto;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.top-header {
  background: white;
  padding: 2rem 2.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #E2E8F0;
  gap: 2rem;
}

.header-left {
  flex-shrink: 0;
}

.page-title {
  font-size: 0.875rem;
  color: #94A3B8;
  font-weight: 400;
  margin: 0 0 0.25rem 0;
}

.page-subtitle {
  font-size: 2rem;
  color: #1E293B;
  font-weight: 300;
  margin: 0;
}

.header-center {
  flex: 1;
  max-width: 400px;
}

.header-center :deep(.p-iconfield) {
  width: 100%;
}

.search-input {
  width: 100%;
  border-radius: 12px;
  font-size: 0.875rem;
}

.header-right {
  flex-shrink: 0;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info {
  text-align: right;
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: #1E293B;
  font-size: 0.875rem;
}

.user-email {
  font-size: 0.75rem;
  color: #94A3B8;
}

.user-plan {
  font-size: 0.75rem;
  color: #64748B;
  margin-top: 0.25rem;
}

.user-avatar {
  position: relative;
}

.avatar-circle {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.status-badge {
  position: absolute;
  bottom: 2px;
  right: 2px;
  min-width: 12px;
  height: 12px;
  border: 2px solid white;
}

/* Content Area */
.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2.5rem;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.report-label {
  font-size: 0.875rem;
  color: #64748B;
  font-weight: 500;
}

.legend {
  display: flex;
  gap: 2rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: #64748B;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.main-chart-card {
  margin-bottom: 2rem;
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.main-chart-card :deep(.p-card-body) {
  padding: 1.5rem;
}

.main-chart-card :deep(.p-card-content) {
  padding: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* Anomalies Table */
.anomalies-table-card {
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.anomalies-table-card :deep(.p-card-title) {
  padding: 1.5rem 1.5rem 0;
  margin: 0;
}

.anomalies-table-card :deep(.p-card-content) {
  padding: 1.5rem;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 1.125rem;
  color: #1E293B;
  font-weight: 600;
}

.table-header i {
  margin-right: 0.5rem;
  color: #F59E0B;
}

.table-count {
  font-size: 0.875rem;
  color: #64748B;
  font-weight: 500;
  background: #F1F5F9;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
}

.anomalies-table :deep(.p-datatable) {
  font-size: 0.875rem;
}

.anomalies-table :deep(.p-datatable-thead > tr > th) {
  background: #F8FAFC;
  color: #64748B;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 2px solid #E2E8F0;
  padding: 1rem 0.75rem;
}

.anomalies-table :deep(.p-datatable-tbody > tr > td) {
  padding: 0.875rem 0.75rem;
  border-bottom: 1px solid #F1F5F9;
}

.anomalies-table :deep(.p-datatable-tbody > tr:hover) {
  background: #F8FAFC;
}

.anomalies-table :deep(.p-paginator) {
  background: transparent;
  border-top: 1px solid #E2E8F0;
  padding: 1rem 0.5rem;
}

.anomalies-table :deep(.p-paginator .p-paginator-pages .p-paginator-page.p-highlight) {
  background: #5B8DEE;
  color: white;
}

.round-cell {
  font-weight: 700;
  color: #5B8DEE;
  font-family: 'Monaco', 'Courier New', monospace;
}

.time-cell {
  font-size: 0.8125rem;
  color: #64748B;
  font-family: 'Monaco', 'Courier New', monospace;
}

.value-cell {
  font-weight: 500;
  color: #1E293B;
}

.value-cell.positive {
  color: #10B981;
  font-weight: 600;
}

.value-cell.negative {
  color: #EF4444;
  font-weight: 600;
}

.zscore-cell {
  font-weight: 600;
  font-family: 'Monaco', 'Courier New', monospace;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  display: inline-block;
  min-width: 50px;
  text-align: center;
}

.zscore-cell.zscore-critical {
  background: #FEE2E2;
  color: #DC2626;
}

.zscore-cell.zscore-high {
  background: #FEF3C7;
  color: #D97706;
}

.zscore-cell.zscore-normal {
  background: #F1F5F9;
  color: #64748B;
}

/* Right Sidebar */
.right-sidebar {
  width: 360px;
  background: #F8FAFC;
  padding: 1.5rem;
  border-left: 1px solid #E2E8F0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  flex-shrink: 0;
}

.notifications-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 1rem;
  border-bottom: 1px solid #E2E8F0;
}

.notifications-header h3 {
  font-size: 1.125rem;
  color: #1E293B;
  margin: 0;
  font-weight: 600;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.notification-item {
  background: white;
  border-radius: 12px;
  padding: 1rem;
  border-left: 4px solid transparent;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s;
}

.notification-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateX(-2px);
}

.notification-item.critical {
  border-left-color: #DC2626;
  background: linear-gradient(to right, #FEF2F2 0%, white 10%);
}

.notification-item.high {
  border-left-color: #F59E0B;
  background: linear-gradient(to right, #FFFBEB 0%, white 10%);
}

.notification-item.medium {
  border-left-color: #3B82F6;
  background: linear-gradient(to right, #EFF6FF 0%, white 10%);
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.notification-type {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  color: #1E293B;
}

.notification-type i {
  font-size: 0.75rem;
  color: #64748B;
}

.notification-time {
  font-size: 0.75rem;
  color: #94A3B8;
}

.notification-body {
  margin-bottom: 0.75rem;
}

.notification-message {
  font-size: 0.875rem;
  color: #475569;
  margin-bottom: 0.75rem;
  font-weight: 500;
}

.notification-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: #F8FAFC;
  padding: 0.75rem;
  border-radius: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
}

.detail-label {
  color: #64748B;
  font-weight: 500;
}

.detail-value {
  color: #1E293B;
  font-weight: 600;
}

.detail-value.z-score {
  color: #EF4444;
}

.detail-value.z-score.negative {
  color: #3B82F6;
}

.notification-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0;
}
</style>
