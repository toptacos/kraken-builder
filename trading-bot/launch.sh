#!/bin/bash

# Kraken Trading Bot - One-Command Launcher
# Launches the complete FrankenPHP-powered trading platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Configuration
APP_NAME="Kraken Trading Bot"
FRANKENPHP_PORT=80
DASHBOARD_URL="http://localhost"

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}[$APP_NAME]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running!"
        log_info "Please start Docker Desktop and try again"
        exit 1
    fi
}

# Check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $port is already in use"
        return 1
    fi
    return 0
}

# Stop existing containers
cleanup_containers() {
    log_info "Cleaning up existing containers..."

    # Stop and remove existing containers
    docker-compose down --remove-orphans 2>/dev/null || true

    # Remove specific containers if they exist
    docker rm -f kraken-frankenphp kraken-trading-bot kraken-mysql 2>/dev/null || true

    log_success "Cleanup complete"
}

# Start FrankenPHP with Docker
start_frankenphp() {
    log_header "🚀 Starting FrankenPHP Server"

    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.frankenphp.yml" ]; then
        log_error "docker-compose.frankenphp.yml not found!"
        exit 1
    fi

    # Start services
    log_info "Building and starting FrankenPHP services..."
    docker-compose -f docker-compose.frankenphp.yml up -d --build

    if [ $? -eq 0 ]; then
        log_success "FrankenPHP services started successfully"
    else
        log_error "Failed to start FrankenPHP services"
        exit 1
    fi
}

# Start Python trading bot
start_trading_bot() {
    log_header "🤖 Starting Python Trading Bot"

    # Check if trading bot exists
    if [ ! -f "trading_bot.py" ]; then
        log_warning "trading_bot.py not found - skipping Python bot startup"
        return
    fi

    # Start trading bot in background
    log_info "Starting Python trading bot..."
    python3 trading_bot.py > logs/trading_bot.log 2>&1 &
    echo $! > trading_bot.pid

    log_success "Trading bot started (PID: $(cat trading_bot.pid))"
}

# Wait for services to be ready
wait_for_services() {
    log_header "⏳ Waiting for services to be ready"

    local max_attempts=30
    local attempt=1

    log_info "Checking FrankenPHP health..."

    while [ $attempt -le $max_attempts ]; do
        if curl -s "$DASHBOARD_URL/health" >/dev/null 2>&1; then
            log_success "FrankenPHP is ready!"
            return 0
        fi

        log_info "Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        attempt=$((attempt + 1))
    done

    log_error "FrankenPHP failed to start within timeout"
    return 1
}

# Open dashboard in browser
open_dashboard() {
    log_header "🌐 Opening Trading Dashboard"

    # Wait a bit more for everything to initialize
    sleep 3

    # Open browser based on OS
    case "$(uname -s)" in
        Darwin)
            # macOS
            open "$DASHBOARD_URL" 2>/dev/null || true
            ;;
        Linux)
            # Linux
            xdg-open "$DASHBOARD_URL" 2>/dev/null || true
            ;;
        *)
            log_info "Please open: $DASHBOARD_URL"
            ;;
    esac

    log_success "Dashboard opened in browser"
}

# Display system information
display_info() {
    echo ""
    log_header "🎯 $APP_NAME - FULLY OPERATIONAL"
    echo "=================================================="

    echo ""
    echo -e "${GREEN}🌐 WEB DASHBOARD:${NC}"
    echo -e "  📊 Main Dashboard:     ${BLUE}$DASHBOARD_URL${NC}"
    echo -e "  ❤️  Health Check:       ${BLUE}$DASHBOARD_URL/health${NC}"
    echo -e "  📋 API Endpoints:       ${BLUE}$DASHBOARD_URL/api/${NC}"

    echo ""
    echo -e "${YELLOW}⚙️  ACTIVE SERVICES:${NC}"
    echo "  🚀 FrankenPHP Server:  Running on port $FRANKENPHP_PORT"
    echo "  🤖 Python Trading Bot: $(pgrep -f 'python3 trading_bot.py' >/dev/null && echo 'Running' || echo 'Not Started')"
    echo "  📊 Real-time Updates:  WebSocket enabled"

    echo ""
    echo -e "${BLUE}📊 MONITORING:${NC}"
    echo "  📝 Application Logs:   logs/"
    echo "  🐳 Docker Containers:   docker-compose -f docker-compose.frankenphp.yml ps"
    echo "  📊 System Resources:   ./monitor_system.sh"

    echo ""
    echo -e "${RED}🚨 EMERGENCY CONTROLS:${NC}"
    echo "  🛑 Stop Everything:     ./stop_all.sh"
    echo "  🔄 Restart Services:    ./launch.sh"
    echo "  📊 View Logs:           tail -f logs/trading_bot.log"

    echo ""
    log_success "✅ $APP_NAME IS NOW RUNNING!"
    echo ""
    echo -e "${GREEN}💡 Features:${NC}"
    echo "  • Dynamic trading dashboard with real-time charts"
    echo "  • X/Twitter scraping for market insights"
    echo "  • FrankenPHP-powered ultra-fast PHP backend"
    echo "  • WebSocket real-time updates"
    echo "  • Comprehensive API endpoints"
    echo "  • Automated trading bot integration"
}

# Create logs directory
ensure_logs_dir() {
    mkdir -p logs
}

# Main execution
main() {
    log_header "🚀 LAUNCHING $APP_NAME"

    # Pre-flight checks
    check_docker
    check_port $FRANKENPHP_PORT
    ensure_logs_dir

    # Start sequence
    cleanup_containers
    start_frankenphp
    start_trading_bot
    wait_for_services
    open_dashboard
    display_info

    log_success "🎯 Launch sequence complete!"
    log_info "Press Ctrl+C to stop all services"
}

# Cleanup function
cleanup() {
    log_header "🧹 Cleaning up..."

    # Stop trading bot
    if [ -f "trading_bot.pid" ]; then
        kill $(cat trading_bot.pid) 2>/dev/null || true
        rm -f trading_bot.pid
        log_info "Trading bot stopped"
    fi

    # Stop Docker services
    docker-compose -f docker-compose.frankenphp.yml down 2>/dev/null || true
    log_info "FrankenPHP services stopped"

    log_success "Cleanup complete"
    exit 0
}

# Trap SIGINT (Ctrl+C) for cleanup
trap cleanup SIGINT

# Run main function
main "$@"