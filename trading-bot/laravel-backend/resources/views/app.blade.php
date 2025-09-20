<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>🚀 Kraken Trading Bot - Vue.js Dashboard</title>

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    <!-- Styles -->
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #1a202c;
        }

        #app {
            min-height: 100vh;
        }

        .loading-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading-text {
            font-size: 1.2em;
            font-weight: 500;
            text-align: center;
        }

        .loading-subtext {
            font-size: 0.9em;
            opacity: 0.8;
            margin-top: 10px;
            text-align: center;
        }

        .error-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 20px;
        }

        .error-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }

        .error-title {
            font-size: 2em;
            font-weight: 700;
            margin-bottom: 10px;
            text-align: center;
        }

        .error-message {
            font-size: 1.1em;
            text-align: center;
            margin-bottom: 30px;
            max-width: 600px;
        }

        .retry-btn {
            background: white;
            color: #e74c3c;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .retry-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div id="loading-screen" class="loading-screen">
        <div class="loading-spinner"></div>
        <div class="loading-text">🚀 Initializing Kraken Trading Bot</div>
        <div class="loading-subtext">Loading Vue.js dashboard and connecting to trading systems...</div>
    </div>

    <!-- Error Screen (hidden by default) -->
    <div id="error-screen" class="error-screen" style="display: none;">
        <div class="error-icon">⚠️</div>
        <div class="error-title">Connection Error</div>
        <div class="error-message">
            Unable to connect to the trading backend. Please check if the Flask API is running and try again.
        </div>
        <button class="retry-btn" onclick="retryConnection()">Retry Connection</button>
    </div>

    <!-- Main Vue App -->
    <div id="app" style="display: none;">
        <trading-dashboard @data-updated="onDataUpdated"></trading-dashboard>
    </div>

    <!-- Vue.js and Dependencies -->
    <script src="https://cdn.jsdelivr.net/npm/vue@3.4.0/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios@1.6.0/dist/axios.min.js"></script>

    <!-- Custom Scripts -->
    <script>
        // Configure Axios
        axios.defaults.baseURL = window.location.origin
        axios.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest'
        axios.defaults.headers.common['X-CSRF-TOKEN'] = document.querySelector('meta[name="csrf-token"]').getAttribute('content')

        // Global error handler
        window.onerror = function(msg, url, line, col, error) {
            console.error('JavaScript Error:', msg, 'at', url, line, col, error)
            showError('JavaScript Error: ' + msg)
            return false
        }

        // Connection management
        let connectionAttempts = 0
        const maxConnectionAttempts = 5

        function showLoading() {
            document.getElementById('loading-screen').style.display = 'flex'
            document.getElementById('app').style.display = 'none'
            document.getElementById('error-screen').style.display = 'none'
        }

        function showApp() {
            document.getElementById('loading-screen').style.display = 'none'
            document.getElementById('app').style.display = 'block'
            document.getElementById('error-screen').style.display = 'none'
        }

        function showError(message) {
            document.getElementById('loading-screen').style.display = 'none'
            document.getElementById('app').style.display = 'none'
            document.getElementById('error-screen').style.display = 'flex'

            if (message) {
                document.querySelector('.error-message').textContent = message
            }
        }

        function retryConnection() {
            connectionAttempts = 0
            initializeApp()
        }

        async function checkBackendHealth() {
            try {
                const response = await axios.get('/api/health', { timeout: 5000 })
                return response.data.status === 'healthy'
            } catch (error) {
                console.warn('Backend health check failed:', error.message)
                return false
            }
        }

        async function initializeApp() {
            try {
                showLoading()

                // Check backend health
                const isHealthy = await checkBackendHealth()

                if (!isHealthy) {
                    throw new Error('Backend services are not healthy')
                }

                // Load Vue app
                const { createApp } = Vue
                const { TradingDashboard } = await import('./js/app.js')

                const app = createApp({
                    components: {
                        TradingDashboard
                    },
                    data() {
                        return {
                            initialized: false
                        }
                    },
                    methods: {
                        onDataUpdated(data) {
                            console.log('Dashboard data updated:', data)
                            this.initialized = true
                        }
                    },
                    mounted() {
                        console.log('🚀 Kraken Trading Bot Vue.js Dashboard initialized')
                    }
                })

                // Mount the app
                app.mount('#app')

                // Show the app
                setTimeout(() => {
                    showApp()
                }, 1000)

            } catch (error) {
                console.error('Failed to initialize app:', error)

                connectionAttempts++
                if (connectionAttempts < maxConnectionAttempts) {
                    console.log(`Retrying connection (${connectionAttempts}/${maxConnectionAttempts})...`)
                    setTimeout(initializeApp, 2000)
                } else {
                    showError('Failed to connect to trading backend after ' + maxConnectionAttempts + ' attempts. Please check if the Flask API is running.')
                }
            }
        }

        // Initialize the app when page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Starting Kraken Trading Bot Vue.js Dashboard...')
            initializeApp()
        })

        // Handle page visibility changes
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) {
                console.log('Page became visible, checking connection...')
                checkBackendHealth().then(healthy => {
                    if (!healthy) {
                        console.warn('Backend connection lost')
                        // Could trigger reconnection logic here
                    }
                })
            }
        })

        // Global error handler for unhandled promise rejections
        window.addEventListener('unhandledrejection', function(event) {
            console.error('Unhandled promise rejection:', event.reason)
            showError('Application Error: ' + event.reason.message)
        })
    </script>
</body>
</html>