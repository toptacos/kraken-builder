# 🚀 Kraken Trading Bot - Full Stack Installation Guide

A comprehensive automated cryptocurrency trading bot with AI-powered analysis, multi-exchange support, and a modern Vue.js dashboard.

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start (Docker)](#quick-start-docker)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [API Setup](#api-setup)
- [Running the Application](#running-the-application)
- [Features Overview](#features-overview)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **RAM**: 4GB
- **Storage**: 2GB free space
- **Network**: Stable internet connection

### Recommended Requirements
- **OS**: macOS 12+, Ubuntu 20.04+
- **RAM**: 8GB
- **Storage**: 5GB free space
- **CPU**: Multi-core processor

### Software Dependencies
- **Docker & Docker Compose** (for containerized deployment)
- **Python 3.8+** (for manual installation)
- **PHP 8.1+** (for Laravel backend)
- **Node.js 16+** (for Vue.js frontend)
- **Composer** (PHP dependency manager)
- **npm or yarn** (Node.js package manager)

## 🐳 Quick Start (Docker)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/kraken-trading-bot.git
cd kraken-trading-bot
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional - defaults will work for testing)
nano .env
```

### 3. Launch with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Trading Bot Dashboard**: http://localhost:8080
- **Vue.js Frontend**: http://localhost:3000
- **Laravel API**: http://localhost:8000/api
- **Flask API**: http://localhost:8080/api

### 5. Stop the Application
```bash
docker-compose down
```

## 🔧 Manual Installation

### Step 1: Python Environment Setup

```bash
# Create virtual environment
python3 -m venv trading_env
source trading_env/bin/activate  # On Windows: trading_env\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install additional packages for analysis
pip install pandas numpy scikit-learn tensorflow
```

### Step 2: PHP/Laravel Backend Setup

```bash
# Navigate to Laravel backend
cd laravel-backend

# Install PHP dependencies
composer install

# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate

# Set up database (optional - uses SQLite by default)
touch database/database.sqlite
php artisan migrate
```

### Step 3: Vue.js Frontend Setup

```bash
# Navigate to Vue.js frontend
cd vue-frontend

# Install Node.js dependencies
npm install

# Build for production (or use dev server)
npm run build
```

### Step 4: Configuration

#### Flask API Configuration (.env)
```env
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_PORT=8080

# Trading Configuration
TEST_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=10

# Exchange API Keys (add your keys here)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
KRAKEN_API_KEY=your_kraken_api_key
KRAKEN_API_SECRET=your_kraken_api_secret
```

#### Laravel Configuration (laravel-backend/.env)
```env
APP_NAME="Kraken Trading Bot"
APP_ENV=local
APP_KEY=base64:your_app_key_here
APP_DEBUG=true
APP_URL=http://localhost:8000

# Flask API Integration
FLASK_API_URL=http://localhost:8080

# Database (SQLite for simplicity)
DB_CONNECTION=sqlite
DB_DATABASE=/absolute/path/to/database/database.sqlite
```

#### Vue.js Configuration (vue-frontend/.env)
```env
VUE_APP_API_BASE_URL=http://localhost:8000/api
VUE_APP_FLASK_API_URL=http://localhost:8080
VUE_APP_WS_URL=ws://localhost:8080
```

## 🔑 API Setup

### Exchange API Keys

#### Binance Setup
1. Visit [Binance API Management](https://www.binance.com/en/my/settings/api-management)
2. Create a new API key
3. Enable trading permissions
4. Add your IP address to whitelist
5. Copy keys to `.env` file

#### Kraken Setup
1. Visit [Kraken API Settings](https://www.kraken.com/u/security/api)
2. Generate new API key
3. Enable necessary permissions
4. Copy keys to `.env` file

#### Coinbase Setup
1. Visit [Coinbase API Settings](https://www.coinbase.com/settings/api)
2. Create Advanced Trade API key
3. Enable trading permissions
4. Copy keys to `.env` file

### Test Mode Configuration

For safe testing without real money:

```env
TEST_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=10
```

## 🚀 Running the Application

### Development Mode

#### Start Flask API
```bash
cd /path/to/project
python3 trading_bot.py
```

#### Start Laravel Backend
```bash
cd laravel-backend
php artisan serve
```

#### Start Vue.js Frontend
```bash
cd vue-frontend
npm run dev
```

### Production Mode

#### Using Docker (Recommended)
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Manual Production Setup
```bash
# Build Vue.js for production
cd vue-frontend
npm run build

# Start Laravel with production server
cd laravel-backend
php artisan config:cache
php artisan route:cache
php artisan serve --host=0.0.0.0 --port=8000
```

## 🎯 Features Overview

### 🤖 AI-Powered Analysis
- **Machine Learning Models**: Price prediction and pattern recognition
- **Sentiment Analysis**: Market sentiment from social media and news
- **Risk Assessment**: Dynamic risk evaluation
- **Auto-Trading**: Automated execution based on AI signals

### 📊 Technical Analysis
- **Multiple Indicators**: RSI, MACD, Bollinger Bands, Stochastic, Williams %R
- **Chart Patterns**: Support/resistance, trend lines, Fibonacci retracements
- **Statistical Analysis**: Mean, median, standard deviation, correlation
- **Backtesting**: Historical performance analysis

### 🌐 Multi-Exchange Support
- **Binance**: Spot and futures trading
- **Kraken**: Advanced trading features
- **Coinbase**: Institutional-grade API
- **KuCoin**: Wide variety of altcoins

### 📈 Altcoin Analysis
- **Correlation Analysis**: BTC vs altcoin relationships
- **Market Cap Tracking**: Top 100 cryptocurrencies
- **Volume Analysis**: Trading volume patterns
- **News Integration**: Cryptocurrency news sentiment

### 🎨 Modern Dashboard
- **Real-time Updates**: Live price feeds and signals
- **Interactive Charts**: Chart.js powered visualizations
- **Responsive Design**: Mobile-friendly interface
- **Dark/Light Themes**: Customizable appearance

## 🔧 Troubleshooting

### Common Issues

#### Flask API Not Starting
```bash
# Check Python version
python3 --version

# Install missing dependencies
pip install -r requirements.txt

# Check for port conflicts
lsof -i :8080
```

#### Laravel Errors
```bash
# Clear cache
php artisan config:clear
php artisan cache:clear
php artisan route:clear

# Check permissions
chmod -R 755 storage
chmod -R 755 bootstrap/cache

# Regenerate key
php artisan key:generate
```

#### Vue.js Build Issues
```bash
# Clear node modules
rm -rf node_modules
npm install

# Clear cache
npm run clean
npm run build
```

#### Docker Issues
```bash
# Check Docker status
docker ps -a

# View container logs
docker logs kraken-trading-bot

# Restart services
docker-compose restart

# Rebuild containers
docker-compose build --no-cache
```

### Performance Optimization

#### Database Optimization
```bash
# Laravel
php artisan db:monitor
php artisan cache:clear

# Enable OPcache
php -m | grep opcache
```

#### Frontend Optimization
```bash
# Build optimized bundle
npm run build -- --mode production

# Enable gzip compression
# Add to nginx configuration
gzip on;
gzip_types text/css application/javascript application/json;
```

## 🔒 Security Considerations

### API Key Security
- **Never commit API keys** to version control
- **Use environment variables** for sensitive data
- **Rotate keys regularly** (every 30-90 days)
- **Enable 2FA** on exchange accounts
- **Use read-only keys** when possible

### Network Security
- **Use HTTPS** in production
- **Implement rate limiting** on API endpoints
- **Enable CORS** properly for frontend
- **Use VPN** for sensitive operations

### Trading Security
- **Start with small amounts** when testing
- **Use stop-loss orders** to limit losses
- **Diversify** across multiple exchanges
- **Monitor positions** regularly
- **Have an exit strategy** for each trade

## 📚 API Documentation

### Flask API Endpoints

#### Health Check
```http
GET /health
```

#### Trading Data
```http
GET /status
```

#### Logs
```http
GET /logs
GET /logs/{level}
```

#### Trading Operations
```http
POST /test_trade
POST /run_cycle
```

### Laravel API Endpoints

#### Analysis
```http
GET /api/analysis/trading-data
GET /api/analysis/technical
POST /api/analysis/statistical
GET /api/analysis/performance
```

#### Health
```http
GET /api/health
```

## 🤝 Support

### Getting Help
1. **Check the logs** for error messages
2. **Review configuration** files for typos
3. **Test with small amounts** first
4. **Join our community** for support

### Community Resources
- **GitHub Issues**: Report bugs and request features
- **Documentation Wiki**: Detailed guides and tutorials
- **Discord Community**: Real-time support and discussions

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This software is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor. Past performance does not guarantee future results. Please trade responsibly and never invest more than you can afford to lose.**

---

## 🚀 What's Next?

After successful installation:

1. **Configure API Keys** for your preferred exchanges
2. **Test in Demo Mode** with small amounts
3. **Customize Strategies** based on your risk tolerance
4. **Monitor Performance** using the dashboard
5. **Scale Up** gradually as you gain confidence

Happy trading! 📈