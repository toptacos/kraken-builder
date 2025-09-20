#!/bin/bash

# Kraken Trading Bot - Production Monitoring Script
# This script monitors the production trading bot health and performance

set -e

# Configuration
MONITOR_INTERVAL=30  # seconds (more frequent for production)
LOG_FILE="/app/logs/monitor_production.log"
ALERT_EMAIL=""  # Set this to receive email alerts
HEALTH_CHECK_URL="http://localhost:8080/health"
OVERALL_STATUS_URL="http://localhost:8080/status"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Send alert (email or other notification)
send_alert() {
    local subject="$1"
    local message="$2"

    log_error "ALERT: $subject - $message"

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Check trading bot container
check_trading_bot_container() {
    log_info "Checking trading bot container..."

    if ! docker ps --format "table {{.Names}}" | grep -q "kraken-trading-bot"; then
        send_alert "Trading Bot Container Down" "Production trading bot container is not running"
        return 1
    fi

    # Check container health
    container_status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "kraken-trading-bot" | awk '{print $2}')
    if [[ "$container_status" != *"Up"* ]]; then
        send_alert "Trading Bot Container Unhealthy" "Container status: $container_status"
        return 1
    fi

    log_success "Trading bot container is healthy"
    return 0
}

# Check Flask API health
check_api_health() {
    log_info "Checking Flask API health..."

    if ! curl -s --max-time 10 "$HEALTH_CHECK_URL" > /dev/null; then
        send_alert "Flask API Unreachable" "Cannot connect to Flask API at $HEALTH_CHECK_URL"
        return 1
    fi

    # Get detailed health status
    health_response=$(curl -s "$HEALTH_CHECK_URL")
    status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")

    case "$status" in
        "healthy")
            log_success "Flask API is healthy"
            ;;
        "warning")
            log_warning "Flask API has warnings"
            ;;
        "error")
            send_alert "Flask API Error" "Health check returned error status"
            return 1
            ;;
        *)
            log_warning "Flask API status unknown: $status"
            ;;
    esac

    return 0
}

# Check trading bot status
check_trading_status() {
    log_info "Checking trading bot operational status..."

    if ! curl -s --max-time 10 "$OVERALL_STATUS_URL" > /dev/null; then
        log_warning "Cannot connect to status endpoint"
        return 1
    fi

    # Get trading status
    status_response=$(curl -s "$OVERALL_STATUS_URL")
    test_mode=$(echo "$status_response" | jq -r '.test_mode' 2>/dev/null || echo "unknown")
    current_balance=$(echo "$status_response" | jq -r '.current_balance' 2>/dev/null || echo "unknown")

    if [ "$test_mode" = "true" ]; then
        send_alert "Production Bot in Test Mode" "Trading bot is running in test mode instead of production"
        return 1
    fi

    if [ "$current_balance" != "unknown" ]; then
        log_info "Current balance: $$current_balance"
    fi

    log_success "Trading bot status OK"
    return 0
}

# Check system resources for production
check_production_resources() {
    log_info "Checking production system resources..."

    # Check memory usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 85 ]; then
        send_alert "High Memory Usage" "Memory usage is at ${memory_usage}% - production impact possible"
    elif [ "$memory_usage" -gt 75 ]; then
        log_warning "Memory usage is at ${memory_usage}%"
    fi

    # Check disk space
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "Critical Disk Usage" "Disk usage is at ${disk_usage}% - immediate action required"
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Disk usage is at ${disk_usage}%"
    fi

    # Check CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    if [ "${cpu_usage%.*}" -gt 90 ]; then
        send_alert "High CPU Usage" "CPU usage is at ${cpu_usage}% - production performance affected"
    elif [ "${cpu_usage%.*}" -gt 75 ]; then
        log_warning "CPU usage is at ${cpu_usage}%"
    fi

    log_success "System resources OK"
}

# Check recent trading activity
check_trading_activity() {
    log_info "Checking recent trading activity..."

    # Check log file for recent activity
    if [ -f "/app/logs/trading_bot.log" ]; then
        # Count recent trades (last 30 minutes)
        recent_trades=$(tail -n 1000 "/app/logs/trading_bot.log" | grep -c "TRADE" || echo "0")
        if [ "$recent_trades" -eq 0 ]; then
            log_warning "No recent trading activity detected"
        else
            log_info "Recent trading activity: $recent_trades trades"
        fi

        # Check for recent errors
        recent_errors=$(tail -n 500 "/app/logs/trading_bot.log" | grep -i error | wc -l)
        if [ "$recent_errors" -gt 5 ]; then
            send_alert "High Error Rate" "Found $recent_errors errors in recent logs"
        elif [ "$recent_errors" -gt 0 ]; then
            log_warning "Found $recent_errors errors in recent logs"
        fi
    else
        log_warning "Trading log file not found"
    fi
}

# Generate production report
generate_production_report() {
    log_info "Generating production monitoring report..."

    local report_file="/app/logs/production_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Kraken Trading Bot - Production Monitoring Report
===============================================

Report Date: $(date)
Monitoring Period: $MONITOR_INTERVAL seconds

Container Status:
----------------
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(kraken|trading)" || echo "No trading containers found")

API Health:
----------
Flask Health: $(curl -s --max-time 5 "$HEALTH_CHECK_URL" > /dev/null && echo "Reachable" || echo "Unreachable")

System Resources:
----------------
Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')
Disk Usage: $(df -h / | tail -1 | awk '{print $5}')
CPU Load: $(uptime | awk -F'load average:' '{print $2}')

Recent Activity:
---------------
Trading Log: $([ -f "/app/logs/trading_bot.log" ] && echo "Present" || echo "Missing")
Recent Trades: $([ -f "/app/logs/trading_bot.log" ] && tail -n 1000 "/app/logs/trading_bot.log" | grep -c "TRADE" || echo "0")
Recent Errors: $([ -f "/app/logs/trading_bot.log" ] && tail -n 500 "/app/logs/trading_bot.log" | grep -i -c error || echo "0")

Report generated: $(date)
EOF

    log_success "Production report generated: $report_file"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -o, --once          Run monitoring once and exit"
    echo "  -r, --report        Generate production report"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --once           # Run once"
    echo "  $0 --report         # Generate report"
    echo "  $0                  # Run continuously"
}

# Main monitoring function
main() {
    local run_once=false
    local generate_report_only=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -o|--once)
                run_once=true
                shift
                ;;
            -r|--report)
                generate_report_only=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"

    if [ "$generate_report_only" = true ]; then
        generate_production_report
        exit 0
    fi

    log_info "Starting Kraken Trading Bot production monitoring..."
    log_info "Monitoring interval: $MONITOR_INTERVAL seconds"
    log_info "Log file: $LOG_FILE"

    while true; do
        log_info "=== Starting production monitoring cycle ==="

        # Critical production checks
        check_trading_bot_container
        check_api_health
        check_trading_status
        check_production_resources
        check_trading_activity

        log_info "=== Production monitoring cycle completed ==="

        if [ "$run_once" = true ]; then
            generate_production_report
            log_info "Production monitoring completed (run once mode)"
            exit 0
        fi

        log_info "Waiting $MONITOR_INTERVAL seconds until next check..."
        sleep "$MONITOR_INTERVAL"
    done
}

# Error handling
trap 'log_error "Production monitoring script failed with exit code $?"' ERR

# Run main function
main "$@"