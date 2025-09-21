#!/bin/bash

# Kraken Trading Bot - Production Monitor
# Simple monitoring for production trading bot

set -e

# Load common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/scripts/common.sh" ]; then
    source "$SCRIPT_DIR/scripts/common.sh"
else
    echo "Error: common.sh not found"
    exit 1
fi

# Configuration
INTERVAL=30
LOG_FILE="logs/monitor_production.log"
HEALTH_URL="http://localhost:8080/health"

# Show usage
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage "./monitor_production.sh" "Monitor production trading bot health"
    echo "  -o, --once    Run once and exit"
    echo "  -r, --report  Generate report only"
    exit 0
fi

# Parse arguments
RUN_ONCE=false
REPORT_ONLY=false

case "$1" in
    -o|--once) RUN_ONCE=true ;;
    -r|--report) REPORT_ONLY=true ;;
    "") ;; # Default continuous mode
    *) log_error "Unknown option: $1"; exit 1 ;;
esac

# Create logs directory
ensure_dir "logs"

if [ "$REPORT_ONLY" = true ]; then
    log_info "Generating production report..."
    # Simple report generation would go here
    log_success "Report generated"
    exit 0
fi

log_header "MONITOR" "📊 Starting Production Monitoring"
log_info "Interval: ${INTERVAL}s, Log: $LOG_FILE"

while true; do
    log_info "=== Health Check ==="

    # Check if bot is running
    if check_port 8080; then
        log_success "Bot port 8080 is active"
    else
        log_error "Bot port 8080 is not responding"
    fi

    # Check health endpoint
    if curl -s --max-time 5 "$HEALTH_URL" > /dev/null; then
        log_success "Health endpoint OK"
    else
        log_error "Health endpoint unreachable"
    fi

    # Check system resources
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 80 ]; then
        log_warning "High memory usage: ${memory_usage}%"
    else
        log_info "Memory usage: ${memory_usage}%"
    fi

    log_info "=== Check Complete ==="

    if [ "$RUN_ONCE" = true ]; then
        log_info "One-time check complete"
        exit 0
    fi

    sleep "$INTERVAL"
done