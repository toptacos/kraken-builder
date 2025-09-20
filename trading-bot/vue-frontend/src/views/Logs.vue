<template>
  <div>
    <div class="row mb-4">
      <div class="col-12">
        <h1 class="mb-3">
          <i class="bi bi-journal-text text-primary"></i> System Logs
        </h1>
        <p class="text-muted">Monitor system activity and trading bot operations</p>
      </div>
    </div>

    <!-- Log Filters -->
    <div class="card mb-4">
      <div class="card-header">
        <h5 class="mb-0">
          <i class="bi bi-funnel"></i> Log Filters
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-3">
            <label class="form-label">Log Level</label>
            <select class="form-select" v-model="filters.level">
              <option value="">All Levels</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
              <option value="SUCCESS">Success</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Time Range</label>
            <select class="form-select" v-model="filters.timeRange">
              <option value="1h">Last Hour</option>
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="all">All Time</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label">Search</label>
            <input type="text" class="form-control" v-model="filters.search" placeholder="Search logs...">
          </div>
          <div class="col-md-3">
            <label class="form-label">&nbsp;</label>
            <div>
              <button class="btn btn-primary w-100" @click="loadLogs">
                <i class="bi bi-search"></i> Filter
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Log Statistics -->
    <div class="row mb-4">
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-info-circle display-4 text-info mb-2"></i>
            <h5 class="card-title">{{ stats.total }}</h5>
            <p class="card-text text-muted">Total Logs</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-exclamation-triangle display-4 text-warning mb-2"></i>
            <h5 class="card-title">{{ stats.warnings }}</h5>
            <p class="card-text text-muted">Warnings</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-x-circle display-4 text-danger mb-2"></i>
            <h5 class="card-title">{{ stats.errors }}</h5>
            <p class="card-text text-muted">Errors</p>
          </div>
        </div>
      </div>
      <div class="col-md-3">
        <div class="card">
          <div class="card-body text-center">
            <i class="bi bi-check-circle display-4 text-success mb-2"></i>
            <h5 class="card-title">{{ stats.success }}</h5>
            <p class="card-text text-muted">Success</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Logs Table -->
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="bi bi-list-ul"></i> Log Entries
        </h5>
        <div class="btn-group">
          <button class="btn btn-sm btn-outline-secondary" @click="autoRefresh = !autoRefresh">
            <i :class="autoRefresh ? 'bi bi-pause' : 'bi bi-play'"></i>
            {{ autoRefresh ? 'Pause' : 'Auto Refresh' }}
          </button>
          <button class="btn btn-sm btn-outline-primary" @click="exportLogs">
            <i class="bi bi-download"></i> Export
          </button>
        </div>
      </div>
      <div class="card-body">
        <div v-if="loading" class="text-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <p class="mt-2 text-muted">Loading logs...</p>
        </div>

        <div v-else-if="logs.length === 0" class="text-center py-4">
          <i class="bi bi-info-circle display-4 text-muted mb-3"></i>
          <h5 class="text-muted">No logs found</h5>
          <p class="text-muted">Try adjusting your filters or check if the bot is running.</p>
        </div>

        <div v-else class="table-responsive">
          <table class="table table-hover">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Message</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in paginatedLogs" :key="log.timestamp + log.message" :class="getLogRowClass(log.level)">
                <td>{{ formatTimestamp(log.timestamp) }}</td>
                <td>
                  <span :class="getLogBadgeClass(log.level)" class="badge">
                    {{ log.level }}
                  </span>
                </td>
                <td>
                  <div class="log-message">{{ log.message }}</div>
                </td>
                <td>
                  <button class="btn btn-sm btn-outline-info" @click="showLogDetails(log)">
                    <i class="bi bi-eye"></i>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <nav v-if="totalPages > 1" class="mt-3">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="goToPage(currentPage - 1)">Previous</a>
            </li>
            <li v-for="page in visiblePages" :key="page" class="page-item" :class="{ active: page === currentPage }">
              <a class="page-link" href="#" @click.prevent="goToPage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="goToPage(currentPage + 1)">Next</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- Log Details Modal -->
    <div class="modal fade" id="logDetailsModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Log Details</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <div v-if="selectedLog">
              <div class="row mb-3">
                <div class="col-sm-3"><strong>Timestamp:</strong></div>
                <div class="col-sm-9">{{ formatTimestamp(selectedLog.timestamp) }}</div>
              </div>
              <div class="row mb-3">
                <div class="col-sm-3"><strong>Level:</strong></div>
                <div class="col-sm-9">
                  <span :class="getLogBadgeClass(selectedLog.level)" class="badge">
                    {{ selectedLog.level }}
                  </span>
                </div>
              </div>
              <div class="row mb-3">
                <div class="col-sm-3"><strong>Message:</strong></div>
                <div class="col-sm-9">
                  <pre class="bg-light p-2 rounded">{{ selectedLog.message }}</pre>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Logs',
  data() {
    return {
      logs: [],
      filteredLogs: [],
      loading: false,
      autoRefresh: true,
      selectedLog: null,
      currentPage: 1,
      perPage: 25,
      filters: {
        level: '',
        timeRange: '24h',
        search: ''
      },
      stats: {
        total: 0,
        warnings: 0,
        errors: 0,
        success: 0
      }
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.filteredLogs.length / this.perPage)
    },
    paginatedLogs() {
      const start = (this.currentPage - 1) * this.perPage
      const end = start + this.perPage
      return this.filteredLogs.slice(start, end)
    },
    visiblePages() {
      const pages = []
      const start = Math.max(1, this.currentPage - 2)
      const end = Math.min(this.totalPages, this.currentPage + 2)

      for (let i = start; i <= end; i++) {
        pages.push(i)
      }

      return pages
    }
  },
  mounted() {
    this.loadLogs()
    if (this.autoRefresh) {
      setInterval(this.loadLogs, 30000) // Refresh every 30 seconds
    }
  },
  methods: {
    async loadLogs() {
      this.loading = true
      try {
        let url = 'http://localhost:8080/logs'
        if (this.filters.level) {
          url = `http://localhost:8080/logs/${this.filters.level}`
        }

        const response = await axios.get(url)
        this.logs = response.data.logs || []
        this.applyFilters()
        this.calculateStats()
      } catch (error) {
        console.error('Error loading logs:', error)
        this.logs = []
        this.filteredLogs = []
      } finally {
        this.loading = false
      }
    },

    applyFilters() {
      let filtered = [...this.logs]

      // Apply search filter
      if (this.filters.search) {
        const searchTerm = this.filters.search.toLowerCase()
        filtered = filtered.filter(log =>
          log.message.toLowerCase().includes(searchTerm) ||
          log.level.toLowerCase().includes(searchTerm)
        )
      }

      // Apply time range filter
      if (this.filters.timeRange !== 'all') {
        const now = new Date()
        const timeLimit = this.getTimeLimit(this.filters.timeRange)
        filtered = filtered.filter(log => {
          const logTime = new Date(log.timestamp)
          return (now - logTime) <= timeLimit
        })
      }

      this.filteredLogs = filtered
      this.currentPage = 1
    },

    getTimeLimit(range) {
      const multipliers = {
        '1h': 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        '7d': 7 * 24 * 60 * 60 * 1000
      }
      return multipliers[range] || 0
    },

    calculateStats() {
      this.stats = {
        total: this.logs.length,
        warnings: this.logs.filter(log => log.level === 'WARNING').length,
        errors: this.logs.filter(log => log.level === 'ERROR').length,
        success: this.logs.filter(log => log.level === 'SUCCESS').length
      }
    },

    formatTimestamp(timestamp) {
      return new Date(timestamp).toLocaleString()
    },

    getLogBadgeClass(level) {
      const classes = {
        'INFO': 'bg-info',
        'WARNING': 'bg-warning',
        'ERROR': 'bg-danger',
        'SUCCESS': 'bg-success'
      }
      return classes[level] || 'bg-secondary'
    },

    getLogRowClass(level) {
      const classes = {
        'ERROR': 'table-danger',
        'WARNING': 'table-warning',
        'SUCCESS': 'table-success'
      }
      return classes[level] || ''
    },

    showLogDetails(log) {
      this.selectedLog = log
      // In a real Vue app, you'd use a modal library
      alert(`Log Details:\n\nTimestamp: ${this.formatTimestamp(log.timestamp)}\nLevel: ${log.level}\nMessage: ${log.message}`)
    },

    goToPage(page) {
      if (page >= 1 && page <= this.totalPages) {
        this.currentPage = page
      }
    },

    exportLogs() {
      const dataStr = JSON.stringify(this.filteredLogs, null, 2)
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)

      const exportFileDefaultName = `trading_bot_logs_${new Date().toISOString().split('T')[0]}.json`

      const linkElement = document.createElement('a')
      linkElement.setAttribute('href', dataUri)
      linkElement.setAttribute('download', exportFileDefaultName)
      linkElement.click()
    }
  },
  watch: {
    'filters.level'() {
      this.loadLogs()
    },
    'filters.search'() {
      this.applyFilters()
    },
    'filters.timeRange'() {
      this.applyFilters()
    }
  }
}
</script>

<style scoped>
.log-message {
  max-width: 500px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.table-responsive {
  max-height: 600px;
  overflow-y: auto;
}

.pagination .page-link {
  color: #007bff;
}

.pagination .page-item.active .page-link {
  background-color: #007bff;
  border-color: #007bff;
}
</style>