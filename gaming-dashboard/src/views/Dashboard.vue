<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
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
import StakesPayoutsChart from '@/components/StakesPayoutsChart.vue'
import StatCard from '@/components/StatCard.vue'
import { apiService, type Notification } from '@/services/api'

const router = useRouter()
const searchQuery = ref('')
const currentMonth = ref('March 2019')
const activeSection = ref('dashboard')
const activeChart = ref<'stakes' | 'payouts'>('stakes')
const dateRange = ref<Date[] | null>(null)

// API Data
const stakesData = ref<any>(null)
const payoutsData = ref<any>(null)
const loading = ref(false)
const notifications = ref<Notification[]>([])
const unreadCount = ref(0)
const notificationsLoading = ref(false)

// Fetch data from API
const fetchChartData = async () => {
  loading.value = true
  try {
    const startDate = dateRange.value?.[0] ? dateRange.value[0].toISOString().split('T')[0] : undefined
    const endDate = dateRange.value?.[1] ? dateRange.value[1].toISOString().split('T')[0] : undefined
    
    const [stakes, payouts] = await Promise.all([
      apiService.getStakesPayoutsChart('stakes', startDate, endDate),
      apiService.getStakesPayoutsChart('payouts', startDate, endDate)
    ])
    stakesData.value = stakes
    payoutsData.value = payouts
  } catch (error) {
    console.error('Error fetching chart data:', error)
  } finally {
    loading.value = false
  }
}

// Fetch notifications from API
const fetchNotifications = async () => {
  notificationsLoading.value = true
  try {
    const response = await apiService.getNotifications(true, 20, 0) // Changed to true to fetch only unread
    notifications.value = response.notifications
    unreadCount.value = response.unread
  } catch (error) {
    console.error('Error fetching notifications:', error)
  } finally {
    notificationsLoading.value = false
  }
}

// Mark notification as read
const markAsRead = async (id: number) => {
  try {
    await apiService.markNotificationRead(id)
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  } catch (error) {
    console.error('Error marking notification as read:', error)
  }
}

// Delete notification
const deleteNotification = async (id: number) => {
  try {
    await apiService.deleteNotification(id)
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      const wasUnread = !notifications.value[index].is_read
      notifications.value.splice(index, 1)
      if (wasUnread) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    }
  } catch (error) {
    console.error('Error deleting notification:', error)
  }
}

// Mark all as read
const markAllAsRead = async () => {
  try {
    await apiService.markAllNotificationsRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    console.error('Error marking all notifications as read:', error)
  }
}

onMounted(() => {
  fetchChartData()
  fetchNotifications()
  
  // Poll for new notifications every 30 seconds
  setInterval(fetchNotifications, 30000)
})

// Watch for date range changes
watch(dateRange, () => {
  fetchChartData()
})

// Format notification timestamp
const formatNotificationTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// Get severity color for notification
const getNotificationSeverity = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical': return 'critical'
    case 'high': return 'high'
    case 'medium': return 'medium'
    default: return 'medium'
  }
}

// Compute anomaly notifications from real data
const anomalyNotifications = computed(() => {
  const notifications: any[] = []
  
  if (stakesData.value?.data?.anomalies) {
    stakesData.value.data.anomalies.slice(0, 3).forEach((anomaly: any, index: number) => {
      notifications.push({
        id: `stakes-${index}`,
        type: 'stakes',
        severity: Math.abs(anomaly.zScore) > 4 ? 'critical' : Math.abs(anomaly.zScore) > 3.5 ? 'high' : 'medium',
        timestamp: new Date(anomaly.x),
        value: anomaly.y,
        normalRange: `${(stakesData.value.mean - 3 * stakesData.value.std).toFixed(0)}-${(stakesData.value.mean + 3 * stakesData.value.std).toFixed(0)}`,
        zScore: anomaly.zScore,
        message: anomaly.zScore > 0 ? 'Unusual spike detected' : 'Unusual drop in stakes'
      })
    })
  }
  
  if (payoutsData.value?.data?.anomalies) {
    payoutsData.value.data.anomalies.slice(0, 3).forEach((anomaly: any, index: number) => {
      notifications.push({
        id: `payouts-${index}`,
        type: 'payouts',
        severity: Math.abs(anomaly.zScore) > 4 ? 'critical' : Math.abs(anomaly.zScore) > 3.5 ? 'high' : 'medium',
        timestamp: new Date(anomaly.x),
        value: anomaly.y,
        normalRange: `${(payoutsData.value.mean - 3 * payoutsData.value.std).toFixed(0)}-${(payoutsData.value.mean + 3 * payoutsData.value.std).toFixed(0)}`,
        zScore: anomaly.zScore,
        message: anomaly.zScore > 0 ? 'Abnormal payout pattern' : 'Unusual drop in payouts'
      })
    })
  }
  
  return notifications.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
})

