<template>
  <div class="trading-dashboard">
    <div class="dashboard-header">
      <h1>🚀 Kraken Trading Bot Dashboard</h1>
      <div class="status-indicators">
        <div class="status-item">
          <span class="status-dot" :class="healthStatusClass"></span>
          <span>{{ healthStatusText }}</span>
        </div>
        <div class="status-item">
          <span class="metric-value">${{ currentBalance }}</span>
          <span>Balance</span>
        </div>
        <div class="status-item">
          <span class="metric-value">{{ winRate }}%</span>
          <span>Win Rate</span>
        </div>
      </div>
    </div>

    <div class="dashboard-controls">
      <button
        class="btn btn-primary"
        @click="refreshData"
        :disabled="loading"
      >
        <span v-if="loading" class="spinner"></span>
        {{ loading ? 'Refreshing...' : '🔄 Refresh Data' }}
      </button>

      <button
        class="btn btn-secondary"
        @click="runTestTrade"
        :disabled="loading"
      >
        🧪 Test Trade
      </button>

      <button
        class="btn btn-warning"
        @click="runTradingCycle"
        :disabled="loading"
      >
        ⚡ Run Cycle
      </button>

      <div class="auto-refresh">
        <label>
          <input
            type="checkbox"
            v-model="autoRefresh"
            @change="toggleAutoRefresh"
          />
          Auto-refresh (5s)
        </label>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- System Health Card -->
      <div class="card">
        <h3>🖥️ System Health</h3>
        <div class="metric">
          <span>Status:</span>
          <span class="metric-value" :class="healthStatusClass">
            {{ health?.status || 'Unknown' }}
          </span>
        </div>
        <div class="metric">
          <span>Test Mode:</span>
          <span class="metric-value">
            {{ health?.test_mode ? 'Yes' : 'No' }}
          </span>
        </div>
        <div class="metric">
          <span>Exchanges:</span>
          <span class="metric-value">
            {{ health?.exchanges_configured || 0 }}
          </span>
        </div>
        <div class="metric">
          <span>Last Update:</span>
          <span class="metric-value">{{ formatTimestamp(health?.timestamp) }}</span>
        </div>
      </div>

      <!-- Portfolio Card -->
      <div class="card">
        <h3>💰 Portfolio</h3>
        <div v-if="portfolio.length === 0" class="metric">
          <span>No assets</span>
          <span class="metric-value">-</span>
        </div>
        <div v-else v-for="asset in portfolio" :key="asset.symbol" class="portfolio-item">
          <span>{{ asset.symbol }}</span>
          <span class="metric-value">{{ asset.amount }}</span>
        </div>
      </div>

      <!-- Current Position Card -->
      <div class="card">
        <h3>📊 Current Position</h3>
        <div class="metric">
          <span>Status:</span>
          <span class="metric-value">{{ currentPosition || 'No Position' }}</span>
        </div>
        <div class="metric">
          <span>Balance:</span>
          <span class="metric-value">${{ currentBalance || '0.00' }}</span>
        </div>
        <div class="metric">
          <span>Last Signal:</span>
          <span class="metric-value">{{ lastSignal || 'None' }}</span>
        </div>
      </div>

      <!-- Trading Statistics Card -->
      <div class="card">
        <h3>📈 Trading Statistics</h3>
        <div class="metric">
          <span>Total Trades:</span>
          <span class="metric-value">{{ statistics.total_trades || 0 }}</span>
        </div>
        <div class="metric">
          <span>Profitable:</span>
          <span class="metric-value">{{ statistics.profitable_trades || 0 }}</span>
        </div>
        <div class="metric">
          <span>Win Rate:</span>
          <span class="metric-value">{{ statistics.win_rate || 0 }}%</span>
        </div>
        <div class="metric">
          <span>Total P&L:</span>
          <span class="metric-value" :class="statistics.total_profit >= 0 ? 'positive' : 'negative'">
            ${{ statistics.total_profit || 0 }}
          </span>
        </div>
      </div>

      <!-- Trending Coin Card -->
      <div class="card">
        <h3>🔥 Trending Coin</h3>
        <div class="metric">
          <span>Coin:</span>
          <span class="metric-value">{{ trendingCoin || 'Loading...' }}</span>
        </div>
        <div class="metric">
          <span>Symbol:</span>
          <span class="metric-value">{{ trendingSymbol || '-' }}</span>
        </div>
      </div>

      <!-- Recent Trades Card -->
      <div class="card">
        <h3>📋 Recent Trades</h3>
        <div v-if="recentTrades.length === 0" class="no-data">
          No recent trades
        </div>
        <div v-else v-for="trade in recentTrades.slice(0, 5)" :key="trade.id" class="trade-item">
          <div class="trade-info">
            <span class="trade-level" :class="getTradeClass(trade.level)">
              {{ trade.level }}
            </span>
            <span class="trade-message">{{ trade.message }}</span>
          </div>
          <div class="trade-time">{{ formatTimestamp(trade.timestamp) }}</div>
        </div>
      </div>
    </div>

    <!-- Logs Section -->
    <div class="logs-section">
      <h3>📋 System Logs</h3>
      <div class="logs-controls">
        <button
          class="btn btn-sm"
          :class="logFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'"
          @click="setLogFilter('ALL')"
        >
          All
        </button>
        <button
          class="btn btn-sm"
          :class="logFilter === 'INFO' ? 'btn-primary' : 'btn-secondary'"
          @click="setLogFilter('INFO')"
        >
          Info
        </button>
        <button
          class="btn btn-sm"
          :class="logFilter === 'ERROR' ? 'btn-primary' : 'btn-secondary'"
          @click="setLogFilter('ERROR')"
        >
          Errors
        </button>
        <button
          class="btn btn-sm"
          :class="logFilter === 'WARNING' ? 'btn-primary' : 'btn-secondary'"
          @click="setLogFilter('WARNING')"
        >
          Warnings
        </button>
      </div>

      <div class="logs-container">
        <div v-if="logs.length === 0" class="no-data">
          No logs available
        </div>
        <div v-else v-for="log in filteredLogs" :key="log.timestamp" class="log-entry" :class="getLogClass(log.level)">
          <div class="log-time">{{ formatTimestamp(log.timestamp) }}</div>
          <div class="log-level">[{{ log.level }}]</div>
          <div class="log-message">{{ log.message }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TradingDashboard',
  data() {
    return {
      health: null,
      portfolio: [],
      currentPosition: null,
      currentBalance: 0,
      lastSignal: null,
      trendingCoin: null,
      trendingSymbol: null,
      logs: [],
      statistics: {},
      recentTrades: [],
      loading: false,
      autoRefresh: false,
      refreshInterval: null,
      logFilter: 'ALL',
      lastUpdate: new Date().toLocaleTimeString()
    }
  },

  computed: {
    healthStatusClass() {
      if (!this.health) return 'status-error'
      return this.health.status === 'healthy' ? 'status-healthy' : 'status-warning'
    },

    healthStatusText() {
      if (!this.health) return 'Unknown'
      return this.health.status === 'healthy' ? 'Healthy' : 'Warning'
    },

    filteredLogs() {
      if (this.logFilter === 'ALL') return this.logs.slice(0, 50)
      return this.logs.filter(log => log.level === this.logFilter).slice(0, 50)
    }
  },

  methods: {
    async refreshData() {
      this.loading = true
      try {
        // Fetch dashboard data from Laravel API
        const response = await axios.get('/api/trading/dashboard')
        const data = response.data.data

        this.health = data.health
        this.portfolio = data.status?.portfolio || []
        this.currentPosition = data.status?.position
        this.currentBalance = data.status?.current_balance || 0
        this.lastSignal = data.status?.last_signal
        this.logs = data.logs?.logs || []
        this.statistics = data.statistics || {}
        this.recentTrades = data.recent_trades || []

        // Mock trending data (would come from Flask API)
        this.trendingCoin = 'BTC'
        this.trendingSymbol = 'BTC/USDT'

        this.lastUpdate = new Date().toLocaleTimeString()

        this.$emit('data-updated', data)

      } catch (error) {
        console.error('Error refreshing data:', error)
        this.logs.unshift({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `Failed to refresh data: ${error.message}`
        })
      } finally {
        this.loading = false
      }
    },

    async runTestTrade() {
      try {
        const response = await axios.post('/api/trading/test-trade')
        this.logs.unshift({
          timestamp: new Date().toISOString(),
          level: 'INFO',
          message: `Test trade executed: ${response.data.message || 'Success'}`
        })
        await this.refreshData()
      } catch (error) {
        this.logs.unshift({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `Test trade failed: ${error.message}`
        })
      }
    },

    async runTradingCycle() {
      try {
        const response = await axios.post('/api/trading/run-cycle')
        this.logs.unshift({
          timestamp: new Date().toISOString(),
          level: 'INFO',
          message: `Trading cycle executed: ${response.data.message || 'Success'}`
        })
        await this.refreshData()
      } catch (error) {
        this.logs.unshift({
          timestamp: new Date().toISOString(),
          level: 'ERROR',
          message: `Trading cycle failed: ${error.message}`
        })
      }
    },

    toggleAutoRefresh() {
      if (this.autoRefresh) {
        this.refreshInterval = setInterval(() => {
          this.refreshData()
        }, 5000) // Refresh every 5 seconds
      } else {
        if (this.refreshInterval) {
          clearInterval(this.refreshInterval)
          this.refreshInterval = null
        }
      }
    },

    setLogFilter(filter) {
      this.logFilter = filter
    },

    formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A'
      return new Date(timestamp).toLocaleString()
    },

    getLogClass(level) {
      const classes = {
        'INFO': 'log-info',
        'ERROR': 'log-error',
        'WARNING': 'log-warning',
        'SUCCESS': 'log-success'
      }
      return classes[level] || 'log-info'
    },

    getTradeClass(level) {
      const classes = {
        'INFO': 'trade-info',
        'ERROR': 'trade-error',
        'WARNING': 'trade-warning',
        'SUCCESS': 'trade-success'
      }
      return classes[level] || 'trade-info'
    }
  },

  mounted() {
    // Initial data load
    this.refreshData()

    // Cleanup on component destroy
    this.$on('hook:beforeDestroy', () => {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval)
      }
    })
  },

  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  }
}
</script>

