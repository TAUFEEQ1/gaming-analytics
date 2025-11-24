<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { apiService } from '@/services/api'

const props = defineProps<{
  startDate?: string
  endDate?: string
}>()

const chartDiv = ref<HTMLDivElement | null>(null)

const renderChart = async () => {
  try {
    // Fetch real data from API with date filters
    // Use higher limit when date filters are applied to get full range
    const limit = (props.startDate || props.endDate) ? 10000 : 100
    const data = await apiService.getCompositeChartData(limit, props.startDate, props.endDate)
    
    if (!data.timestamps || data.timestamps.length === 0) {
      console.error('No data available')
      return
    }

    const timestamps = data.timestamps.map(t => new Date(t))
    const stakeZScores = data.stakeZScores
    const payoutZScores = data.payoutZScores
    const houseNetZScores = data.houseNetZScores
    const anomalyIndices = data.anomalyIndices

    const traces = []

    // Stake Z-Scores - all data points
    traces.push({
      x: timestamps,
      y: stakeZScores,
      type: 'scatter',
      mode: 'lines',
      name: 'Stake Z-Score',
      line: {
        color: '#3B82F6',
        width: 2
      },
      hovertemplate: '<b>%{x}</b><br>Stake Z-Score: %{y:.2f}<extra></extra>'
    })

    // Payout Z-Scores - all data points
    traces.push({
      x: timestamps,
      y: payoutZScores,
      type: 'scatter',
      mode: 'lines',
      name: 'Payout Z-Score',
      line: {
        color: '#10B981',
        width: 2
      },
      hovertemplate: '<b>%{x}</b><br>Payout Z-Score: %{y:.2f}<extra></extra>'
    })

    // House Net Z-Scores - all data points
    traces.push({
      x: timestamps,
      y: houseNetZScores,
      type: 'scatter',
      mode: 'lines',
      name: 'House Net Z-Score',
      line: {
        color: '#F59E0B',
        width: 2
      },
      hovertemplate: '<b>%{x}</b><br>House Net Z-Score: %{y:.2f}<extra></extra>'
    })

    // DBSCAN Anomalies - overlay markers
    if (anomalyIndices.length > 0) {
      traces.push({
        x: anomalyIndices.map(i => timestamps[i]),
        y: anomalyIndices.map(i => stakeZScores[i]),
        type: 'scatter',
        mode: 'markers',
        name: 'DBSCAN Anomaly',
        marker: {
          size: 10,
          color: '#EF4444',
          symbol: 'diamond',
          line: {
            color: '#DC2626',
            width: 2
          }
        },
        hovertemplate: '<b>DBSCAN Anomaly</b><br>%{x}<br>Stake Z: %{y:.2f}<extra></extra>',
        showlegend: true
      })

      traces.push({
        x: anomalyIndices.map(i => timestamps[i]),
        y: anomalyIndices.map(i => payoutZScores[i]),
        type: 'scatter',
        mode: 'markers',
        name: 'DBSCAN Anomaly',
        marker: {
          size: 10,
          color: '#EF4444',
          symbol: 'diamond',
          line: {
            color: '#DC2626',
            width: 2
          }
        },
        hovertemplate: '<b>DBSCAN Anomaly</b><br>%{x}<br>Payout Z: %{y:.2f}<extra></extra>',
        showlegend: false
      })

      traces.push({
        x: anomalyIndices.map(i => timestamps[i]),
        y: anomalyIndices.map(i => houseNetZScores[i]),
        type: 'scatter',
        mode: 'markers',
        name: 'DBSCAN Anomaly',
        marker: {
          size: 10,
          color: '#EF4444',
          symbol: 'diamond',
          line: {
            color: '#DC2626',
            width: 2
          }
        },
        hovertemplate: '<b>DBSCAN Anomaly</b><br>%{x}<br>House Net Z: %{y:.2f}<extra></extra>',
        showlegend: false
      })
    }

    // Reference lines at ±3 (anomaly threshold)
    traces.push({
      x: [timestamps[0], timestamps[timestamps.length - 1]],
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
      x: [timestamps[0], timestamps[timestamps.length - 1]],
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
      x: [timestamps[0], timestamps[timestamps.length - 1]],
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
      height: 600,
      autosize: true,
      margin: { t: 20, r: 20, b: 60, l: 60 },
      xaxis: {
        title: 'Time',
        gridcolor: '#F1F5F9',
        tickfont: { size: 11, color: '#64748B' },
        titlefont: { size: 12, color: '#475569' },
        type: 'date'
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

    if (chartDiv.value) {
      Plotly.newPlot(chartDiv.value, traces, layout, config)
    }
  } catch (error) {
    console.error('Failed to render composite chart:', error)
  }
}

onMounted(() => {
  renderChart()
})

// Watch for date filter changes
watch(() => [props.startDate, props.endDate], () => {
  renderChart()
})
</script>

<template>
  <div ref="chartDiv" class="chart-container"></div>
</template>

<style scoped>
.chart-container {
  width: 100%;
  min-height: 600px;
}
</style>
