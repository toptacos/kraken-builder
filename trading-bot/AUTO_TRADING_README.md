# 🤖 Automated Trading System

## Overview

The Kraken Trading Bot now includes a comprehensive automated trading system that can execute trades every minute when enabled. The system integrates with the existing scraping and analysis functionality to provide continuous, intelligent trading.

## 🚀 Quick Start

### 1. Enable Production Mode
```bash
# Set environment variables
export TEST_MODE=false
export TRADING_MODE=production
```

### 2. Enable Auto-Trading
```bash
# Set auto-trading environment variables
export AUTO_TRADING_ENABLED=true
export AUTO_TRADING_INTERVAL=60  # seconds between trades
```

### 3. Start the System
```bash
# Run the clean deployment script
./clean_test_and_deploy.sh
```

### 4. Access Dashboard
- Open http://localhost:8080
- Switch to **PRODUCTION MODE** using the toggle
- Enable **AUTO TRADING** using the second toggle

## 🎛️ Dashboard Controls

### Mode Switching
- **TEST MODE**: Safe simulation mode (default)
- **PRODUCTION MODE**: Real trading with actual funds ⚠️

### Auto-Trading Toggle
- Only available in PRODUCTION MODE
- Enables automatic trading every minute
- Includes safety checks and monitoring

## 🔧 Technical Components

### Files Added
- `auto_trader.py` - Main automated trading script
- `setup_cron.sh` - Cron job setup script
- Updated `trading_bot.py` - Backend API endpoints
- Updated `advanced-dashboard.html` - Frontend controls

### API Endpoints
- `GET/POST /mode` - Get/set trading mode
- `GET/POST /auto-trading` - Get/set auto-trading settings
- `POST /auto-trade` - Trigger automated trading cycle

### Environment Variables
```bash
# Mode Settings
TEST_MODE=false              # Enable production mode
TRADING_MODE=production      # Explicit mode setting

# Auto-Trading Settings
AUTO_TRADING_ENABLED=true    # Enable auto-trading
AUTO_TRADING_INTERVAL=60     # Seconds between cycles
AUTO_TRADER_MODE=continuous  # continuous/single
```

## 🛡️ Safety Features

### Production Mode Requirements
- Auto-trading only works in production mode
- Requires explicit mode confirmation
- Includes health checks before each trade

### Risk Management
- Respects existing stop-loss and take-profit settings
- Double-checks all trades before execution
- Monitors consecutive losses and trading limits

### Monitoring
- Comprehensive logging for all automated actions
- Real-time dashboard updates
- Health checks every cycle

## 📊 Trading Logic

### Every Minute Cycle:
1. **Health Check** - Verify system is operational
2. **Mode Verification** - Confirm production mode and auto-trading enabled
3. **Data Scraping** - Fetch trending coins from CoinGecko
4. **Analysis** - Run technical indicators (SMA, RSI, MACD, Bollinger Bands)
5. **Signal Generation** - Determine buy/sell/hold based on analysis
6. **Risk Assessment** - Check position sizes, losses, and limits
7. **Trade Execution** - Execute trade if signal is valid
8. **Logging** - Record all actions and results

### Technical Indicators Used:
- Simple Moving Averages (10, 25, 50 periods)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Volume analysis
- Trend strength calculations

## 🔄 Cron Job Setup

The system automatically sets up a cron job during deployment:

```bash
# Cron job runs every minute
* * * * * cd /app && python3 auto_trader.py >> logs/auto_trader.log 2>&1
```

### Manual Cron Setup:
```bash
# Make script executable
chmod +x setup_cron.sh

# Setup cron job
./setup_cron.sh

# Check cron jobs
crontab -l

# Remove cron jobs
crontab -r
```

## 📈 Monitoring & Logs

### Log Files
- `logs/trading_bot.log` - Main application logs
- `logs/auto_trader.log` - Automated trading logs

### Dashboard Monitoring
- Real-time trade status
- Profit/loss tracking
- System health indicators
- Recent trading activity

### Health Checks
- API endpoint: `GET /health`
- System resource monitoring
- Exchange connectivity checks

## ⚠️ Important Warnings

### Production Trading Risks
- **Real Money**: Auto-trading executes real trades with actual funds
- **No Guarantees**: Past performance doesn't predict future results
- **Market Volatility**: Cryptocurrency markets can be highly volatile
- **Technical Risks**: Software bugs or connectivity issues can cause losses

### Safety Recommendations
1. Start with small amounts
2. Monitor closely during initial operation
3. Set appropriate stop-loss limits
4. Keep emergency funds separate
5. Regular backup of configuration and logs

### Emergency Stop
- Switch back to TEST MODE in dashboard
- Disable AUTO TRADING toggle
- Use emergency stop button if needed
- Check logs for any issues

## 🔧 Troubleshooting

### Auto-Trading Not Starting
```bash
# Check environment variables
echo $AUTO_TRADING_ENABLED
echo $TRADING_MODE

# Check cron jobs
crontab -l

# Check logs
tail -f logs/auto_trader.log
```

### Health Check Failures
```bash
# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8080/mode

# Check system resources
docker stats kraken-trading-bot-production
```

### Trade Execution Issues
```bash
# Check exchange connectivity
curl http://localhost:8080/exchange-portfolios

# Review recent logs
tail -50 logs/trading_bot.log
```

## 📚 Advanced Configuration

### Custom Intervals
```bash
# Different trading frequencies
export AUTO_TRADING_INTERVAL=30   # Every 30 seconds
export AUTO_TRADING_INTERVAL=300  # Every 5 minutes
```

### Single Cycle Mode
```bash
# Run one cycle then stop
export AUTO_TRADER_MODE=single
python3 auto_trader.py
```

### Custom Risk Parameters
```bash
# Adjust in trading_bot.py or environment
export TAKE_PROFIT_PERCENT=2.0
export STOP_LOSS_PERCENT=0.5
export MAX_DAILY_LOSS_PERCENT=2.0
```

## 🎯 Best Practices

1. **Start Small**: Begin with minimal trade amounts
2. **Monitor Closely**: Watch the first few days of operation
3. **Regular Reviews**: Check performance weekly
4. **Backup Data**: Save logs and configuration regularly
5. **Stay Informed**: Keep up with market conditions
6. **Emergency Plan**: Know how to stop trading quickly

## 📞 Support

For issues or questions:
1. Check the logs in `logs/auto_trader.log`
2. Review dashboard error messages
3. Test in manual mode first
4. Ensure all environment variables are set correctly

Remember: This system is for educational and research purposes. Always trade responsibly and never risk more than you can afford to lose.