<style scoped>
.trading-dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 2.5em;
}

.status-indicators {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 20px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-healthy { background-color: #27ae60; }
.status-warning { background-color: #f39c12; }
.status-error { background-color: #e74c3c; }

.dashboard-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
  flex-wrap: wrap;
  align-items: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #e67e22;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 12px;
}

.auto-refresh {
  display: flex;
  align-items: center;
  gap: 8px;
}

.auto-refresh label {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  font-weight: 500;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #ffffff;
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  border: 1px solid #e1e8ed;
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card h3 {
  color: #2c3e50;
  margin-bottom: 20px;
  font-size: 1.3em;
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.metric:last-child {
  border-bottom: none;
}

.metric-value {
  font-weight: 600;
  color: #667eea;
  font-size: 1.1em;
}

.metric-value.positive {
  color: #27ae60;
}

.metric-value.negative {
  color: #e74c3c;
}

.portfolio-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.portfolio-item:last-child {
  border-bottom: none;
}

.trade-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.trade-item:last-child {
  border-bottom: none;
}

.trade-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.trade-level {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  font-weight: 600;
}

.trade-info { background: #e8f5e8; color: #27ae60; }
.trade-error { background: #fdeaea; color: #e74c3c; }
.trade-warning { background: #fff3cd; color: #856404; }

.trade-time {
  font-size: 0.9em;
  color: #6c757d;
}

.logs-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  border: 1px solid #e1e8ed;
}

.logs-controls {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.logs-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  background: #f8f9fa;
}

.log-entry {
  padding: 12px 16px;
  border-bottom: 1px solid #e1e8ed;
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-time {
  font-size: 0.9em;
  color: #6c757d;
  min-width: 140px;
}

.log-level {
  font-weight: 600;
  min-width: 70px;
  text-align: center;
}

.log-message {
  flex: 1;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 0.9em;
}

.log-info { background: #f0f8ff; }
.log-error { background: #fef2f2; border-left: 4px solid #e74c3c; }
.log-warning { background: #fffbeb; border-left: 4px solid #f59e0b; }
.log-success { background: #f0fdf4; border-left: 4px solid #10b981; }

.no-data {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  font-style: italic;
}

/* Responsive Design */
@media (max-width: 768px) {
  .trading-dashboard {
    padding: 15px;
  }

  .dashboard-header h1 {
    font-size: 2em;
  }

  .status-indicators {
    flex-direction: column;
    gap: 15px;
  }

  .dashboard-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .logs-controls {
    justify-content: center;
  }

  .log-entry {
    flex-direction: column;
    gap: 5px;
  }
}
</style>