#!/bin/bash

# Kraken Trading Bot - Start Production
# Simple script to start the main trading bot

set -e

# Load common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/scripts/common.sh" ]; then
    source "$SCRIPT_DIR/scripts/common.sh"
else
    echo "Error: common.sh not found"
    exit 1
fi

# Show usage
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage "./start_production.sh" "Start the Kraken trading bot in production mode"
    exit 0
fi

log_header "PRODUCTION" "🚀 Starting Kraken Production Trading Bot"

# 1. Clean up old processes
log_info "Cleaning up old processes..."
kill_process "python3 trading_bot.py"
kill_process "trading_bot"
kill_port 8080
log_success "Cleanup complete"

# 2. Check requirements
log_info "Checking requirements..."
if ! check_python_version; then
    log_error "Python 3.8+ required"
    exit 1
fi

if ! file_exists "trading_bot.py"; then
    log_error "trading_bot.py not found"
    exit 1
fi

if ! file_exists ".env"; then
    log_warning "Creating .env template..."
    cat > .env << 'EOF'
# Production Configuration
TEST_MODE=false
PRODUCTION_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=25
WEB_UI=true

# Add your API keys here
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
KRAKEN_API_KEY=your_key
KRAKEN_API_SECRET=your_secret
EOF
    log_warning "Edit .env with your API keys!"
fi

log_success "Requirements OK"

# 3. Install dependencies
log_info "Installing dependencies..."
if ! install_python_deps; then
    log_error "Failed to install dependencies"
    exit 1
fi
log_success "Dependencies installed"

# 4. Create logs directory
ensure_dir "logs"

# 5. Start monitoring in background
if file_exists "scripts/monitor_production.sh"; then
    log_info "Starting monitoring..."
    nohup ./scripts/monitor_production.sh > logs/monitoring.log 2>&1 &
    echo $! > monitor_pid.txt
    log_success "Monitoring started"
fi

# 6. Show info
echo ""
log_header "PRODUCTION" "🌐 Access Points:"
echo "  Dashboard: http://localhost:8080"
echo "  Health:    http://localhost:8080/health"
echo "  Logs:      http://localhost:8080/logs"
echo ""
log_success "✅ Production bot starting..."

# 7. Start the bot
export PRODUCTION_MODE=true
exec python3 trading_bot.py