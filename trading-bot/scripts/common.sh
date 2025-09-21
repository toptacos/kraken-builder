#!/bin/bash

# Kraken Trading Bot - Common Utilities
# Simple, reusable functions for all scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Simple logging functions
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
    echo -e "${PURPLE}[$1]${NC} $2"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version (returns 0 if >= 3.8)
check_python_version() {
    if ! command_exists python3; then
        return 1
    fi

    local version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -gt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -ge 8 ]); then
        return 0
    else
        return 1
    fi
}

# Install Python dependencies (handles macOS externally managed environment)
install_python_deps() {
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found!"
        return 1
    fi

    # Check for externally managed environment
    if python3 -m pip install --dry-run --quiet pip 2>&1 | grep -q "externally-managed-environment"; then
        log_info "Using --user flag for macOS/Homebrew Python"
        pip3 install --user -r requirements.txt
    else
        pip3 install -r requirements.txt
    fi
}

# Kill process by name
kill_process() {
    local process_name="$1"
    pkill -f "$process_name" 2>/dev/null || true
}

# Kill process by port
kill_port() {
    local port="$1"
    lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
}

# Check if port is in use
check_port() {
    local port="$1"
    if lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Wait for service to be ready
wait_for_service() {
    local url="$1"
    local timeout="${2:-30}"
    local count=0

    log_info "Waiting for service at $url..."

    while [ $count -lt $timeout ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            log_success "Service is ready!"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done

    log_error "Service failed to start within $timeout seconds"
    return 1
}

# Create directory if it doesn't exist
ensure_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
    fi
}

# Check if file exists
file_exists() {
    [ -f "$1" ]
}

# Print usage for scripts
show_usage() {
    local script_name="$1"
    local description="$2"

    echo "Usage: $script_name"
    echo "$description"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
}