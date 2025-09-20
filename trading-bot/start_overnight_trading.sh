#!/bin/bash

# Kraken Trading Bot - Start Overnight Trading Script
# This script starts the overnight trading session with monitoring

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
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${PURPLE}[OVERNIGHT]${NC} $1"
}

# Function to cleanup existing processes
cleanup_processes() {
    print_header "🧹 CLEANING UP EXISTING PROCESSES"

    # Kill any existing overnight trader processes
    pkill -f "python3 overnight_trader.py" 2>/dev/null || true
    pkill -f "overnight_trader" 2>/dev/null || true

    # Kill processes on used ports
    lsof -ti:8081 | xargs kill -9 2>/dev/null || true

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

    # Check if overnight_trader.py exists
    if [ ! -f "overnight_trader.py" ]; then
        print_error "overnight_trader.py not found in current directory"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << 'EOF'
# === OVERNIGHT TRADING CONFIGURATION ===
TEST_MODE=false
PRODUCTION_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=25
VERBOSE_LOGGING=true
LOG_LEVEL=INFO

# === OVERNIGHT TRADING PARAMETERS ===
DAILY_PROFIT_TARGET=50
DAILY_LOSS_LIMIT=-100
MAX_TRADES_PER_HOUR=12
MIN_ARB_PROFIT_PCT=0.5
MAX_ARB_POSITIONS=5

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

# Function to start overnight trader
start_overnight_trader() {
    print_header "🌙 STARTING OVERNIGHT TRADING SESSION"

    # Create logs directory
    mkdir -p logs

    # Set environment variables for overnight trading
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"

    # Start the overnight trader
    print_status "Starting overnight trader..."
    print_status "Monitoring server will be available at: http://localhost:8081"
    print_status "Status endpoint: http://localhost:8081/overnight/status"
    print_status "Stop endpoint: http://localhost:8081/overnight/stop"

    # Run the overnight trader
    exec python3 overnight_trader.py
}

# Function to display overnight trading information
display_info() {
    echo ""
    print_header "🌙 KRAKEN OVERNIGHT TRADING BOT"
    echo "======================================"

    echo ""
    echo -e "${GREEN}🌐 MONITORING ENDPOINTS:${NC}"
    echo -e "  📊 Status:     ${BLUE}http://localhost:8081/overnight/status${NC}"
    echo -e "  🛑 Emergency Stop: ${RED}http://localhost:8081/overnight/stop${NC}"

    echo ""
    echo -e "${YELLOW}⚙️  OVERNIGHT SETTINGS:${NC}"
    echo "  💰 Starting Balance:    \$1000"
    echo "  🎯 Daily Profit Target: \$50"
    echo "  🛡️  Daily Loss Limit:   -\$100"
    echo "  ⚡ Max Trades/Hour:     12"
    echo "  📊 Min Profit Margin:   0.5%"
    echo "  🌙 Trading Hours:       24/7 (stops 6-8 AM)"

    echo ""
    echo -e "${BLUE}📊 LOG FILES:${NC}"
    echo "  📝 Main Log:    logs/overnight_trader.log"
    echo "  📈 Trend Cache: trend_cache/"

    echo ""
    echo -e "${RED}🚨 EMERGENCY CONTROLS:${NC}"
    echo "  curl http://localhost:8081/overnight/stop    # Emergency stop"
    echo "  pkill -f overnight_trader                   # Force stop"
    echo "  pkill -f \"python3 overnight_trader.py\"      # Alternative stop"

    echo ""
    print_success "✅ OVERNIGHT TRADING BOT IS NOW RUNNING!"
    echo ""
    echo -e "${GREEN}💡 Features:${NC}"
    echo "  • Multi-exchange arbitrage trading"
    echo "  • Advanced trend analysis"
    echo "  • Real-time profit/loss tracking"
    echo "  • Automatic risk management"
    echo "  • Daily limits with auto-stop"
    echo "  • Comprehensive logging"
}

# Function to create stop script
create_stop_script() {
    cat > stop_overnight_trading.sh << 'EOF'
#!/bin/bash
# Stop overnight trading script

echo "🛑 Stopping overnight trading..."

# Kill overnight trader processes
pkill -f "python3 overnight_trader.py" 2>/dev/null || true
pkill -f "overnight_trader" 2>/dev/null || true

# Kill processes on port 8081
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

echo "✅ Overnight trading stopped"
EOF

    chmod +x stop_overnight_trading.sh
    print_success "Stop script created: ./stop_overnight_trading.sh"
}

# Main execution
main() {
    print_header "🚀 STARTING KRAKEN OVERNIGHT TRADING BOT"

    # Make scripts executable
    chmod +x *.sh 2>/dev/null || true

    # Execute startup sequence
    cleanup_processes
    check_requirements
    install_dependencies
    create_stop_script
    display_info
    start_overnight_trader
}

# Run main function
main "$@"