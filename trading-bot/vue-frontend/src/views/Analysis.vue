<template>
  <div>
    <div class="row mb-4">
      <div class="col-12">
        <h1 class="mb-3">
          <i class="bi bi-bar-chart-line text-primary"></i> Technical Analysis
        </h1>
        <p class="text-muted">Advanced technical indicators and statistical analysis</p>
      </div>
    </div>

    <!-- Analysis Controls -->
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="bi bi-sliders"></i> Analysis Parameters
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-3">
            <label class="form-label">Symbol</label>
            <select class="form-select" v-model="analysisParams.symbol">
              <option value="BTC/USDT">BTC/USDT</option>
              <option value="ETH/USDT">ETH/USDT</option>
              <option value="ADA/USDT">ADA/USDT</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Timeframe</label>
            <select class="form-select" v-model="analysisParams.timeframe">
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Period</label>
            <input type="number" class="form-control" v-model="analysisParams.period" min="5" max="200">
          </div>
          <div class="col-md-3">
            <label class="form-label">&nbsp;</label>
            <div>
              <button class="btn btn-primary w-100" @click="runAnalysis" :disabled="loading">
                <i class="bi bi-play"></i> Run Analysis
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Technical Indicators -->
    <div class="row mb-4">
      <div class="col-lg-8">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-graph-up"></i> Technical Indicators
            </h5>
          </div>
          <div class="card-body">
            <div class="chart-container">
              <canvas ref="technicalChart"></canvas>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-calculator"></i> Indicator Values
            </h5>
          </div>
          <div class="card-body">
            <div v-if="technicalData.sma" class="mb-3">
              <div class="d-flex justify-content-between">
                <span>SMA ({{ analysisParams.period }})</span>
                <strong>{{ technicalData.sma.slice(-1)[0]?.toFixed(2) || 'N/A' }}</strong>
              </div>
              <div class="progress" style="height: 6px;">
                <div class="progress-bar bg-primary" :style="{ width: '75%' }"></div>
              </div>
            </div>

            <div v-if="technicalData.rsi" class="mb-3">
              <div class="d-flex justify-content-between">
                <span>RSI (14)</span>
                <strong>{{ technicalData.rsi.toFixed(2) }}</strong>
              </div>
              <div class="progress" style="height: 6px;">
                <div class="progress-bar" :class="getRSIColor(technicalData.rsi)" :style="{ width: technicalData.rsi + '%' }"></div>
              </div>
            </div>

            <div v-if="technicalData.macd" class="mb-3">
              <div class="d-flex justify-content-between">
                <span>MACD</span>
                <strong>{{ technicalData.macd.macd.slice(-1)[0]?.toFixed(4) || 'N/A' }}</strong>
              </div>
            </div>

            <div v-if="technicalData.trend_analysis" class="mb-3">
              <div class="d-flex justify-content-between">
                <span>Trend</span>
                <span :class="getTrendColor(technicalData.trend_analysis.direction)">
                  {{ technicalData.trend_analysis.direction }}
                </span>
              </div>
              <small class="text-muted">
                Strength: {{ technicalData.trend_analysis.strength?.toFixed(2) }}%
              </small>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-lightbulb"></i> Signals
            </h5>
          </div>
          <div class="card-body">
            <div v-if="signals.length === 0" class="text-center text-muted">
              <i class="bi bi-info-circle mb-2"></i>
              <p>No signals detected</p>
            </div>
            <div v-else v-for="signal in signals" :key="signal.id" class="mb-2">
              <div class="d-flex justify-content-between align-items-center">
                <span :class="getSignalColor(signal.type)">
                  <i :class="getSignalIcon(signal.type)"></i> {{ signal.type.toUpperCase() }}
                </span>
                <small class="text-muted">{{ signal.timestamp }}</small>
              </div>
              <small class="text-muted">{{ signal.description }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Statistical Analysis -->
    <div class="row">
      <div class="col-lg-6">
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-bar-chart"></i> Statistical Analysis
            </h5>
          </div>
          <div class="card-body">
            <div v-if="statisticalData" class="row">
              <div class="col-6">
                <div class="stat-item">
                  <div class="stat-value">{{ statisticalData.mean?.toFixed(2) }}</div>
                  <div class="stat-label">Mean</div>
                </div>
              </div>
              <div class="col-6">
                <div class="stat-item">
                  <div class="stat-value">{{ statisticalData.median?.toFixed(2) }}</div>
                  <div class="stat-label">Median</div>
                </div>
              </div>
              <div class="col-6">
                <div class="stat-item">
                  <div class="stat-value">{{ statisticalData.standard_deviation?.toFixed(2) }}</div>
                  <div class="stat-label">Std Dev</div>
                </div>
              </div>
              <div class="col-6">
                <div class="stat-item">
                  <div class="stat-value">{{ statisticalData.skewness?.toFixed(2) }}</div>
                  <div class="stat-label">Skewness</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-6">
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-graph-up"></i> Distribution Analysis
            </h5>
          </div>
          <div class="card-body">
            <div class="chart-container">
              <canvas ref="distributionChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

export default {
  name: 'Analysis',
  components: {
    Line,
    Bar
  },
  data() {
    return {
      loading: false,
      analysisParams: {
        symbol: 'BTC/USDT',
        timeframe: '1h',
        period: 50
      },
      technicalData: {},
      statisticalData: null,
      signals: [],
      technicalChart: null,
      distributionChart: null
    }
  },
  mounted() {
    this.runAnalysis()
  },
  methods: {
    async runAnalysis() {
      this.loading = true
      try {
        // Get technical analysis from Laravel API
        const technicalResponse = await axios.get('http://localhost:8000/api/analysis/technical', {
          params: this.analysisParams
        })
        this.technicalData = technicalResponse.data.analysis || {}

        // Get statistical analysis
        const statisticalResponse = await axios.post('http://localhost:8000/api/analysis/statistical', {
          data: this.generateSampleData()
        })
        this.statisticalData = statisticalResponse.data.analysis

        // Generate signals based on technical data
        this.generateSignals()

        // Update charts
        this.updateTechnicalChart()
        this.updateDistributionChart()

      } catch (error) {
        console.error('Analysis error:', error)
        this.showError('Failed to run analysis')
      } finally {
        this.loading = false
      }
    },

    generateSampleData() {
      // Generate sample data for demonstration
      const data = []
      for (let i = 0; i < 100; i++) {
        data.push({
          value: Math.random() * 100 + 50,
          timestamp: new Date(Date.now() - (99 - i) * 3600000).toISOString()
        })
      }
      return data
    },

    generateSignals() {
      this.signals = []

      if (this.technicalData.rsi) {
        if (this.technicalData.rsi < 30) {
          this.signals.push({
            id: 1,
            type: 'buy',
            description: 'RSI indicates oversold condition',
            timestamp: new Date().toLocaleTimeString()
          })
        } else if (this.technicalData.rsi > 70) {
          this.signals.push({
            id: 2,
            type: 'sell',
            description: 'RSI indicates overbought condition',
            timestamp: new Date().toLocaleTimeString()
          })
        }
      }

      if (this.technicalData.trend_analysis) {
        const trend = this.technicalData.trend_analysis
        if (trend.direction === 'uptrend' && trend.strength > 0.5) {
          this.signals.push({
            id: 3,
            type: 'buy',
            description: 'Strong uptrend detected',
            timestamp: new Date().toLocaleTimeString()
          })
        }
      }
    },

    updateTechnicalChart() {
      if (!this.$refs.technicalChart) return

      const ctx = this.$refs.technicalChart.getContext('2d')

      if (this.technicalChart) {
        this.technicalChart.destroy()
      }

      // Sample price data
      const labels = Array.from({length: 50}, (_, i) => `T-${49-i}`)
      const prices = Array.from({length: 50}, () => Math.random() * 20 + 80)

      const datasets = [{
        label: 'Price',
        data: prices,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1
      }]

      // Add SMA if available
      if (this.technicalData.sma) {
        datasets.push({
          label: 'SMA',
          data: this.technicalData.sma,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderDash: [5, 5]
        })
      }

      this.technicalChart = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: `${this.analysisParams.symbol} Technical Analysis`
            }
          }
        }
      })
    },

    updateDistributionChart() {
      if (!this.$refs.distributionChart) return

      const ctx = this.$refs.distributionChart.getContext('2d')

      if (this.distributionChart) {
        this.distributionChart.destroy()
      }

      // Sample distribution data
      const data = this.generateSampleData().map(item => item.value)
      const histogram = this.createHistogram(data, 10)

      this.distributionChart = new ChartJS(ctx, {
        type: 'bar',
        data: {
          labels: histogram.labels,
          datasets: [{
            label: 'Frequency',
            data: histogram.values,
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
            },
            title: {
              display: true,
              text: 'Price Distribution'
            }
          }
        }
      })
    },

    createHistogram(data, bins) {
      const min = Math.min(...data)
      const max = Math.max(...data)
      const range = max - min
      const binSize = range / bins

      const labels = []
      const values = new Array(bins).fill(0)

      for (let i = 0; i < bins; i++) {
        const binStart = min + (i * binSize)
        const binEnd = min + ((i + 1) * binSize)
        labels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`)

        data.forEach(value => {
          if (value >= binStart && value < binEnd) {
            values[i]++
          }
        })
      }

      return { labels, values }
    },

    getRSIColor(rsi) {
      if (rsi < 30) return 'bg-success'
      if (rsi > 70) return 'bg-danger'
      return 'bg-warning'
    },

    getTrendColor(direction) {
      return direction === 'uptrend' ? 'text-success' : direction === 'downtrend' ? 'text-danger' : 'text-muted'
    },

    getSignalColor(type) {
      return type === 'buy' ? 'text-success' : type === 'sell' ? 'text-danger' : 'text-warning'
    },

    getSignalIcon(type) {
      return type === 'buy' ? 'bi bi-arrow-up-circle' : type === 'sell' ? 'bi bi-arrow-down-circle' : 'bi bi-dash-circle'
    },

    showError(message) {
      // In a real app, you'd use a toast notification
      alert(message)
    }
  }
}
</script>

<style scoped>
.chart-container {
  height: 300px;
  width: 100%;
}

.stat-item {
  text-align: center;
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #007bff;
}

.stat-label {
  font-size: 0.875rem;
  color: #6c757d;
  margin-top: 0.25rem;
}

.progress {
  margin-top: 0.25rem;
}
</style>