const formatTimeAgo = (date: Date) => {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

// Compute stats from real data
const stats = computed(() => [
  {
    title: 'Stakes Anomalies',
    value: stakesData.value?.data?.anomalies?.length?.toString() || '0',
    subtitle: 'Z-score > 3 detected',
    trend: 'up' as const,
    icon: 'pi-exclamation-triangle'
  },
  {
    title: 'Payout Anomalies',
    value: payoutsData.value?.data?.anomalies?.length?.toString() || '0',
    subtitle: 'Unusual payout patterns',
    trend: 'down' as const,
    icon: 'pi-exclamation-circle'
  },
  {
    title: 'Average Stake',
    value: stakesData.value ? `$${stakesData.value.mean.toFixed(2)}` : '$0.00',
    subtitle: `Std Dev: $${stakesData.value?.std?.toFixed(2) || '0.00'}`,
    trend: 'up' as const,
    icon: 'pi-dollar'
  },
  {
    title: 'Average Payout',
    value: payoutsData.value ? `$${payoutsData.value.mean.toFixed(2)}` : '$0.00',
    subtitle: `Std Dev: $${payoutsData.value?.std?.toFixed(2) || '0.00'}`,
    trend: 'up' as const,
    icon: 'pi-chart-line'
  }
])

// Compute anomaly table data from real API data
const anomalyTableData = computed(() => {
  const tableData: any[] = []
  
  if (stakesData.value && payoutsData.value) {
    // Add all stake anomalies
    stakesData.value.data.anomalies.forEach((anomaly: any) => {
      tableData.push({
        time: new Date(anomaly.x),
        stake: anomaly.y,
        payout: payoutsData.value.mean, // Use average payout for display
        gamers: Math.floor(Math.random() * 40) + 10, // Mock data
        skins: Math.floor(Math.random() * 10) + 3,    // Mock data
        peopleWin: Math.floor(Math.random() * 15) + 5, // Mock data
        peopleLost: Math.floor(Math.random() * 30) + 10, // Mock data
        anomalyType: 'stake',
        severity: Math.abs(anomaly.zScore) > 4 ? 'critical' : Math.abs(anomaly.zScore) > 3.5 ? 'high' : 'medium'
      })
    })
    
    // Add all payout anomalies
    payoutsData.value.data.anomalies.forEach((anomaly: any) => {
      tableData.push({
        time: new Date(anomaly.x),
        stake: stakesData.value.mean, // Use average stake for display
        payout: anomaly.y,
        gamers: Math.floor(Math.random() * 40) + 10, // Mock data
        skins: Math.floor(Math.random() * 10) + 3,    // Mock data
        peopleWin: Math.floor(Math.random() * 15) + 5, // Mock data
        peopleLost: Math.floor(Math.random() * 30) + 10, // Mock data
        anomalyType: 'payout',
        severity: Math.abs(anomaly.zScore) > 4 ? 'critical' : Math.abs(anomaly.zScore) > 3.5 ? 'high' : 'medium'
      })
    })
    
    // Sort by time descending
    tableData.sort((a, b) => b.time.getTime() - a.time.getTime())
  }
  
  return tableData
})

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
    default: return 'secondary'
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
          @click="activeSection = 'dashboard'"
        >
          <i class="pi pi-chart-bar"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'composite' }]"
          @click="router.push('/composite')"
        >
          <i class="pi pi-sitemap"></i>
        </button>
        <button 
          :class="['nav-item', { active: activeSection === 'analytics' }]"
          @click="activeSection = 'analytics'"
        >
          <i class="pi pi-briefcase"></i>
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
          <Badge 
            v-if="unreadCount > 0" 
            :value="unreadCount" 
            severity="danger" 
            class="notification-badge"
          />
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
          <h1 class="page-title">Dashboard</h1>
          <h2 class="page-subtitle">Stakes & Payouts Anomaly Detection</h2>
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
            <div class="date-range-filter">
              <Calendar 
                v-model="dateRange" 
                selectionMode="range" 
                :manualInput="false"
                dateFormat="yy-mm-dd"
                placeholder="Select Date Range"
                showIcon
                iconDisplay="input"
                class="date-range-calendar"
              />
              <Button 
                v-if="dateRange" 
                icon="pi pi-times" 
                @click="dateRange = null"
                text
                rounded
                severity="secondary"
                size="small"
                title="Clear date filter"
              />
            </div>
            <div class="chart-controls">
              <div class="chart-tabs">
                <Button 
                  label="Stakes"
                  icon="pi pi-circle-fill"
                  :outlined="activeChart !== 'stakes'"
                  :severity="activeChart === 'stakes' ? 'info' : 'secondary'"
                  @click="activeChart = 'stakes'"
                  class="chart-tab-btn"
                  size="small"
                />
                <Button 
                  label="Payouts"
                  icon="pi pi-circle-fill"
                  :outlined="activeChart !== 'payouts'"
                  :severity="activeChart === 'payouts' ? 'success' : 'secondary'"
                  @click="activeChart = 'payouts'"
                  class="chart-tab-btn"
                  size="small"
                />
              </div>
              <div class="legend-info">
                <span class="legend-item">
                  <span class="legend-dot" style="background: #EF4444;"></span>
                  Anomalies Detected
                </span>
              </div>
            </div>
          </div>

          <!-- Main Chart -->
          <Card class="main-chart-card">
            <template #content>
              <StakesPayoutsChart 
                :chart-type="activeChart" 
                :start-date="dateRange?.[0]?.toISOString().split('T')[0]"
                :end-date="dateRange?.[1]?.toISOString().split('T')[0]"
              />
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

          <!-- Anomalies Table -->
          <Card class="anomalies-table-card">
            <template #title>
              <div class="table-header">
                <div>
                  <i class="pi pi-exclamation-circle"></i>
                  Detected Anomalies
                </div>
                <span class="table-count">{{ anomalyTableData.length }} records</span>
              </div>
            </template>
            <template #content>
              <DataTable 
                :value="anomalyTableData" 
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
                    <span :class="['value-cell', { 'anomaly-highlight': slotProps.data.anomalyType === 'stake' }]">
                      ${{ slotProps.data.stake.toFixed(2) }}
                    </span>
                  </template>
                </Column>
                <Column field="gamers" header="Gamers" sortable>
                  <template #body="slotProps">
                    <span class="value-cell">{{ slotProps.data.gamers }}</span>
                  </template>
                </Column>
                <Column field="skins" header="Skins" sortable>
                  <template #body="slotProps">
                    <span class="value-cell">{{ slotProps.data.skins }}</span>
                  </template>
                </Column>
                <Column field="payout" header="Payout" sortable>
                  <template #body="slotProps">
                    <span :class="['value-cell', { 'anomaly-highlight': slotProps.data.anomalyType === 'payout' }]">
                      ${{ slotProps.data.payout.toFixed(2) }}
                    </span>
                  </template>
                </Column>
                <Column field="peopleWin" header="People Win" sortable>
                  <template #body="slotProps">
                    <span class="value-cell win">{{ slotProps.data.peopleWin }}</span>
                  </template>
                </Column>
                <Column field="peopleLost" header="People Lost" sortable>
                  <template #body="slotProps">
                    <span class="value-cell lost">{{ slotProps.data.peopleLost }}</span>
                  </template>
                </Column>
                <Column field="severity" header="Severity" sortable>
                  <template #body="slotProps">
                    <Tag :value="slotProps.data.severity" :severity="getSeverityColor(slotProps.data.severity)" />
                  </template>
                </Column>
              </DataTable>
            </template>
          </Card>
        </div>

        <!-- Right Sidebar -->
        <aside class="right-sidebar">
          <div class="notifications-header">
            <h3>Anomaly Notifications</h3>
            <div class="header-actions">
              <Badge :value="unreadCount" severity="danger" />
              <Button 
                v-if="unreadCount > 0"
                label="Mark all read" 
                @click="markAllAsRead"
                text 
                size="small"
                severity="secondary"
              />
            </div>
          </div>
          
          <div v-if="notificationsLoading" class="loading-container">
            <i class="pi pi-spin pi-spinner" style="font-size: 1.5rem; color: #5B8DEE;"></i>
            <p>Loading notifications...</p>
          </div>
          <div v-else-if="notifications.length === 0" class="empty-state">
            <i class="pi pi-bell" style="font-size: 3rem; color: #CBD5E1;"></i>
            <p>No notifications</p>
            <span class="empty-hint">Anomalies will appear here</span>
          </div>
          <div v-else class="notifications-list">
            <div 
              v-for="notification in notifications" 
              :key="notification.id"
              :class="['notification-item', getNotificationSeverity(notification.severity), { unread: !notification.is_read }]"
            >
              <div class="notification-header">
                <div class="notification-type">
                  <i :class="notification.anomaly_type === 'stakes' ? 'pi pi-arrow-up' : 'pi pi-arrow-down'"></i>
                  <span class="type-label">{{ notification.anomaly_type }}</span>
                  <Badge v-if="!notification.is_read" value="NEW" severity="info" size="small" />
                </div>
                <span class="notification-time">{{ formatNotificationTime(notification.created_at) }}</span>
              </div>
              
              <div class="notification-body">
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-details">
                  <div class="detail-row">
                    <span class="detail-label">Value:</span>
                    <span class="detail-value">${{ notification.value.toFixed(2) }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Z-Score:</span>
                    <span :class="['detail-value', 'z-score', { negative: notification.z_score < 0 }]">
                      {{ notification.z_score > 0 ? '+' : '' }}{{ notification.z_score.toFixed(2) }}
                    </span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Severity:</span>
                    <Tag :value="notification.severity" :severity="getSeverityColor(notification.severity)" />
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value time">{{ new Date(notification.timestamp).toLocaleString() }}</span>
                  </div>
                </div>
              </div>
              
              <Divider />
              <div class="notification-footer">
                <Button 
                  v-if="!notification.is_read"
                  label="Mark as read" 
                  @click="markAsRead(notification.id)"
                  link 
                  size="small" 
                  severity="info" 
                />
                <span v-else class="read-label">
                  <i class="pi pi-check"></i> Read
                </span>
                <Button 
                  icon="pi pi-trash" 
                  @click="deleteNotification(notification.id)"
                  text 
                  rounded 
                  size="small" 
                  severity="danger" 
                />
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

.nav-item .notification-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  font-size: 0.625rem;
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

.page-subtitle::first-word {
  color: #94A3B8;
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
  gap: 1rem;
  flex-wrap: wrap;
}

.report-label {
  font-size: 0.875rem;
  color: #64748B;
  font-weight: 500;
}

.date-range-filter {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.date-range-calendar {
  width: 280px;
}

.date-range-calendar :deep(.p-inputtext) {
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.chart-tabs {
  display: flex;
  gap: 0.5rem;
}

.chart-tab-btn :deep(.pi-circle-fill) {
  font-size: 0.5rem;
}

.legend-info {
  display: flex;
  gap: 1.5rem;
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
  padding: 0;
}

.main-chart-card :deep(.p-card-content) {
  padding: 0;
  height: 100%;
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
  color: #EF4444;
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

.time-cell {
  font-size: 0.8125rem;
  color: #64748B;
  font-family: 'Monaco', 'Courier New', monospace;
}

.value-cell {
  font-weight: 500;
  color: #1E293B;
}

.value-cell.anomaly-highlight {
  color: #EF4444;
  font-weight: 700;
  background: #FEE2E2;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.value-cell.win {
  color: #10B981;
  font-weight: 600;
}

.value-cell.lost {
  color: #94A3B8;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.notification-item.unread {
  box-shadow: 0 2px 8px rgba(91, 141, 238, 0.15);
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 8px;
  height: 8px;
  background: #3B82F6;
  border-radius: 50%;
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

.read-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #10B981;
  font-weight: 500;
}

.read-label i {
  font-size: 0.875rem;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  color: #64748B;
}

.empty-state p {
  font-size: 1rem;
  font-weight: 500;
  margin: 1rem 0 0.25rem;
  color: #475569;
}

.empty-hint {
  font-size: 0.875rem;
  color: #94A3B8;
}

.detail-value.time {
  font-size: 0.7rem;
  color: #64748B;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  gap: 1rem;
  color: #64748B;
}

</style>
