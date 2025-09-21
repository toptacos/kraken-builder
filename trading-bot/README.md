# Kraken Trading Bot

A simple and powerful cryptocurrency trading bot with automated strategies.

## 🚀 Quick Start

### Option 1: Automated Build and Deploy (Recommended)

```bash
# 1. Configure API Keys
# Edit .env file with your exchange API keys
nano .env

# 2. Build and test the application
./build_and_deploy.sh --build

# 3. Deploy to production
./build_and_deploy.sh --deploy

# 4. Check status
./build_and_deploy.sh --status
```

### Option 2: Manual Setup

#### 1. Setup Environment
```bash
# Option 1: Use virtual environment (recommended)
./setup_venv.sh
source venv/bin/activate

# Option 2: Use system Python (may need --user flag)
# Just run scripts directly
```

#### 2. Configure API Keys
Edit `.env` file with your exchange API keys:
```bash
# Add your keys here
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
KRAKEN_API_KEY=your_key
KRAKEN_API_SECRET=your_secret
```

#### 3. Start Trading
```bash
# Start main production bot
./start_production.sh

# Or start overnight trading
./start_overnight_trading.sh
```

## 📊 Available Scripts

### Build and Deployment
| Script | Purpose | Usage |
|--------|---------|-------|
| `./build_and_deploy.sh` | Complete build and deployment pipeline | `./build_and_deploy.sh --build/--deploy/--restart/--status` |
| `./test_basic_functionality.py` | Run basic functionality tests | `python3 test_basic_functionality.py` |

### Trading Scripts
| Script | Purpose | Usage |
|--------|---------|-------|
| `./start_production.sh` | Start main trading bot | `./start_production.sh` |
| `./start_overnight_trading.sh` | Start overnight trading | `./start_overnight_trading.sh` |
| `./monitor_production.sh` | Monitor bot health | `./monitor_production.sh [--once\|--report]` |
| `./monitor_system.sh` | Monitor system resources | `./monitor_system.sh [--once\|--report]` |
| `./setup_venv.sh` | Create virtual environment | `./setup_venv.sh` |

## 🏗️ Project Structure

```
kraken-trading-bot/
├── scripts/
│   └── common.sh          # Shared utilities
├── trading_bot.py         # Main trading bot
├── overnight_trader.py    # Overnight trading
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── .env                  # Environment variables
└── README.md            # This file
```

## 🔧 Features

- **Multi-Exchange Support**: Binance, Kraken, Coinbase, KuCoin
- **Automated Strategies**: Trend following, arbitrage, risk management
- **Web Dashboard**: Monitor trades at http://localhost:8080
- **Production Ready**: Health monitoring, error handling, logging
- **Docker Support**: Easy deployment with Docker

## 📈 Trading Modes

### Production Mode
- Real money trading
- Risk management
- Continuous monitoring
- Web dashboard

### Overnight Mode
- Automated overnight trading
- Daily profit/loss limits
- Morning auto-stop

## 🛠️ Development

### Prerequisites
- Python 3.8+
- pip
- curl (for health checks)

### Installation
```bash
# Clone repository
git clone <repository-url>
cd kraken-trading-bot

# Setup environment
./setup_venv.sh
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t kraken-trading-bot .
docker run -p 8080:8080 kraken-trading-bot
```

### Automated Build and Deploy
The `build_and_deploy.sh` script provides a complete CI/CD pipeline with support for both Python and PHP implementations:

```bash
# Python Implementation (default)
./build_and_deploy.sh --python --build
./build_and_deploy.sh --python --deploy

# PHP Implementation (FrankenPHP)
./build_and_deploy.sh --php --build
./build_and_deploy.sh --php --deploy

# Service Management
./build_and_deploy.sh --restart    # Restart all services
./build_and_deploy.sh --status     # Check service status
./build_and_deploy.sh --rollback   # Rollback to previous deployment
./build_and_deploy.sh --stop       # Stop all services
```

#### Build Process Features:
- ✅ **Multi-language support** - Python and PHP implementations
- ✅ **Dependency checking** - Verifies all required tools are installed
- ✅ **Automated testing** - Runs test suite with coverage reporting
- ✅ **Docker image building** - Builds optimized Docker images
- ✅ **Backup creation** - Creates backups before major changes
- ✅ **Cleanup** - Removes old Docker images and temporary files

#### Deployment Features:
- ✅ **Health checks** - Verifies services are running correctly
- ✅ **Rollback capability** - Automatic rollback on deployment failure
- ✅ **Service monitoring** - Continuous health monitoring
- ✅ **Environment-specific configs** - Supports different environments
- ✅ **Profit/loss thresholds** - Automatic trading halt when limits reached

#### PHP Implementation (FrankenPHP):
```bash
# Start PHP trading bot directly
php bin/console start

# Check PHP bot status
php bin/console status

# Run PHP bot tests
php bin/console test

# Stop PHP trading bot
php bin/console stop
```

## 📊 Monitoring

### Health Endpoints
- `http://localhost:8080/health` - Bot health status
- `http://localhost:8080/status` - Trading status
- `http://localhost:8080/portfolio` - Portfolio overview

### Monitoring Scripts
```bash
# Monitor bot health
./monitor_production.sh

# Monitor system resources
./monitor_system.sh

# Generate reports
./monitor_production.sh --report
./monitor_system.sh --report
```

## ⚠️ Important Notes

- **Real Money Trading**: This bot trades with real money. Use at your own risk.
- **API Keys**: Never commit API keys to version control.
- **Risk Management**: Always set appropriate stop-loss limits.
- **Testing**: Test with small amounts first.

## 🆘 Troubleshooting

### Common Issues

**"pip install" fails**
```bash
# Try with user flag
pip install --user -r requirements.txt

# Or use virtual environment
./setup_venv.sh
source venv/bin/activate
pip install -r requirements.txt
```

**Bot won't start**
```bash
# Check Python version
python3 --version

# Check if .env file exists
ls -la .env

# Check API keys in .env
cat .env
```

**Port already in use**
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9

# Or use different port
# Edit scripts to use different port
```

## 📝 License

This project is for educational purposes. Use at your own risk.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Check the monitoring scripts output
4. Open an issue with detailed information