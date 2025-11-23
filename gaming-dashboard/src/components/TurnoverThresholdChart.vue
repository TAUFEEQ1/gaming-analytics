<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Plotly from 'plotly.js-dist-min'

const chartDiv = ref<HTMLDivElement | null>(null)

// Sample data for turnover monitoring
const generateTurnoverData = () => {
  const now = Date.now()
  const dataPoints = 50
  const timestamps = []
  const turnover = []
  const threshold = 50000 // Regulatory minimum turnover threshold
  const breachPoints = []

  for (let i = 0; i < dataPoints; i++) {
    const timestamp = new Date(now - (dataPoints - i) * 86400000) // daily data
    timestamps.push(timestamp)
    
    // Generate turnover with occasional drops below threshold
    let turnoverValue = 60000 + Math.random() * 20000
    
    // Inject threshold breaches
    if (i > 30 && i < 40) {
      turnoverValue = 40000 + Math.random() * 8000 // Below threshold
      breachPoints.push({ x: timestamp, y: turnoverValue })
    }
    
    turnover.push(turnoverValue)
  }

  return { timestamps, turnover, threshold, breachPoints }
}

onMounted(() => {
  if (!chartDiv.value) return

  const { timestamps, turnover, threshold, breachPoints } = generateTurnoverData()

  // Create threshold line
  const thresholdLine = timestamps.map(() => threshold)

  const traces: any[] = [
    // Turnover trace
    {
      x: timestamps,
      y: turnover,
      type: 'scatter',
      mode: 'lines',
      name: 'Operator Turnover',
      line: { 
        color: turnover.map(t => t < threshold ? '#ef4444' : '#3b82f6'),
        width: 3
      },
      fill: 'tonexty',
      fillcolor: 'rgba(59, 130, 246, 0.1)',
      hovertemplate: '<b>Turnover</b><br>Date: %{x}<br>Amount: $%{y:,.2f}<extra></extra>'
    },
    // Threshold line
    {
      x: timestamps,
      y: thresholdLine,
      type: 'scatter',
      mode: 'lines',
      name: 'Regulatory Threshold',
      line: { 
        color: '#dc2626', 
        width: 2, 
        dash: 'dash' 
      },
      hovertemplate: '<b>Regulatory Minimum</b><br>$%{y:,.2f}<extra></extra>'
    }
  ]

  // Add breach markers
  if (breachPoints.length > 0) {
    traces.push({
      x: breachPoints.map(b => b.x),
      y: breachPoints.map(b => b.y),
      type: 'scatter',
      mode: 'markers',
      name: 'Compliance Breach',
      marker: {
        color: '#dc2626',
        size: 12,
        symbol: 'x',
        line: { color: '#991b1b', width: 2 }
      },
      hovertemplate: '<b>⚠️ Compliance Alert</b><br>Date: %{x}<br>Turnover: $%{y:,.2f}<br><i>Below regulatory threshold</i><extra></extra>'
    })
  }

  const layout = {
    xaxis: {
      showgrid: true,
      gridcolor: '#F1F5F9',
      zeroline: false
    },
    yaxis: {
      title: 'Turnover ($)',
      titlefont: { color: '#64748B', size: 12 },
      tickfont: { color: '#94A3B8', size: 11 },
      showgrid: true,
      gridcolor: '#F1F5F9',
      tickformat: '$,.0f',
      zeroline: false
    },
    hovermode: 'closest',
    showlegend: true,
    legend: {
      x: 0.01,
      y: 0.99,
      bgcolor: 'rgba(255, 255, 255, 0.9)',
      bordercolor: '#E2E8F0',
      borderwidth: 1,
      font: { size: 11 }
    },
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    shapes: [
      {
        type: 'rect',
        xref: 'paper',
        yref: 'y',
        x0: 0,
        y0: 0,
        x1: 1,
        y1: threshold,
        fillcolor: '#FEE2E2',
        opacity: 0.2,
        line: { width: 0 },
        layer: 'below'
      }
    ],
    annotations: [
      {
        x: timestamps[35],
        y: threshold - 5000,
        xref: 'x',
        yref: 'y',
        text: '⚠️ Risk Zone',
        showarrow: false,
        font: { color: '#DC2626', size: 11, family: 'Arial' },
        bgcolor: 'rgba(254, 226, 226, 0.9)',
        bordercolor: '#DC2626',
        borderwidth: 1,
        borderpad: 4
      }
    ],
    margin: { t: 20, r: 60, b: 40, l: 80 }
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  }

  Plotly.newPlot(chartDiv.value, traces, layout, config)
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
  min-height: 350px;
}

.plotly-chart {
  width: 100%;
  height: 350px;
}
</style>
