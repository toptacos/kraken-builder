#!/bin/bash

# Kraken Trading Bot - Start Overnight Trading
# Simple script to start overnight trading session

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
    show_usage "./start_overnight_trading.sh" "Start overnight trading session"
    exit 0
fi

log_header "OVERNIGHT" "🌙 Starting Overnight Trading Session"

# 1. Clean up old processes
log_info "Cleaning up old processes..."
kill_process "python3 overnight_trader.py"
kill_process "overnight_trader"
kill_port 8081
log_success "Cleanup complete"

# 2. Check requirements
log_info "Checking requirements..."
if ! check_python_version; then
    log_error "Python 3.8+ required"
    exit 1
fi

if ! file_exists "overnight_trader.py"; then
    log_error "overnight_trader.py not found"
    exit 1
fi

if ! file_exists ".env"; then
    log_warning "Creating .env template..."
    cat > .env << 'EOF'
# Overnight Trading Configuration
TEST_MODE=false
PRODUCTION_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=25
DAILY_PROFIT_TARGET=50
DAILY_LOSS_LIMIT=-100
MAX_TRADES_PER_HOUR=12

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

# 5. Show info
echo ""
log_header "OVERNIGHT" "🌐 Access Points:"
echo "  Status:  http://localhost:8081/overnight/status"
echo "  Stop:    http://localhost:8081/overnight/stop"
echo ""
log_success "✅ Overnight trading starting..."

# 6. Start the overnight trader
exec python3 overnight_trader.py