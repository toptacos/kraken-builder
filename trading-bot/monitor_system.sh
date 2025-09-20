#!/bin/bash

# Kraken Trading Bot - System Monitoring Script
# Basic system health monitoring for the trading environment

set -e

# Configuration
MONITOR_INTERVAL=60  # seconds
LOG_FILE="/app/logs/monitor_system.log"
ALERT_EMAIL=""  # Set this to receive email alerts

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

# Send alert
send_alert() {
    local subject="$1"
    local message="$2"

    log_error "ALERT: $subject - $message"

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Check CPU usage
check_cpu() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

    if [ "${cpu_usage%.*}" -gt 90 ]; then
        send_alert "Critical CPU Usage" "CPU usage is at ${cpu_usage}%"
    elif [ "${cpu_usage%.*}" -gt 80 ]; then
        log_warning "High CPU usage: ${cpu_usage}%"
    else
        log_info "CPU usage: ${cpu_usage}%"
    fi
}

# Check memory usage
check_memory() {
    local memory_info=$(free | grep Mem)
    local memory_usage=$(echo "$memory_info" | awk '{printf "%.0f", $3/$2 * 100.0}')
    local memory_used=$(echo "$memory_info" | awk '{print $3}')
    local memory_total=$(echo "$memory_info" | awk '{print $2}')

    if [ "$memory_usage" -gt 90 ]; then
        send_alert "Critical Memory Usage" "Memory usage is at ${memory_usage}% (${memory_used}KB/${memory_total}KB)"
    elif [ "$memory_usage" -gt 80 ]; then
        log_warning "High memory usage: ${memory_usage}% (${memory_used}KB/${memory_total}KB)"
    else
        log_info "Memory usage: ${memory_usage}% (${memory_used}KB/${memory_total}KB)"
    fi
}

# Check disk space
check_disk() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    local disk_available=$(df -h / | tail -1 | awk '{print $4}')

    if [ "$disk_usage" -gt 95 ]; then
        send_alert "Critical Disk Space" "Disk usage is at ${disk_usage}% (${disk_available} available)"
    elif [ "$disk_usage" -gt 90 ]; then
        log_warning "Low disk space: ${disk_usage}% (${disk_available} available)"
    else
        log_info "Disk usage: ${disk_usage}% (${disk_available} available)"
    fi
}

# Check network connectivity
check_network() {
    # Test basic internet connectivity
    if ping -c 1 -W 5 8.8.8.8 > /dev/null 2>&1; then
        log_success "Network connectivity OK"
    else
        send_alert "Network Connectivity Issue" "Cannot reach internet (8.8.8.8)"
    fi

    # Test DNS resolution
    if nslookup google.com > /dev/null 2>&1; then
        log_success "DNS resolution OK"
    else
        log_warning "DNS resolution issue detected"
    fi
}

# Check system load
check_load() {
    local load_info=$(uptime | awk -F'load average:' '{print $2}')
    local load_1m=$(echo "$load_info" | awk -F',' '{print $1}' | sed 's/ //g')
    local load_5m=$(echo "$load_info" | awk -F',' '{print $2}' | sed 's/ //g')
    local load_15m=$(echo "$load_info" | awk -F',' '{print $3}' | sed 's/ //g')

    log_info "System load - 1m: $load_1m, 5m: $load_5m, 15m: $load_15m"

    # Get number of CPU cores
    local cpu_cores=$(nproc 2>/dev/null || echo "1")

    # Check if load is too high (load > cores * 2)
    local threshold=$(echo "$cpu_cores * 2" | bc -l 2>/dev/null || echo "2")

    if [ "$(echo "$load_1m > $threshold" | bc -l 2>/dev/null)" = "1" ]; then
        log_warning "High system load: $load_1m (threshold: $threshold)"
    fi
}

# Check running processes
check_processes() {
    local total_processes=$(ps aux | wc -l)
    local zombie_processes=$(ps aux | grep -c " Z " || echo "0")

    log_info "Total processes: $total_processes"

    if [ "$zombie_processes" -gt 0 ]; then
        log_warning "Zombie processes detected: $zombie_processes"
    fi

    # Check for critical trading processes
    if pgrep -f "python3 trading_bot.py" > /dev/null; then
        log_success "Trading bot process running"
    else
        log_warning "Trading bot process not found"
    fi
}

# Generate system report
generate_system_report() {
    log_info "Generating system monitoring report..."

    local report_file="/app/logs/system_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" << EOF
Kraken Trading Bot - System Monitoring Report
===========================================

Report Date: $(date)
Monitoring Period: $MONITOR_INTERVAL seconds

System Information:
------------------
Hostname: $(hostname)
OS: $(uname -s) $(uname -r)
Uptime: $(uptime)

Resource Usage:
--------------
CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')%
Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')
Disk: $(df -h / | tail -1 | awk '{print $5 " (" $4 " available)"}')
Load Average: $(uptime | awk -F'load average:' '{print $2}')

Network Status:
--------------
Internet: $(ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1 && echo "Connected" || echo "Disconnected")
DNS: $(nslookup google.com > /dev/null 2>&1 && echo "Working" || echo "Issue")

Process Information:
-------------------
Total Processes: $(ps aux | wc -l)
Trading Bot: $(pgrep -f "python3 trading_bot.py" > /dev/null && echo "Running" || echo "Not Running")

Report generated: $(date)
EOF

    log_success "System report generated: $report_file"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -o, --once          Run monitoring once and exit"
    echo "  -r, --report        Generate system report"
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
        generate_system_report
        exit 0
    fi

    log_info "Starting Kraken Trading Bot system monitoring..."
    log_info "Monitoring interval: $MONITOR_INTERVAL seconds"
    log_info "Log file: $LOG_FILE"

    while true; do
        log_info "=== Starting system monitoring cycle ==="

        check_cpu
        check_memory
        check_disk
        check_network
        check_load
        check_processes

        log_info "=== System monitoring cycle completed ==="

        if [ "$run_once" = true ]; then
            generate_system_report
            log_info "System monitoring completed (run once mode)"
            exit 0
        fi

        log_info "Waiting $MONITOR_INTERVAL seconds until next check..."
        sleep "$MONITOR_INTERVAL"
    done
}

# Error handling
trap 'log_error "System monitoring script failed with exit code $?"' ERR

# Run main function
main "$@"