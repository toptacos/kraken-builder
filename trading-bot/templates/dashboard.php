<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kraken Trading Bot - Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-3xl font-bold text-blue-400">
                <i class="fas fa-chart-line mr-2"></i>Kraken Trading Bot
            </h1>
            <div class="flex space-x-4">
                <button id="startTrading" class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-play mr-2"></i>Start Trading
                </button>
                <button id="stopTrading" class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-stop mr-2"></i>Stop Trading
                </button>
                <button id="refreshData" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-sync-alt mr-2"></i>Refresh
                </button>
            </div>
        </div>

        <!-- Status Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-gray-800 rounded-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Balance</p>
                        <p id="balance" class="text-2xl font-bold text-green-400">$1,000.00</p>
                    </div>
                    <i class="fas fa-dollar-sign text-green-400 text-2xl"></i>
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Daily P&L</p>
                        <p id="dailyPnL" class="text-2xl font-bold text-blue-400">+$25.50</p>
                    </div>
                    <i class="fas fa-chart-line text-blue-400 text-2xl"></i>
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">Active Positions</p>
                        <p id="activePositions" class="text-2xl font-bold text-purple-400">3</p>
                    </div>
                    <i class="fas fa-briefcase text-purple-400 text-2xl"></i>
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-400 text-sm">System Status</p>
                        <p id="systemStatus" class="text-2xl font-bold text-green-400">Healthy</p>
                    </div>
                    <i class="fas fa-heartbeat text-green-400 text-2xl"></i>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <!-- P&L Chart -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-4">Profit & Loss</h3>
                <canvas id="pnlChart" width="400" height="200"></canvas>
            </div>

            <!-- Portfolio Allocation -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-4">Portfolio Allocation</h3>
                <canvas id="portfolioChart" width="400" height="200"></canvas>
            </div>
        </div>

        <!-- Trading Activity & Logs -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Recent Trades -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-4">Recent Trades</h3>
                <div id="recentTrades" class="space-y-3 max-h-96 overflow-y-auto">
                    <!-- Trades will be loaded here -->
                </div>
            </div>

            <!-- Live Logs -->
            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-xl font-bold mb-4">Live Trading Logs</h3>
                <div id="liveLogs" class="bg-black rounded p-4 font-mono text-sm max-h-96 overflow-y-auto">
                    <!-- Logs will be loaded here -->
                </div>
            </div>
        </div>

        <!-- X/Twitter Prompts Section -->
        <div class="mt-8 bg-gray-800 rounded-lg p-6">
            <h3 class="text-xl font-bold mb-4">
                <i class="fab fa-twitter text-blue-400 mr-2"></i>Market Insights from X
            </h3>
            <div class="flex space-x-4 mb-4">
                <button id="scrapePrompts" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-search mr-2"></i>Scrape Latest Prompts
                </button>
                <button id="generatePrompts" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg transition-colors">
                    <i class="fas fa-magic mr-2"></i>Generate AI Prompts
                </button>
            </div>
            <div id="promptsContainer" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <!-- Prompts will be loaded here -->
            </div>
        </div>
    </div>

    <script>
        // Global state
        let charts = {};
        let wsConnection = null;

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeCharts();
            setupWebSocket();
            setupEventListeners();
            loadInitialData();
            startAutoRefresh();
        });

        // Initialize charts
        function initializeCharts() {
            // P&L Chart
            const pnlCtx = document.getElementById('pnlChart').getContext('2d');
            charts.pnl = new Chart(pnlCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'P&L',
                        data: [],
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        x: {
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: 'white' } }
                    }
                }
            });

            // Portfolio Chart
            const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
            charts.portfolio = new Chart(portfolioCtx, {
                type: 'doughnut',
                data: {
                    labels: [],
                    datasets: [{
                        data: [],
                        backgroundColor: [
                            'rgb(59, 130, 246)',
                            'rgb(147, 51, 234)',
                            'rgb(34, 197, 94)',
                            'rgb(239, 68, 68)',
                            'rgb(245, 158, 11)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { labels: { color: 'white' } }
                    }
                }
            });
        }

        // Setup WebSocket connection
        function setupWebSocket() {
            if (typeof WebSocket !== 'undefined') {
                wsConnection = new WebSocket('ws://localhost:8081');

                wsConnection.onopen = function() {
                    console.log('WebSocket connected');
                };

                wsConnection.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleRealTimeUpdate(data);
                };

                wsConnection.onclose = function() {
                    console.log('WebSocket disconnected');
                    setTimeout(setupWebSocket, 5000); // Reconnect after 5 seconds
                };

                wsConnection.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
        }

        // Setup event listeners
        function setupEventListeners() {
            document.getElementById('startTrading').addEventListener('click', startTrading);
            document.getElementById('stopTrading').addEventListener('click', stopTrading);
            document.getElementById('refreshData').addEventListener('click', loadInitialData);
            document.getElementById('scrapePrompts').addEventListener('click', scrapePrompts);
            document.getElementById('generatePrompts').addEventListener('click', generatePrompts);
        }

        // Load initial data
        async function loadInitialData() {
            try {
                const [statusResponse, portfolioResponse, tradesResponse, analyticsResponse] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/portfolio'),
                    fetch('/api/trades?limit=10'),
                    fetch('/api/analytics')
                ]);

                const status = await statusResponse.json();
                const portfolio = await portfolioResponse.json();
                const trades = await tradesResponse.json();
                const analytics = await analyticsResponse.json();

                updateStatusCards(status);
                updatePortfolioChart(portfolio);
                updateTradesList(trades.trades);
                updatePnLChart(analytics.profit_loss);

            } catch (error) {
                console.error('Error loading data:', error);
            }
        }

        // Update status cards
        function updateStatusCards(status) {
            document.getElementById('balance').textContent = `$${status.current_balance.toFixed(2)}`;
            document.getElementById('dailyPnL').textContent = `$${status.daily_pnl.toFixed(2)}`;
            document.getElementById('activePositions').textContent = status.active_positions;
            document.getElementById('systemStatus').textContent = status.trading_active ? 'Active' : 'Inactive';
            document.getElementById('systemStatus').className = status.trading_active ?
                'text-2xl font-bold text-green-400' : 'text-2xl font-bold text-red-400';
        }

        // Update portfolio chart
        function updatePortfolioChart(portfolio) {
            const allocations = portfolio.allocations;
            charts.portfolio.data.labels = Object.keys(allocations);
            charts.portfolio.data.datasets[0].data = Object.values(allocations);
            charts.portfolio.update();
        }

        // Update P&L chart
        function updatePnLChart(pnlData) {
            charts.pnl.data.labels = pnlData.labels;
            charts.pnl.data.datasets[0].data = pnlData.data;
            charts.pnl.update();
        }

        // Update trades list
        function updateTradesList(trades) {
            const container = document.getElementById('recentTrades');
            container.innerHTML = '';

            trades.forEach(trade => {
                const tradeElement = document.createElement('div');
                tradeElement.className = 'flex justify-between items-center p-3 bg-gray-700 rounded';
                tradeElement.innerHTML = `
                    <div>
                        <span class="font-bold ${trade.side === 'buy' ? 'text-green-400' : 'text-red-400'}">
                            ${trade.side.toUpperCase()}
                        </span>
                        <span class="text-gray-300">${trade.symbol}</span>
                    </div>
                    <div class="text-right">
                        <div class="font-bold">${trade.amount}</div>
                        <div class="text-sm text-gray-400">$${trade.price}</div>
                    </div>
                `;
                container.appendChild(tradeElement);
            });
        }

        // Handle real-time updates
        function handleRealTimeUpdate(data) {
            if (data.type === 'trade') {
                addNewTrade(data.trade);
                updateStatusCards(data.status);
            } else if (data.type === 'log') {
                addLogEntry(data.message);
            } else if (data.type === 'status') {
                updateStatusCards(data.status);
            }
        }

        // Add new trade to list
        function addNewTrade(trade) {
            const container = document.getElementById('recentTrades');
            const tradeElement = document.createElement('div');
            tradeElement.className = 'flex justify-between items-center p-3 bg-gray-700 rounded animate-pulse';
            tradeElement.innerHTML = `
                <div>
                    <span class="font-bold ${trade.side === 'buy' ? 'text-green-400' : 'text-red-400'}">
                        ${trade.side.toUpperCase()}
                    </span>
                    <span class="text-gray-300">${trade.symbol}</span>
                </div>
                <div class="text-right">
                    <div class="font-bold">${trade.amount}</div>
                    <div class="text-sm text-gray-400">$${trade.price}</div>
                </div>
            `;

            container.insertBefore(tradeElement, container.firstChild);

            // Remove animation after 2 seconds
            setTimeout(() => {
                tradeElement.classList.remove('animate-pulse');
            }, 2000);
        }

        // Add log entry
        function addLogEntry(message) {
            const container = document.getElementById('liveLogs');
            const logElement = document.createElement('div');
            logElement.className = 'text-gray-300 py-1';
            logElement.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;

            container.appendChild(logElement);
            container.scrollTop = container.scrollHeight;
        }

        // Trading controls
        async function startTrading() {
            try {
                const response = await fetch('/api/trading/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        strategy: 'default',
                        amount: 100
                    })
                });

                const result = await response.json();
                if (result.status === 'started') {
                    addLogEntry('✅ Trading started successfully');
                } else {
                    addLogEntry('❌ Failed to start trading');
                }
            } catch (error) {
                console.error('Error starting trading:', error);
                addLogEntry('❌ Error starting trading');
            }
        }

        async function stopTrading() {
            try {
                const response = await fetch('/api/trading/stop', { method: 'POST' });
                const result = await response.json();
                addLogEntry('🛑 Trading stop signal sent');
            } catch (error) {
                console.error('Error stopping trading:', error);
                addLogEntry('❌ Error stopping trading');
            }
        }

        // X/Twitter functionality
        async function scrapePrompts() {
            try {
                const response = await fetch('/api/prompts', { method: 'POST' });
                const result = await response.json();

                displayPrompts(result.prompts);
                addLogEntry(`📊 Scraped ${result.prompts.length} prompts from X`);
            } catch (error) {
                console.error('Error scraping prompts:', error);
                addLogEntry('❌ Error scraping prompts from X');
            }
        }

        async function generatePrompts() {
            try {
                const response = await fetch('/api/prompts');
                const result = await response.json();

                displayPrompts(result.prompts);
                addLogEntry('🤖 Generated AI trading prompts');
            } catch (error) {
                console.error('Error generating prompts:', error);
                addLogEntry('❌ Error generating prompts');
            }
        }

        function displayPrompts(prompts) {
            const container = document.getElementById('promptsContainer');
            container.innerHTML = '';

            prompts.forEach(prompt => {
                const promptElement = document.createElement('div');
                promptElement.className = 'bg-gray-700 p-4 rounded-lg';
                promptElement.innerHTML = `
                    <p class="text-sm text-gray-300">${prompt}</p>
                    <button class="mt-2 text-blue-400 hover:text-blue-300 text-sm">
                        <i class="fas fa-copy mr-1"></i>Use Prompt
                    </button>
                `;
                container.appendChild(promptElement);
            });
        }

        // Auto refresh every 30 seconds
        function startAutoRefresh() {
            setInterval(loadInitialData, 30000);
        }
    </script>
</body>
</html>