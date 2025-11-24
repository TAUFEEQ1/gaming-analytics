<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Plotly from 'plotly.js-dist-min'

// Generate sample data with z-scores and DBSCAN anomalies
const generateSampleData = () => {
  const rounds = 100
  const data: {
    round: number
    stakeZScore: number
    payoutZScore: number
    houseNetZScore: number
    dbAnomaly: number
  }[] = []

  for (let i = 0; i < rounds; i++) {
    // Normal data follows standard distribution
    const stakeZ = (Math.random() - 0.5) * 4 // Most values between -2 and +2
    const payoutZ = (Math.random() - 0.5) * 4
    const houseNetZ = (Math.random() - 0.5) * 4
    
    // Inject some DBSCAN anomalies (multi-variate outliers)
    let dbAnomaly = 0
    
    // DBSCAN detects points that are outliers in multi-dimensional space
    // Create anomalies where multiple z-scores are extreme simultaneously
    if (Math.random() < 0.15) {
      const anomalyType = Math.random()
      if (anomalyType < 0.5) {
        // Type 1: High stakes + High payouts = Large house loss
        data.push({
          round: i + 1,
          stakeZScore: 3.5 + Math.random() * 1.5,
          payoutZScore: 3.2 + Math.random() * 1.5,
          houseNetZScore: -(3.0 + Math.random() * 1.5),
          dbAnomaly: 1
        })
      } else {
        // Type 2: Low stakes + Very high payouts = Unusual win pattern
        data.push({
          round: i + 1,
          stakeZScore: -(2.5 + Math.random() * 1.5),
          payoutZScore: 3.8 + Math.random() * 1.5,
          houseNetZScore: 3.5 + Math.random() * 1.5,
          dbAnomaly: 1
        })
      }
    } else {
      data.push({
        round: i + 1,
        stakeZScore: stakeZ,
        payoutZScore: payoutZ,
        houseNetZScore: houseNetZ,
        dbAnomaly: 0
      })
    }
  }
  
  return data
}

