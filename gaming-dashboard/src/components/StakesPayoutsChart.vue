<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'

const props = defineProps<{
  chartType: 'stakes' | 'payouts'
}>()

const chartDiv = ref<HTMLDivElement | null>(null)

// Sample data structure - replace with actual data from your casino rounds
const generateSampleData = () => {
  const now = Date.now()
  const dataPoints = 100
  const timestamps = []
  const stakes = []
  const payouts = []
  const stakeAnomalies = []
  const payoutAnomalies = []

  // Generate sample time series data
  for (let i = 0; i < dataPoints; i++) {
    const timestamp = new Date(now - (dataPoints - i) * 3600000) // hourly data
    timestamps.push(timestamp)
    
    // Normal stakes with some random variation
    const baseStake = 100 + Math.random() * 50
    const stakeValue = baseStake + (Math.random() - 0.5) * 20
    stakes.push(stakeValue)
    
    // Normal payouts
    const basePayout = 80 + Math.random() * 40
    const payoutValue = basePayout + (Math.random() - 0.5) * 15
    payouts.push(payoutValue)
    
    // Inject some anomalies (z-score > 3 or < -3)
    if (Math.random() > 0.95) {
      stakes[i] = baseStake + (Math.random() > 0.5 ? 80 : -60) // spike or drop
      stakeAnomalies.push({ x: timestamp, y: stakes[i], index: i })
    }
    
    if (Math.random() > 0.95) {
      payouts[i] = basePayout + (Math.random() > 0.5 ? 70 : -50)
      payoutAnomalies.push({ x: timestamp, y: payouts[i], index: i })
    }
  }

  return { timestamps, stakes, payouts, stakeAnomalies, payoutAnomalies }
}

const renderChart = () => {
  if (!chartDiv.value) return

  const { timestamps, stakes, payouts, stakeAnomalies, payoutAnomalies } = generateSampleData()

  // Calculate z-score bounds (mean ± 3 standard deviations)
  const calculateBounds = (data: number[]) => {
    const mean = data.reduce((a, b) => a + b, 0) / data.length
    const std = Math.sqrt(data.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / data.length)
    return {
      upper: data.map(() => mean + 3 * std),
      lower: data.map(() => mean - 3 * std),
      mean: data.map(() => mean)
    }
  }

  const stakeBounds = calculateBounds(stakes)
  const payoutBounds = calculateBounds(payouts)

  let traces: any[] = []
  let yAxisTitle = ''
  let mainColor = ''
  let lightColor = ''
  let anomalies: any[] = []

  if (props.chartType === 'stakes') {
    yAxisTitle = 'Stakes'
    mainColor = '#3b82f6'
    lightColor = '#93c5fd'
    anomalies = stakeAnomalies

    traces = [
      // Stakes trace
      {
        x: timestamps,
        y: stakes,
        type: 'scatter',
        mode: 'lines',
        name: 'Stakes',
        line: { color: mainColor, width: 2 },
        fill: 'tonexty',
        fillcolor: 'rgba(59, 130, 246, 0.05)'
      },
      // Stakes upper bound
      {
        x: timestamps,
        y: stakeBounds.upper,
        type: 'scatter',
        mode: 'lines',
        name: 'Normal Range Upper',
        line: { color: lightColor, width: 1, dash: 'dot' },
        showlegend: false
      },
      // Stakes lower bound
      {
        x: timestamps,
        y: stakeBounds.lower,
        type: 'scatter',
        mode: 'lines',
        name: 'Normal Range Lower',
        line: { color: lightColor, width: 1, dash: 'dot' },
        fill: 'tonexty',
        fillcolor: 'rgba(147, 197, 253, 0.1)',
        showlegend: false
      }
    ]
  } else {
    yAxisTitle = 'Payouts'
    mainColor = '#10b981'
    lightColor = '#86efac'
    anomalies = payoutAnomalies

    traces = [
      // Payouts trace
      {
        x: timestamps,
        y: payouts,
        type: 'scatter',
        mode: 'lines',
        name: 'Payouts',
        line: { color: mainColor, width: 2 },
        fill: 'tonexty',
        fillcolor: 'rgba(16, 185, 129, 0.05)'
      },
      // Payouts upper bound
      {
        x: timestamps,
        y: payoutBounds.upper,
        type: 'scatter',
        mode: 'lines',
        name: 'Normal Range Upper',
        line: { color: lightColor, width: 1, dash: 'dot' },
        showlegend: false
      },
      // Payouts lower bound
      {
        x: timestamps,
        y: payoutBounds.lower,
        type: 'scatter',
        mode: 'lines',
        name: 'Normal Range Lower',
        line: { color: lightColor, width: 1, dash: 'dot' },
        fill: 'tonexty',
        fillcolor: 'rgba(134, 239, 172, 0.1)',
        showlegend: false
      }
    ]
  }

  // Add anomaly markers
  if (anomalies.length > 0) {
    traces.push({
      x: anomalies.map(a => a.x),
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
      hovertemplate: `<b>Anomaly Detected</b><br>Time: %{x}<br>${yAxisTitle}: %{y:.2f}<extra></extra>`
    })
  }

  const layout = {
    xaxis: {
      showgrid: true,
      gridcolor: '#F1F5F9',
      zeroline: false
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
    margin: { t: 20, r: 60, b: 40, l: 60 }
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  }

  Plotly.newPlot(chartDiv.value, traces, layout, config)
}

onMounted(() => {
  renderChart()
})

watch(() => props.chartType, () => {
  renderChart()
})
</script>

<template>
  <div class="chart-container">
    <div ref="chartDiv" class="plotly-chart"></div>
  </div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  min-height: 400px;
}

.plotly-chart {
  width: 100%;
  height: 400px;
}
</style>
