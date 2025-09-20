#!/bin/bash

# Kraken Trading Bot - Start Production Script
# This script starts the main trading bot in production mode

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output with timestamps
print_status() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${PURPLE}[PRODUCTION]${NC} $1"
}

# Function to cleanup existing processes
cleanup_processes() {
    print_header "🧹 CLEANING UP EXISTING PROCESSES"

    # Kill any existing trading bot processes
    pkill -f "python3 trading_bot.py" 2>/dev/null || true
    pkill -f "trading_bot" 2>/dev/null || true

    # Kill processes on used ports
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true

    print_success "Process cleanup completed"
}

# Function to check system requirements
check_requirements() {
    print_header "🔍 CHECKING SYSTEM REQUIREMENTS"

    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        print_status "Please install Python 3.8 or higher"
        exit 1
    fi

    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [ "$(printf '%s\n' "$python_version" "3.8" | sort -V | head -n1)" != "3.8" ]; then
        print_error "Python 3.8 or higher is required. Current version: $python_version"
        exit 1
    fi

    print_success "Python $python_version found"

    # Check if trading_bot.py exists
    if [ ! -f "trading_bot.py" ]; then
        print_error "trading_bot.py not found in current directory"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << 'EOF'
# === PRODUCTION TRADING BOT CONFIGURATION ===
TEST_MODE=false
PRODUCTION_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=25
WEB_UI=true
VERBOSE_LOGGING=true
LOG_LEVEL=INFO

# === MAXIMUM PROFITABILITY SETTINGS ===
TAKE_PROFIT_PERCENT=5
STOP_LOSS_PERCENT=2
MAX_CONSECUTIVE_LOSSES=3
TRADING_CYCLE_MINUTES=1

# === EXCHANGE API KEYS ===
# Add your production API keys here
BINANCE_API_KEY=your_production_binance_key
BINANCE_API_SECRET=your_production_binance_secret
KRAKEN_API_KEY=your_production_kraken_key
KRAKEN_API_SECRET=your_production_kraken_secret
COINBASE_API_KEY_NAME=""
COINBASE_API_PRIVATE_KEY=""
KUCOIN_API_KEY=""
KUCOIN_API_SECRET=""
KUCOIN_API_PASSPHRASE=""
EOF
        print_warning "Please edit .env file with your production API keys!"
        print_warning "The bot will run in demo mode until real keys are added."
    fi

    # Check available disk space
    DISK_SPACE=$(df / | tail -1 | awk '{print $4}' 2>/dev/null || echo "1000000")
    if [ "$DISK_SPACE" -lt 1000000 ] 2>/dev/null; then
        DISK_MB=$((DISK_SPACE / 1024))
        print_warning "Low disk space detected: ${DISK_MB}MB available"
    fi

    print_success "System requirements check passed"
}

# Function to install/update Python dependencies
install_dependencies() {
    print_header "📦 INSTALLING PYTHON DEPENDENCIES"

    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found!"
        print_status "Please ensure requirements.txt exists with necessary dependencies"
        exit 1
    fi

    # Check if we're in an externally managed environment (macOS/Homebrew Python)
    if python3 -c "import sys; print('externally-managed' in str(sys.flags))" 2>/dev/null | grep -q "True" || python3 -m pip install --dry-run --quiet pip 2>&1 | grep -q "externally-managed-environment"; then
        print_warning "Detected externally managed Python environment (macOS/Homebrew)"
        print_status "Using --user flag for pip installs..."

        # Install/update pip with --user
        print_status "Updating pip..."
        python3 -m pip install --user --upgrade pip

        # Install requirements with --user
        print_status "Installing Python dependencies..."
        if ! pip3 install --user -r requirements.txt; then
            print_error "Failed to install Python dependencies"
            print_status "Try creating a virtual environment:"
            print_status "  python3 -m venv venv"
            print_status "  source venv/bin/activate"
            print_status "  pip install -r requirements.txt"
            exit 1
        fi
    else
        # Standard installation for other environments
        print_status "Updating pip..."
        python3 -m pip install --upgrade pip

        # Install requirements
        print_status "Installing Python dependencies..."
        if ! pip3 install -r requirements.txt; then
            print_error "Failed to install Python dependencies"
            exit 1
        fi
    fi

    print_success "Python dependencies installed successfully"
}

