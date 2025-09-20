#!/bin/bash

# Kraken Trading Bot - Monitoring Script
# This script monitors the health and performance of the application

set -e

# Configuration
MONITOR_INTERVAL=60  # seconds
LOG_FILE="/app/logs/monitor.log"
ALERT_EMAIL=""  # Set this to receive email alerts
HEALTH_CHECK_URL="http://localhost:8080/health"

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

# Check Docker containers
check_containers() {
    log_info "Checking Docker containers..."

    local unhealthy_containers=0

    # Check if containers are running
    if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "kraken-trading-bot"; then
        send_alert "Trading Bot Container Down" "Trading bot container is not running"
        ((unhealthy_containers++))
    fi

    if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "laravel"; then
        send_alert "Laravel Container Down" "Laravel backend container is not running"
        ((unhealthy_containers++))
    fi

    if ! docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "vue"; then
        send_alert "Vue Container Down" "Vue frontend container is not running"
        ((unhealthy_containers++))
    fi

    if [ $unhealthy_containers -eq 0 ]; then
        log_success "All containers are running"
    fi
}

# Check application health
check_health() {
    log_info "Checking application health..."

    # Check Flask API health
    if curl -s --max-time 10 "$HEALTH_CHECK_URL" > /dev/null; then
        local health_response=$(curl -s "$HEALTH_CHECK_URL")
        local status=$(echo "$health_response" | jq -r '.status' 2>/dev/null || echo "unknown")

        if [ "$status" = "healthy" ]; then
            log_success "Flask API is healthy"
        elif [ "$status" = "warning" ]; then
            log_warning "Flask API has warnings"
        else
            send_alert "Flask API Unhealthy" "Health check returned status: $status"
        fi
    else
        send_alert "Flask API Unreachable" "Cannot connect to Flask API at $HEALTH_CHECK_URL"
    fi

    # Check Laravel API health
    if curl -s --max-time 10 "http://localhost:8000/api/health" > /dev/null; then
        log_success "Laravel API is reachable"
    else
        send_alert "Laravel API Unreachable" "Cannot connect to Laravel API"
    fi

    # Check Vue frontend
    if curl -s --max-time 10 "http://localhost:3000" > /dev/null; then
        log_success "Vue frontend is reachable"
    else
        send_alert "Vue Frontend Unreachable" "Cannot connect to Vue frontend"
    fi
}

# Check system resources
check_resources() {
    log_info "Checking system resources..."

    # Check disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "High Disk Usage" "Disk usage is at ${disk_usage}%"
    elif [ "$disk_usage" -gt 80 ]; then
        log_warning "Disk usage is at ${disk_usage}%"
    else
        log_info "Disk usage: ${disk_usage}%"
    fi

    # Check memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 90 ]; then
        send_alert "High Memory Usage" "Memory usage is at ${memory_usage}%"
    elif [ "$memory_usage" -gt 80 ]; then
        log_warning "Memory usage is at ${memory_usage}%"
    else
        log_info "Memory usage: ${memory_usage}%"
    fi

    # Check CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    if [ "${cpu_usage%.*}" -gt 90 ]; then
        send_alert "High CPU Usage" "CPU usage is at ${cpu_usage}%"
    elif [ "${cpu_usage%.*}" -gt 80 ]; then
        log_warning "CPU usage is at ${cpu_usage}%"
    else
        log_info "CPU usage: ${cpu_usage}%"
    fi
}

# Check log files
check_logs() {
    log_info "Checking log files..."

    local log_files=("/app/logs/trading_bot.log" "/app/laravel-backend/storage/logs/laravel.log")

    for log_file in "${log_files[@]}"; do
        if [ -f "$log_file" ]; then
            # Check for recent errors
            local error_count=$(tail -1000 "$log_file" 2>/dev/null | grep -i error | wc -l)
            if [ "$error_count" -gt 10 ]; then
                send_alert "High Error Count" "Found $error_count errors in $(basename "$log_file") in the last 1000 lines"
            elif [ "$error_count" -gt 0 ]; then
                log_warning "Found $error_count errors in $(basename "$log_file")"
            fi

            # Check log file size
            local log_size=$(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null || echo "0")
            local log_size_mb=$((log_size / 1024 / 1024))
            if [ "$log_size_mb" -gt 100 ]; then
                log_warning "Log file $(basename "$log_file") is ${log_size_mb}MB - consider rotation"
            fi
        else
            log_info "Log file not found: $log_file"
        fi
    done
}

# Check trading bot status
check_trading_bot() {
    log_info "Checking trading bot status..."

    # Check if bot is running trading cycles
    local recent_trades=$(curl -s "$HEALTH_CHECK_URL" | jq -r '.services.trading_bot.status' 2>/dev/null || echo "unknown")

    if [ "$recent_trades" = "unknown" ]; then
        log_warning "Cannot determine trading bot status"
    elif [ "$recent_trades" = "error" ]; then
        send_alert "Trading Bot Error" "Trading bot is in error state"
    else
        log_success "Trading bot status: $recent_trades"
    fi
}

# Generate monitoring report
generate_report() {
    log_info "Generating monitoring report..."

    local report_file="/app/logs/monitor_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Kraken Trading Bot - Monitoring Report
=======================================

Report Date: $(date)
Monitoring Period: $MONITOR_INTERVAL seconds

System Information:
------------------
Hostname: $(hostname)
OS: $(uname -s) $(uname -r)
Uptime: $(uptime)

Container Status:
----------------
$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")

Resource Usage:
--------------
Disk Usage: $(df -h / | tail -1 | awk '{print $5}')
Memory Usage: $(free -h | grep Mem | awk '{print $3 "/" $2}')
CPU Load: $(uptime | awk -F'load average:' '{print $2}')

Application Health:
------------------
Flask API: $(curl -s --max-time 5 "$HEALTH_CHECK_URL" > /dev/null && echo "Reachable" || echo "Unreachable")
Laravel API: $(curl -s --max-time 5 "http://localhost:8000/api/health" > /dev/null && echo "Reachable" || echo "Unreachable")
Vue Frontend: $(curl -s --max-time 5 "http://localhost:3000" > /dev/null && echo "Reachable" || echo "Unreachable")

Recent Alerts:
-------------
$(tail -20 "$LOG_FILE" | grep ALERT || echo "No recent alerts")

Report generated: $(date)
EOF

    log_success "Monitoring report generated: $report_file"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -o, --once          Run monitoring once and exit"
    echo "  -r, --report        Generate monitoring report"
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
        generate_report
        exit 0
    fi

    log_info "Starting Kraken Trading Bot monitoring..."
    log_info "Monitoring interval: $MONITOR_INTERVAL seconds"
    log_info "Log file: $LOG_FILE"

    while true; do
        log_info "=== Starting monitoring cycle ==="

        check_containers
        check_health
        check_resources
        check_logs
        check_trading_bot

        log_info "=== Monitoring cycle completed ==="

        if [ "$run_once" = true ]; then
            generate_report
            log_info "Monitoring completed (run once mode)"
            exit 0
        fi

        log_info "Waiting $MONITOR_INTERVAL seconds until next check..."
        sleep "$MONITOR_INTERVAL"
    done
}

# Error handling
trap 'log_error "Monitoring script failed with exit code $?"' ERR

# Run main function
main "$@"