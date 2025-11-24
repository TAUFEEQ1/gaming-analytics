<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
import Calendar from 'primevue/calendar'
import Dialog from 'primevue/dialog'
import CompositeMetricsChart from '@/components/CompositeMetricsChart.vue'
import StatCard from '@/components/StatCard.vue'
import { apiService } from '@/services/api'
import type { DBSCANNotification, DBSCANTableRecord, CompositeStats, RoundDetail } from '@/services/api'

const router = useRouter()
const searchQuery = ref('')
const currentMonth = ref('March 2019')
const activeSection = ref('composite')

// Date filter state
const dateRange = ref<Date[] | null>(null)
const startDate = ref<string | undefined>(undefined)
const endDate = ref<string | undefined>(undefined)

// DBSCAN Anomaly notifications
const anomalyNotifications = ref<DBSCANNotification[]>([])

// Composite stats
const stats = ref<Array<{
  title: string
  value: string
  subtitle: string
  trend: 'up' | 'down'
  icon: string
}>>([])

// DBSCAN Anomaly table data
const dbscanAnomalyData = ref<DBSCANTableRecord[]>([])

// Round details modal
const showRoundModal = ref(false)
const selectedRound = ref<RoundDetail | null>(null)
const loadingRoundDetails = ref(false)

const formatTimeAgo = (timestamp: string) => {
  const date = new Date(timestamp)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// Fetch data function with date filters
const fetchData = async () => {
  try {
    // Fetch notifications
    const notifications = await apiService.getDBSCANNotifications(5, startDate.value, endDate.value)
    anomalyNotifications.value = notifications

    // Fetch stats
    const compositeStats: CompositeStats = await apiService.getCompositeStats(startDate.value, endDate.value)
    stats.value = [
      {
        title: 'DBSCAN Anomalies',
        value: compositeStats.dbscanAnomalies.toString(),
        subtitle: 'Multi-variate outliers',
        trend: 'up',
        icon: 'pi-exclamation-triangle'
      },
      {
        title: 'Avg House Net',
        value: `$${compositeStats.avgHouseNet.toFixed(2)}`,
        subtitle: 'Per round average',
        trend: compositeStats.avgHouseNet < 0 ? 'down' : 'up',
        icon: 'pi-chart-line'
      },
      {
        title: 'Total Rounds',
        value: compositeStats.totalRounds.toLocaleString(),
        subtitle: 'Rounds analyzed',
        trend: 'up',
        icon: 'pi-sync'
      },
      {
        title: 'Cluster Count',
        value: compositeStats.clusterCount.toString(),
        subtitle: 'DBSCAN clusters',
        trend: 'up',
        icon: 'pi-check-circle'
      }
    ]

    // Fetch table data (anomalies only)
    const tableData = await apiService.getDBSCANTable(12, true, startDate.value, endDate.value)
    dbscanAnomalyData.value = tableData
  } catch (error) {
    console.error('Failed to fetch composite data:', error)
  }
}

// Handle date range change
const onDateRangeChange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    startDate.value = dateRange.value[0]?.toISOString()
    endDate.value = dateRange.value[1]?.toISOString()
  } else {
    startDate.value = undefined
    endDate.value = undefined
  }
  fetchData()
}

// Clear filters
const clearFilters = () => {
  dateRange.value = null
  startDate.value = undefined
  endDate.value = undefined
  fetchData()
}

// Fetch data on mount
onMounted(async () => {
  await fetchData()
})

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
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

