#!/bin/bash

# Kraken Trading Bot - Stop All Services
# Gracefully stops all FrankenPHP and trading services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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
    echo -e "${PURPLE}[STOP]${NC} $1"
}

# Stop Python trading bot
stop_trading_bot() {
    log_info "Stopping Python trading bot..."

    if [ -f "trading_bot.pid" ]; then
        local pid=$(cat trading_bot.pid)
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            log_success "Trading bot stopped (PID: $pid)"
        else
            log_warning "Trading bot process not found"
        fi
        rm -f trading_bot.pid
    else
        # Try to find and kill any trading bot processes
        pkill -f "python3 trading_bot.py" 2>/dev/null || true
        pkill -f "python3 overnight_trader.py" 2>/dev/null || true
        log_info "Killed any remaining trading bot processes"
    fi
}

# Stop FrankenPHP services
stop_frankenphp() {
    log_info "Stopping FrankenPHP services..."

    if [ -f "docker-compose.frankenphp.yml" ]; then
        docker-compose -f docker-compose.frankenphp.yml down --remove-orphans
        log_success "FrankenPHP services stopped"
    else
        log_warning "docker-compose.frankenphp.yml not found"
    fi
}

# Stop any remaining containers
stop_containers() {
    log_info "Cleaning up remaining containers..."

    # Stop specific containers
    docker stop kraken-frankenphp kraken-mysql kraken-redis 2>/dev/null || true
    docker rm kraken-frankenphp kraken-mysql kraken-redis 2>/dev/null || true

    log_success "Container cleanup complete"
}

# Kill any processes on our ports
kill_ports() {
    log_info "Freeing up ports..."

    # Kill processes on common ports
    for port in 80 443 3306 6379 8080 8081; do
        lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
    done

    log_success "Ports freed"
}

# Main execution
main() {
    log_header "🛑 Stopping Kraken Trading Bot"

    stop_trading_bot
    stop_frankenphp
    stop_containers
    kill_ports

    echo ""
    log_success "✅ All services stopped successfully!"
    echo ""
    echo -e "${GREEN}To restart:${NC} ./launch.sh"
    echo -e "${GREEN}To check status:${NC} docker-compose -f docker-compose.frankenphp.yml ps"
}

# Run main function
main "$@"