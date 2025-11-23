<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { apiService } from '@/services/api'

const props = defineProps<{
  chartType: 'stakes' | 'payouts'
  startDate?: string
  endDate?: string
}>()

const chartDiv = ref<HTMLDivElement | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const renderChart = async () => {
  if (!chartDiv.value) {
    console.warn('Chart div not ready yet')
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await apiService.getStakesPayoutsChart(
      props.chartType,
      props.startDate,
      props.endDate
    )

    const { data, mean, std } = response
    const timestamps = data.timestamps.map(t => new Date(t))
    const values = data.values
    const anomalies = data.anomalies
    const bounds = data.bounds

    let traces: any[] = []
    let yAxisTitle = ''
    let mainColor = ''
    let lightColor = ''

    if (props.chartType === 'stakes') {
      yAxisTitle = 'Stakes'
      mainColor = '#3b82f6'
      lightColor = '#93c5fd'

      traces = [
        // Stakes trace
        {
          x: timestamps,
          y: values,
          type: 'scatter',
          mode: 'lines',
          name: 'Stakes',
          line: { color: mainColor, width: 2 },
          fill: 'tozeroy',
          fillcolor: 'rgba(59, 130, 246, 0.05)'
        },
        // Stakes upper bound only (stakes can't be negative)
        {
          x: timestamps,
          y: bounds.upper,
          type: 'scatter',
          mode: 'lines',
          name: 'Upper Threshold',
          line: { color: lightColor, width: 1, dash: 'dot' },
          showlegend: false
        }
      ]
    } else {
      yAxisTitle = 'Payouts'
      mainColor = '#10b981'
      lightColor = '#86efac'

      traces = [
        // Payouts trace
        {
          x: timestamps,
          y: values,
          type: 'scatter',
          mode: 'lines',
          name: 'Payouts',
          line: { color: mainColor, width: 2 },
          fill: 'tozeroy',
          fillcolor: 'rgba(16, 185, 129, 0.05)'
        },
        // Payouts upper bound only (payouts can't be negative)
        {
          x: timestamps,
          y: bounds.upper,
          type: 'scatter',
          mode: 'lines',
          name: 'Upper Threshold',
          line: { color: lightColor, width: 1, dash: 'dot' },
          showlegend: false
        }
      ]
    }

    // Add anomaly markers
    if (anomalies.length > 0) {
      traces.push({
        x: anomalies.map(a => new Date(a.x)),
        y: anomalies.map(a => a.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Anomaly',
        marker: {
          color: '#ef4444',
          size: 10,
          symbol: 'diamond',
          line: { color: '#dc2626', width: 2 }
        },
        text: anomalies.map(a => `Z-Score: ${a.zScore}`),
        hovertemplate: `<b>Anomaly Detected</b><br>Time: %{x}<br>${yAxisTitle}: %{y:.2f}<br>%{text}<extra></extra>`
      })
    }

    const layout = {
      xaxis: {
        showgrid: true,
        gridcolor: '#F1F5F9',
        zeroline: false,
        title: 'Time'
      },
      yaxis: {
        title: yAxisTitle,
        titlefont: { color: '#64748B', size: 12 },
        tickfont: { color: '#94A3B8', size: 11 },
        showgrid: true,
        gridcolor: '#F1F5F9',
        zeroline: false
      },
      hovermode: 'closest',
      showlegend: false,
      plot_bgcolor: 'white',
      paper_bgcolor: 'white',
      margin: { t: 10, r: 20, b: 50, l: 60 },
      autosize: true
    }

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d']
    }

    // Ensure the div still exists before plotting
    if (!chartDiv.value) {
      console.warn('Chart div was removed before plotting')
      loading.value = false
      return
    }

    await Plotly.newPlot(chartDiv.value, traces, layout, config)
    
    // Force resize after plot is created
    window.dispatchEvent(new Event('resize'))
    
    loading.value = false
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load chart data'
    loading.value = false
    console.error('Error loading chart:', err)
  }
}

onMounted(async () => {
  // Wait for next tick to ensure DOM is ready
  await new Promise(resolve => setTimeout(resolve, 0))
  renderChart()
})

watch(() => [props.chartType, props.startDate, props.endDate], async () => {
  // Wait for next tick before re-rendering
  await new Promise(resolve => setTimeout(resolve, 0))
  renderChart()
})
</script>

<template>
  <div class="chart-container">
    <div v-if="loading" class="loading-overlay">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <p>Loading chart data...</p>
    </div>
    <div v-if="error" class="error-message">
      <i class="pi pi-exclamation-circle"></i>
      <p>{{ error }}</p>
    </div>
    <div ref="chartDiv" class="plotly-chart" :style="{ display: loading || error ? 'none' : 'block' }"></div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 500px;
  position: relative;
}

.plotly-chart {
  width: 100%;
  height: 500px;
}

.plotly-chart :deep(.plotly) {
  width: 100% !important;
  height: 100% !important;
}

.plotly-chart :deep(.plotly .main-svg) {
  width: 100% !important;
  height: 100% !important;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #64748B;
  gap: 1rem;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #EF4444;
  gap: 1rem;
}

.error-message i {
  font-size: 2rem;
}
</style>
