<template>
  <div>
    <div class="row mb-4">
      <div class="col-12">
        <h1 class="mb-3">
          <i class="bi bi-graph-up text-primary"></i> Trading Bot Dashboard
        </h1>
        <p class="text-muted">Real-time monitoring and analysis of your automated trading bot</p>
      </div>
    </div>

    <!-- Status Cards -->
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-robot display-4 text-primary mb-2"></i>
            <h5 class="card-title">Bot Status</h5>
            <span class="badge bg-success fs-6">Running</span>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-cash-coin display-4 text-success mb-2"></i>
            <h5 class="card-title">Current Balance</h5>
            <h4 class="text-success">$100.00</h4>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-graph-up-arrow display-4 text-info mb-2"></i>
            <h5 class="card-title">Active Trades</h5>
            <h4 class="text-info">0</h4>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-clock display-4 text-warning mb-2"></i>
            <h5 class="card-title">Uptime</h5>
            <h4 class="text-warning">{{ uptime }}</h4>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="row">
      <!-- Trading Data -->
      <div class="col-lg-8">
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-bar-chart-line"></i> Trading Activity
            </h5>
          </div>
          <div class="card-body">
            <div class="chart-container">
              <canvas ref="tradingChart"></canvas>
            </div>
          </div>
        </div>

        <!-- Recent Trades -->
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-clock-history"></i> Recent Activity
            </h5>
          </div>
          <div class="card-body">
            <div v-if="recentLogs.length === 0" class="text-center text-muted py-4">
              <i class="bi bi-info-circle display-4 mb-3"></i>
              <p>No recent trading activity</p>
            </div>
            <div v-else class="table-responsive">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Level</th>
                    <th>Message</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in recentLogs.slice(0, 10)" :key="log.timestamp">
                    <td>{{ formatTime(log.timestamp) }}</td>
                    <td>
                      <span :class="getLogBadgeClass(log.level)" class="badge">
                        {{ log.level }}
                      </span>
                    </td>
                    <td>{{ log.message }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="col-lg-4">
        <!-- Quick Actions -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-gear"></i> Quick Actions
            </h5>
          </div>
          <div class="card-body">
            <div class="d-grid gap-2">
              <button class="btn btn-primary" @click="refreshData">
                <i class="bi bi-arrow-clockwise"></i> Refresh Data
              </button>
              <button class="btn btn-outline-secondary" @click="viewLogs">
                <i class="bi bi-journal-text"></i> View All Logs
              </button>
              <button class="btn btn-outline-info" @click="viewAnalysis">
                <i class="bi bi-bar-chart"></i> Advanced Analysis
              </button>
            </div>
          </div>
        </div>

        <!-- System Info -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-info-circle"></i> System Information
            </h5>
          </div>
          <div class="card-body">
            <div class="row text-center">
              <div class="col-6">
                <div class="border-end">
                  <h6 class="text-muted">Mode</h6>
                  <span class="badge bg-warning">Test</span>
                </div>
              </div>
              <div class="col-6">
                <h6 class="text-muted">Version</h6>
                <span class="text-primary">1.0.0</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Performance Metrics -->
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">
              <i class="bi bi-trophy"></i> Performance
            </h5>
          </div>
          <div class="card-body">
            <div class="row text-center">
              <div class="col-6">
                <h6 class="text-muted">Win Rate</h6>
                <h5 class="text-success">0%</h5>
              </div>
              <div class="col-6">
                <h6 class="text-muted">Total P&L</h6>
                <h5 class="text-primary">$0.00</h5>
              </div>
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
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

export default {
  name: 'Dashboard',
  components: {
    Line
  },
  data() {
    return {
      uptime: '00:00:00',
      recentLogs: [],
      tradingChart: null,
      startTime: Date.now()
    }
  },
  mounted() {
    this.updateUptime()
    this.loadData()
    setInterval(this.updateUptime, 1000)
    setInterval(this.loadData, 30000) // Refresh every 30 seconds
  },
  methods: {
    updateUptime() {
      const elapsed = Date.now() - this.startTime
      const hours = Math.floor(elapsed / 3600000)
      const minutes = Math.floor((elapsed % 3600000) / 60000)
      const seconds = Math.floor((elapsed % 60000) / 1000)
      this.uptime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    },

    async loadData() {
      try {
        // Load logs from Flask API
        const logsResponse = await axios.get('http://localhost:8080/logs')
        this.recentLogs = logsResponse.data.logs || []

        // Load trading data from Laravel API
        const tradingResponse = await axios.get('http://localhost:8000/api/analysis/trading-data')
        // Process trading data for chart
        this.updateChart(tradingResponse.data)
      } catch (error) {
        console.error('Error loading data:', error)
      }
    },

    updateChart(data) {
      if (!this.$refs.tradingChart) return

      const ctx = this.$refs.tradingChart.getContext('2d')

      if (this.tradingChart) {
        this.tradingChart.destroy()
      }

      // Sample data for demonstration
      const labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
      const balanceData = [100, 102, 98, 105, 103, 108]

      this.tradingChart = new ChartJS(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Account Balance ($)',
            data: balanceData,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            tension: 0.1
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
              text: 'Account Balance Over Time'
            }
          }
        }
      })
    },

    formatTime(timestamp) {
      return new Date(timestamp).toLocaleTimeString()
    },

    getLogBadgeClass(level) {
      const classes = {
        'INFO': 'bg-info',
        'ERROR': 'bg-danger',
        'WARNING': 'bg-warning',
        'SUCCESS': 'bg-success'
      }
      return classes[level] || 'bg-secondary'
    },

    refreshData() {
      this.loadData()
    },

    viewLogs() {
      this.$router.push('/logs')
    },

    viewAnalysis() {
      this.$router.push('/analysis')
    }
  }
}
</script>

<style scoped>
.chart-container {
  height: 300px;
  width: 100%;
}

.card {
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
}

.display-4 {
  font-size: 2.5rem;
}

.badge {
  font-size: 0.75em;
}
</style>