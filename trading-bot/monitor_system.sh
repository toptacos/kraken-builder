#!/bin/bash

# Kraken Trading Bot - System Monitor
# Basic system health monitoring

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
INTERVAL=60
LOG_FILE="logs/monitor_system.log"

# Show usage
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage "./monitor_system.sh" "Monitor basic system health"
    echo "  -o, --once    Run once and exit"
    echo "  -r, --report  Generate system report"
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
    log_info "Generating system report..."
    # Simple report generation
    echo "System Report - $(date)" > "logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')% idle" >> "logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')" >> "logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    echo "Disk: $(df -h / | tail -1 | awk '{print $5}')" >> "logs/system_report_$(date +%Y%m%d_%H%M%S).txt"
    log_success "Report generated"
    exit 0
fi

log_header "SYSMON" "🔍 Starting System Monitoring"
log_info "Interval: ${INTERVAL}s, Log: $LOG_FILE"

while true; do
    log_info "=== System Check ==="

    # CPU usage
    cpu_idle=$(top -bn1 | grep "Cpu(s)" | awk '{print $8}')
    cpu_usage=$(echo "100 - $cpu_idle" | bc 2>/dev/null || echo "0")
    if [ "${cpu_usage%.*}" -gt 80 ]; then
        log_warning "High CPU usage: ${cpu_usage}%"
    else
        log_info "CPU usage: ${cpu_usage}%"
    fi

    # Memory usage
    memory_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$memory_usage" -gt 80 ]; then
        log_warning "High memory usage: ${memory_usage}%"
    else
        log_info "Memory usage: ${memory_usage}%"
    fi

    # Disk usage
    disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_warning "High disk usage: ${disk_usage}%"
    else
        log_info "Disk usage: ${disk_usage}%"
    fi

    # Network check
    if ping -c 1 -W 2 8.8.8.8 >/dev/null 2>&1; then
        log_success "Network OK"
    else
        log_warning "Network issues detected"
    fi

    log_info "=== Check Complete ==="

    if [ "$RUN_ONCE" = true ]; then
        log_info "One-time check complete"
        exit 0
    fi

    sleep "$INTERVAL"
done