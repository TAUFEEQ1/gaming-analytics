<script setup lang="ts">
import { defineProps } from 'vue'
import Card from 'primevue/card'

defineProps<{
  title: string
  value: string
  subtitle: string
  trend?: 'up' | 'down'
  icon?: string
}>()
</script>

<template>
  <Card class="stat-card">
    <template #content>
      <div class="stat-content">
        <div class="stat-header">
          <h3>{{ title }}</h3>
        </div>
        <div class="stat-value">{{ value }}</div>
        <div class="stat-footer">
          <span class="stat-subtitle">{{ subtitle }}</span>
          <div class="stat-chart">
            <svg viewBox="0 0 100 30" class="mini-chart">
              <polyline
                v-if="trend === 'up'"
                points="0,25 20,20 40,18 60,15 80,12 100,5"
                fill="none"
                stroke="#10B981"
                stroke-width="2"
              />
              <polyline
                v-else
                points="0,5 20,8 40,10 60,13 80,16 100,20"
                fill="none"
                stroke="#EF4444"
                stroke-width="2"
              />
            </svg>
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.stat-card {
  border-radius: 16px;
  border: 1px solid #E2E8F0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-card :deep(.p-card-body) {
  padding: 1.5rem;
}

.stat-card :deep(.p-card-content) {
  padding: 0;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.stat-header h3 {
  font-size: 0.875rem;
  color: #64748B;
  margin: 0;
  font-weight: 500;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1E293B;
}

.stat-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-subtitle {
  font-size: 0.75rem;
  color: #94A3B8;
}

.stat-chart {
  width: 100px;
  height: 30px;
}

.mini-chart {
  width: 100%;
  height: 100%;
}
</style>