const renderChart = () => {
  const data = generateSampleData()
  
  const rounds = data.map(d => d.round)
  const stakeZScores = data.map(d => d.stakeZScore)
  const payoutZScores = data.map(d => d.payoutZScore)
  const houseNetZScores = data.map(d => d.houseNetZScore)
  
  // Separate normal and anomaly points
  const normalIndices = data.map((d, i) => d.dbAnomaly === 0 ? i : -1).filter(i => i !== -1)
  const anomalyIndices = data.map((d, i) => d.dbAnomaly === 1 ? i : -1).filter(i => i !== -1)

  const traces = []

  // Normal points - Stake Z-Scores
  traces.push({
    x: normalIndices.map(i => rounds[i]),
    y: normalIndices.map(i => stakeZScores[i]),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Stake Z-Score',
    line: {
      color: '#3B82F6',
      width: 2
    },
    marker: {
      size: 6,
      color: '#3B82F6',
      opacity: 0.7
    },
    hovertemplate: '<b>Round %{x}</b><br>Stake Z-Score: %{y:.2f}<extra></extra>'
  })

  // Normal points - Payout Z-Scores
  traces.push({
    x: normalIndices.map(i => rounds[i]),
    y: normalIndices.map(i => payoutZScores[i]),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Payout Z-Score',
    line: {
      color: '#10B981',
      width: 2
    },
    marker: {
      size: 6,
      color: '#10B981',
      opacity: 0.7
    },
    hovertemplate: '<b>Round %{x}</b><br>Payout Z-Score: %{y:.2f}<extra></extra>'
  })

  // Normal points - House Net Z-Scores
  traces.push({
    x: normalIndices.map(i => rounds[i]),
    y: normalIndices.map(i => houseNetZScores[i]),
    type: 'scatter',
    mode: 'lines+markers',
    name: 'House Net Z-Score',
    line: {
      color: '#F59E0B',
      width: 2
    },
    marker: {
      size: 6,
      color: '#F59E0B',
      opacity: 0.7
    },
    hovertemplate: '<b>Round %{x}</b><br>House Net Z-Score: %{y:.2f}<extra></extra>'
  })

  // DBSCAN Anomalies - overlaid on all three metrics
  if (anomalyIndices.length > 0) {
    // Stake anomalies
    traces.push({
      x: anomalyIndices.map(i => rounds[i]),
      y: anomalyIndices.map(i => stakeZScores[i]),
      type: 'scatter',
      mode: 'markers',
      name: 'DBSCAN Anomaly (Stake)',
      marker: {
        size: 12,
        color: '#EF4444',
        symbol: 'diamond',
        line: {
          color: '#DC2626',
          width: 2
        }
      },
      hovertemplate: '<b>DBSCAN Anomaly</b><br>Round %{x}<br>Stake Z: %{y:.2f}<extra></extra>',
      showlegend: false
    })

    // Payout anomalies
    traces.push({
      x: anomalyIndices.map(i => rounds[i]),
      y: anomalyIndices.map(i => payoutZScores[i]),
      type: 'scatter',
      mode: 'markers',
      name: 'DBSCAN Anomaly (Payout)',
      marker: {
        size: 12,
        color: '#EF4444',
        symbol: 'diamond',
        line: {
          color: '#DC2626',
          width: 2
        }
      },
      hovertemplate: '<b>DBSCAN Anomaly</b><br>Round %{x}<br>Payout Z: %{y:.2f}<extra></extra>',
      showlegend: false
    })

    // House Net anomalies
    traces.push({
      x: anomalyIndices.map(i => rounds[i]),
      y: anomalyIndices.map(i => houseNetZScores[i]),
      type: 'scatter',
      mode: 'markers',
      name: 'DBSCAN Anomaly',
      marker: {
        size: 12,
        color: '#EF4444',
        symbol: 'diamond',
        line: {
          color: '#DC2626',
          width: 2
        }
      },
      hovertemplate: '<b>DBSCAN Anomaly</b><br>Round %{x}<br>House Net Z: %{y:.2f}<extra></extra>'
    })
  }

  // Reference lines at ±3 (anomaly threshold)
  traces.push({
    x: [rounds[0], rounds[rounds.length - 1]],
    y: [3, 3],
    type: 'scatter',
    mode: 'lines',
    name: 'Upper Threshold (+3σ)',
    line: {
      color: '#94A3B8',
      width: 1,
      dash: 'dash'
    },
    hoverinfo: 'skip',
    showlegend: false
  })

  traces.push({
    x: [rounds[0], rounds[rounds.length - 1]],
    y: [-3, -3],
    type: 'scatter',
    mode: 'lines',
    name: 'Lower Threshold (-3σ)',
    line: {
      color: '#94A3B8',
      width: 1,
      dash: 'dash'
    },
    hoverinfo: 'skip',
    showlegend: false
  })

  traces.push({
    x: [rounds[0], rounds[rounds.length - 1]],
    y: [0, 0],
    type: 'scatter',
    mode: 'lines',
    name: 'Mean',
    line: {
      color: '#CBD5E1',
      width: 1,
      dash: 'dot'
    },
    hoverinfo: 'skip',
    showlegend: false
  })

  const layout = {
    height: 450,
    margin: { t: 20, r: 20, b: 60, l: 60 },
    xaxis: {
      title: 'Round Number',
      gridcolor: '#F1F5F9',
      tickfont: { size: 11, color: '#64748B' },
      titlefont: { size: 12, color: '#475569' }
    },
    yaxis: {
      title: 'Z-Score',
      gridcolor: '#F1F5F9',
      zeroline: true,
      zerolinecolor: '#CBD5E1',
      zerolinewidth: 1,
      tickfont: { size: 11, color: '#64748B' },
      titlefont: { size: 12, color: '#475569' }
    },
    plot_bgcolor: 'white',
    paper_bgcolor: 'white',
    hovermode: 'closest',
    showlegend: true,
    legend: {
      orientation: 'h',
      x: 0.5,
      xanchor: 'center',
      y: -0.15,
      font: { size: 11, color: '#475569' }
    }
  }

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d']
  }

  const chartElement = document.getElementById('composite-chart')
  if (chartElement) {
    Plotly.newPlot(chartElement, traces, layout, config)
  }
}

onMounted(() => {
  renderChart()
})
</script>

<template>
  <div id="composite-chart" class="chart-container"></div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  min-height: 450px;
}
</style>