# Function to start production monitoring
start_monitoring() {
    print_header "📊 STARTING PRODUCTION MONITORING"

    # Start background monitoring
    if [ -f "monitor_production.sh" ]; then
        print_status "Starting production monitoring..."
        nohup ./monitor_production.sh > monitoring_production.log 2>&1 &
        MONITOR_PID=$!
        echo $MONITOR_PID > monitor_production_pid.txt
        print_success "Production monitoring started (PID: $MONITOR_PID)"
    else
        print_warning "monitor_production.sh not found - skipping monitoring"
    fi
}

# Function to start trading bot
start_trading_bot() {
    print_header "🚀 STARTING PRODUCTION TRADING BOT"

    # Create logs directory
    mkdir -p logs

    # Set environment variables
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    export PRODUCTION_MODE=true

    # Start the trading bot
    print_status "Starting trading bot..."
    print_status "Web UI will be available at: http://localhost:8080"
    print_status "Health check: http://localhost:8080/health"
    print_status "Portfolio: http://localhost:8080/portfolio"

    # Run the trading bot
    exec python3 trading_bot.py
}

# Function to display production information
display_info() {
    echo ""
    print_header "🚀 KRAKEN PRODUCTION TRADING BOT"
    echo "====================================="

    echo ""
    echo -e "${GREEN}🌐 WEB INTERFACE:${NC}"
    echo -e "  📊 Dashboard:  ${BLUE}http://localhost:8080${NC}"
    echo -e "  ❤️  Health:     ${BLUE}http://localhost:8080/health${NC}"
    echo -e "  📋 Portfolio:  ${BLUE}http://localhost:8080/portfolio${NC}"
    echo -e "  📈 Signals:    ${BLUE}http://localhost:8080/signals${NC}"
    echo -e "  📝 Logs:       ${BLUE}http://localhost:8080/logs${NC}"

    echo ""
    echo -e "${YELLOW}⚙️  PRODUCTION SETTINGS:${NC}"
    echo "  💰 Starting Balance:    \$1000"
    echo "  🎯 Take Profit:         5%"
    echo "  🛡️  Stop Loss:          2%"
    echo "  📊 Max Consecutive Losses: 3"
    echo "  ⚡ Trading Cycle:       1 minute"
    echo "  🌐 Web UI:              Enabled"

    echo ""
    echo -e "${BLUE}📊 LOG FILES:${NC}"
    echo "  📝 Trading Log: logs/trading_bot.log"
    echo "  📊 Monitor Log: monitoring_production.log"

    echo ""
    echo -e "${RED}🚨 EMERGENCY CONTROLS:${NC}"
    echo "  ./stop_production.sh                    # Graceful stop"
    echo "  pkill -f \"python3 trading_bot.py\"       # Force stop"
    echo "  pkill -f monitor_production             # Stop monitoring"

    echo ""
    print_success "✅ PRODUCTION TRADING BOT IS NOW RUNNING!"
    echo ""
    echo -e "${GREEN}💡 Production Features:${NC}"
    echo "  • Real-time trading with live data"
    echo "  • Advanced risk management"
    echo "  • Web-based monitoring dashboard"
    echo "  • Automatic profit taking"
    echo "  • Comprehensive logging"
    echo "  • Production health monitoring"
}

# Function to create stop script
create_stop_script() {
    cat > stop_production.sh << 'EOF'
#!/bin/bash
# Stop production trading bot script

echo "🛑 Stopping production trading bot..."

# Stop monitoring
if [ -f "monitor_production_pid.txt" ]; then
    MONITOR_PID=$(cat monitor_production_pid.txt)
    kill $MONITOR_PID 2>/dev/null || true
    rm -f monitor_production_pid.txt
    echo "📊 Monitoring stopped"
fi

# Kill trading bot processes
pkill -f "python3 trading_bot.py" 2>/dev/null || true
pkill -f "trading_bot" 2>/dev/null || true

# Kill processes on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

echo "✅ Production trading bot stopped"
EOF

    chmod +x stop_production.sh
    print_success "Stop script created: ./stop_production.sh"
}

# Main execution
main() {
    print_header "🚀 STARTING KRAKEN PRODUCTION TRADING BOT"

    # Make scripts executable
    chmod +x *.sh 2>/dev/null || true

    # Execute startup sequence
    cleanup_processes
    check_requirements
    install_dependencies
    start_monitoring
    create_stop_script
    display_info
    start_trading_bot
}

# Run main function
main "$@"