const viewRoundDetails = async (roundId: number) => {
  loadingRoundDetails.value = true
  showRoundModal.value = true
  try {
    selectedRound.value = await apiService.getRoundDetails(roundId)
  } catch (error) {
    console.error('Failed to fetch round details:', error)
  } finally {
    loadingRoundDetails.value = false
  }
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
          <div class="filter-controls">
            <Calendar 
              v-model="dateRange" 
              selectionMode="range" 
              :manualInput="false"
              dateFormat="M dd, yy"
              placeholder="Select date range"
              @date-select="onDateRangeChange"
              showIcon
              :showButtonBar="true"
              class="date-filter"
            />
            <Button 
              v-if="dateRange" 
              icon="pi pi-times" 
              @click="clearFilters" 
              severity="secondary"
              text
              rounded
              aria-label="Clear filters"
            />
          </div>
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
              <CompositeMetricsChart :startDate="startDate" :endDate="endDate" />
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
                <Column header="Actions">
                  <template #body="slotProps">
                    <Button 
                      icon="pi pi-eye" 
                      @click="viewRoundDetails(slotProps.data.id)"
                      text
                      rounded
                      severity="info"
                      size="small"
                      v-tooltip.top="'View Details'"
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

    <!-- Round Details Modal -->
    <Dialog 
      v-model:visible="showRoundModal" 
      modal 
      header="Round Details"
      :style="{ width: '600px' }"
      :draggable="false"
    >
      <div v-if="loadingRoundDetails" class="loading-state">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        <p>Loading round details...</p>
      </div>
      <div v-else-if="selectedRound" class="round-details">
        <div class="detail-section">
          <h4>Round Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Round ID:</span>
              <span class="detail-value">#{{ selectedRound.ID }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Timestamp:</span>
              <span class="detail-value">{{ formatDateTime(selectedRound.time) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Moderator:</span>
              <span class="detail-value">{{ selectedRound.moderator === 1 ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>

        <Divider />

        <div class="detail-section">
          <h4>Game Metrics</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Gamers:</span>
              <span class="detail-value highlight">{{ selectedRound.gamers }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Skins:</span>
              <span class="detail-value highlight">{{ selectedRound.skins }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Ticks:</span>
              <span class="detail-value">${{ selectedRound.ticks.toFixed(2) }}</span>
            </div>
          </div>
        </div>

        <Divider />

        <div class="detail-section">
          <h4>Financial Metrics</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Money (Stake):</span>
              <span class="detail-value money">${{ selectedRound.money.toFixed(2) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">People Win:</span>
              <span class="detail-value win">${{ selectedRound.peopleWin.toFixed(2) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">People Lost:</span>
              <span class="detail-value loss">${{ selectedRound.peopleLost.toFixed(2) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Outpay:</span>
              <span class="detail-value">${{ selectedRound.outpay.toFixed(2) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">House Net:</span>
              <span :class="['detail-value', 'house-net', (selectedRound.peopleWin - selectedRound.peopleLost) > 0 ? 'positive' : 'negative']">
                ${{ (selectedRound.peopleWin - selectedRound.peopleLost).toFixed(2) }}
              </span>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <Button label="Close" icon="pi pi-times" @click="showRoundModal = false" text />
      </template>
    </Dialog>
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
  max-width: 500px;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
}

.date-filter {
  flex: 1;
}

.date-filter :deep(.p-calendar) {
  width: 100%;
}

.date-filter :deep(.p-inputtext) {
  border-radius: 12px;
  font-size: 0.875rem;
  padding: 0.625rem 1rem;
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

/* Round Details Modal */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
  color: #64748B;
}

.round-details {
  padding: 1rem 0;
}

.detail-section {
  margin-bottom: 1rem;
}

.detail-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #1E293B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-section h4::before {
  content: '';
  width: 4px;
  height: 1rem;
  background: #5B8DEE;
  border-radius: 2px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: #F8FAFC;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.detail-label {
  font-size: 0.75rem;
  color: #64748B;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-value {
  font-size: 1rem;
  color: #1E293B;
  font-weight: 600;
}

.detail-value.highlight {
  color: #5B8DEE;
  font-size: 1.25rem;
}

.detail-value.money {
  color: #3B82F6;
  font-family: 'Monaco', 'Courier New', monospace;
}

.detail-value.win {
  color: #10B981;
  font-family: 'Monaco', 'Courier New', monospace;
}

.detail-value.loss {
  color: #EF4444;
  font-family: 'Monaco', 'Courier New', monospace;
}

.detail-value.house-net {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 1.125rem;
}

.detail-value.house-net.positive {
  color: #10B981;
}

.detail-value.house-net.negative {
  color: #EF4444;
}
</style>
