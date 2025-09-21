#!/bin/bash

# Kraken Trading Bot - Build and Deploy Script
# ============================================
#
# This script provides a comprehensive build, test, and deployment pipeline for the trading bot.
#
# Features:
# - Clean build process with dependency management
# - Automated testing with coverage reporting
# - Docker container management
# - Graceful service restart
# - Health checks and rollback capabilities
# - Environment-specific configurations
# - Support for both Python and PHP implementations
#
# Usage:
#   ./build_and_deploy.sh --build        # Build and test
#   ./build_and_deploy.sh --deploy       # Deploy to production
#   ./build_and_deploy.sh --restart      # Restart services
#   ./build_and_deploy.sh --rollback     # Rollback to previous version
#   ./build_and_deploy.sh --status       # Check service status
#   ./build_and_deploy.sh --stop         # Stop all services
#   ./build_and_deploy.sh --php          # Use PHP implementation (FrankenPHP)
#   ./build_and_deploy.sh --python       # Use Python implementation
#   ./build_and_deploy.sh --help         # Show help

set -e  # Exit on any error

# Configuration
PROJECT_NAME="kraken-trading-bot"
BACKUP_DIR="./backups"
LOG_DIR="./logs"
DOCKER_IMAGE_NAME="kraken-trading-bot"
DOCKER_TAG="latest"
COMPOSE_FILE="docker-compose.yml"
PHP_COMPOSE_FILE="docker-compose.frankenphp.yml"
HEALTH_CHECK_TIMEOUT=60
USE_PHP=false
REQUIRED_COMMANDS=("docker" "docker-compose" "curl")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Create directories
create_directories() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
}

# Show usage information
show_help() {
    cat << EOF
Kraken Trading Bot - Build and Deploy Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --build         Build the application (dependencies, tests, Docker images)
    --deploy        Deploy the application to production
    --restart       Restart all services
    --rollback      Rollback to previous deployment
    --status        Check status of all services
    --stop          Stop all services
    --php           Use PHP implementation (FrankenPHP)
    --python        Use Python implementation (default)
    --help          Show this help message

EXAMPLES:
    $0 --build              # Build and test the application
    $0 --deploy             # Deploy to production
    $0 --restart            # Restart services
    $0 --status             # Check service status
    $0 --rollback           # Rollback deployment

ENVIRONMENT VARIABLES:
    TEST_MODE       Set to 'true' for test mode (default: false)
    VERBOSE         Set to 'true' for verbose output (default: false)
    BACKUP_ENABLED  Set to 'false' to disable backups (default: true)

FILES:
    docker-compose.yml      Docker Compose configuration
    Dockerfile             Docker image definition
    requirements.txt       Python dependencies
    .env                   Environment variables

For more information, see the README.md file.
EOF
}

# Check if required commands are available
check_dependencies() {
    log_info "Checking system dependencies..."

    local missing_deps=()

    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_error "Please install missing dependencies and try again."
        return 1
    fi

    log_success "All system dependencies are available"
    return 0
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies..."

    # Upgrade pip
    if ! python3 -m pip install --upgrade pip --quiet; then
        log_error "Failed to upgrade pip"
        return 1
    fi

    # Install dependencies
    if ! python3 -m pip install -r requirements.txt --quiet; then
        log_error "Failed to install Python dependencies"
        return 1
    fi

    log_success "Python dependencies installed successfully"
    return 0
}

# Run tests
run_tests() {
    log_info "Running test suite..."

    if [ ! -d "tests" ]; then
        log_warning "No tests directory found, skipping tests"
        return 0
    fi

    # Check if pytest is available
    if ! python3 -c "import pytest" 2>/dev/null; then
        log_warning "pytest not available, running basic functionality test instead"
        if ! python3 test_basic_functionality.py; then
            log_error "Basic functionality tests failed"
            return 1
        fi
        return 0
    fi

    # Run tests (different for PHP vs Python)
    if [ "$USE_PHP" = true ]; then
        if ! php test_php_functionality.php; then
            log_error "PHP test suite failed"
            return 1
        fi
    else
        if ! python3 -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80 -v; then
            log_error "Python test suite failed"
            return 1
        fi
    fi

    log_success "All tests passed!"
    return 0
}

# Build Docker images
build_docker_images() {
    log_info "Building Docker images..."

    # Build main application image
    if ! docker build -t "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}" .; then
        log_error "Failed to build Docker image"
        return 1
    fi

    # Build FrankenPHP image if it exists
    if [ -f "frankenphp.dockerfile" ]; then
        if ! docker build -f frankenphp.dockerfile -t "kraken-frankenphp:latest" .; then
            log_error "Failed to build FrankenPHP image"
            return 1
        fi
    fi

    log_success "Docker images built successfully"
    return 0
}

# Create backup
create_backup() {
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_path="${BACKUP_DIR}/backup_${timestamp}"

    log_info "Creating backup at ${backup_path}"

    mkdir -p "$backup_path"

    # Backup important files
    local files_to_backup=(
        "trading_bot.py"
        "overnight_trader.py"
        "crypto_trend_analyzer.py"
        "requirements.txt"
        "docker-compose.yml"
        "Dockerfile"
        ".env"
    )

    for file in "${files_to_backup[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "${backup_path}/"
            log_info "Backed up: $file"
        fi
    done

    log_success "Backup created successfully at ${backup_path}"
    echo "$backup_path"
}

# Start services
start_services() {
    log_info "Starting services..."

    # Stop any existing services first
    docker-compose down --remove-orphans 2>/dev/null || true

    # Start services
    if [ "$USE_PHP" = true ]; then
        if ! docker-compose -f "$COMPOSE_FILE" up -d --build frankenphp trading-bot; then
            log_error "Failed to start PHP services"
            return 1
        fi
    else
        if ! docker-compose -f "$COMPOSE_FILE" up -d --build; then
            log_error "Failed to start services"
            return 1
        fi
    fi

    log_success "Services started successfully"
    return 0
}

# Stop services
stop_services() {
    log_info "Stopping services..."

    if [ "$USE_PHP" = true ]; then
        if ! docker-compose -f "$COMPOSE_FILE" down --remove-orphans; then
            log_warning "Some PHP services may not have stopped cleanly"
        fi
    else
        if ! docker-compose -f "$COMPOSE_FILE" down --remove-orphans; then
            log_warning "Some services may not have stopped cleanly"
        fi
    fi

    log_success "Services stopped"
    return 0
}

# Health check
health_check() {
    local timeout=${1:-$HEALTH_CHECK_TIMEOUT}
    log_info "Performing health checks (timeout: ${timeout}s)..."

    local start_time
    start_time=$(date +%s)

    while true; do
        local current_time
        current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [ $elapsed -ge $timeout ]; then
            log_error "Health check timeout after ${timeout} seconds"
            return 1
        fi

        # Check API health (different for PHP vs Python)
        if [ "$USE_PHP" = true ]; then
            # Check FrankenPHP health
            if curl -f -s "http://localhost:80/health" >/dev/null 2>&1; then
                log_success "FrankenPHP API is healthy"

                # Check if bot is initialized
                if curl -f -s "http://localhost:80/status" >/dev/null 2>&1; then
                    log_success "PHP Trading bot is running"
                    return 0
                else
                    log_info "PHP Trading bot not yet initialized, waiting..."
                fi
            else
                log_info "FrankenPHP API not ready, waiting..."
            fi
        else
            # Check Flask API health
            if curl -f -s "http://localhost:8080/health" >/dev/null 2>&1; then
                log_success "Flask API is healthy"

                # Check if bot is initialized
                if curl -f -s "http://localhost:8080/status" >/dev/null 2>&1; then
                    log_success "Trading bot is running"
                    return 0
                else
                    log_info "Trading bot not yet initialized, waiting..."
                fi
            else
                log_info "Flask API not ready, waiting..."
            fi
        fi

        sleep 5
    done
}

# Cleanup old images
cleanup_old_images() {
    log_info "Cleaning up old Docker images..."

    # Remove dangling images
    docker image prune -f >/dev/null 2>&1 || true

    # Remove old images (keep last 3 versions)
    local images_to_remove
    images_to_remove=$(docker images "${DOCKER_IMAGE_NAME}" --format "{{.Repository}}:{{.Tag}}" | tail -n +4)

    if [ -n "$images_to_remove" ]; then
        echo "$images_to_remove" | xargs docker rmi -f >/dev/null 2>&1 || true
        log_info "Cleaned up old Docker images"
    fi

    return 0
}

# Build process
build() {
    log_info "🚀 Starting build process..."

    # Create backup if enabled
    if [ "${BACKUP_ENABLED:-true}" = "true" ]; then
        create_backup
    fi

    # Check dependencies
    if ! check_dependencies; then
        return 1
    fi

    # Install dependencies (skip Python if using PHP)
    if [ "$USE_PHP" = false ]; then
        if ! install_python_dependencies; then
            return 1
        fi
    else
        log_info "Using PHP implementation - skipping Python dependencies"
    fi

    # Run tests
    if ! run_tests; then
        return 1
    fi

    # Build Docker images
    if ! build_docker_images; then
        return 1
    fi

    # Cleanup
    cleanup_old_images

    log_success "✅ Build process completed successfully!"
    return 0
}

# Deploy process
deploy() {
    log_info "🚀 Starting deployment process..."

    # Stop existing services
    stop_services

    # Start new services
    if ! start_services; then
        log_error "❌ Failed to start services"
        return 1
    fi

    # Perform health checks
    if ! health_check; then
        log_error "❌ Health checks failed"
        log_info "🔄 Attempting rollback..."
        if ! rollback; then
            log_error "❌ Rollback also failed"
        fi
        return 1
    fi

    log_success "✅ Deployment completed successfully!"
    return 0
}

# Restart services
restart() {
    log_info "🔄 Restarting services..."

    if ! stop_services; then
        log_warning "⚠️ Warning: Could not stop all services cleanly"
    fi

    if ! start_services; then
        log_error "❌ Failed to restart services"
        return 1
    fi

    if ! health_check; then
        log_error "❌ Services failed health checks after restart"
        return 1
    fi

    log_success "✅ Services restarted successfully!"
    return 0
}

# Rollback deployment
rollback() {
    log_info "🔄 Starting rollback process..."

    # Find latest backup
    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -name "backup_*" -type d -print0 2>/dev/null | xargs -0 ls -td | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "❌ No backups found for rollback"
        return 1
    fi

    log_info "Rolling back to backup: $latest_backup"

    # Stop services
    stop_services

    # Restore files from backup
    for file in "$latest_backup"/*; do
        if [ -f "$file" ]; then
            local filename
            filename=$(basename "$file")
            cp "$file" "./$filename"
            log_info "Restored: $filename"
        fi
    done

    # Restart services
    if ! start_services; then
        log_error "❌ Failed to restart services after rollback"
        return 1
    fi

    if ! health_check; then
        log_error "❌ Services failed health checks after rollback"
        return 1
    fi

    log_success "✅ Rollback completed successfully!"
    return 0
}

# Check service status
status() {
    log_info "📊 Checking service status..."

    # Check Docker containers
    echo ""
    log_info "🐳 Docker Containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || log_warning "No containers running"

    # Check Docker Compose services
    echo ""
    log_info "📋 Docker Compose Services:"
    docker-compose ps 2>/dev/null || log_warning "Docker Compose not configured"

    # Check API health
    echo ""
    log_info "🌐 API Health Check:"
    if [ "$USE_PHP" = true ]; then
        if curl -f -s "http://localhost:80/health" >/dev/null 2>&1; then
            log_success "✅ FrankenPHP API: Healthy"
            # Try to get health details
            local health_data
            health_data=$(curl -s "http://localhost:80/health" 2>/dev/null)
            if [ -n "$health_data" ]; then
                echo "   Status: $(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
                echo "   Uptime: $(echo "$health_data" | grep -o '"uptime":"[^"]*"' | cut -d'"' -f4)"
            fi
        else
            log_error "❌ FrankenPHP API: Unhealthy"
        fi
    else
        if curl -f -s "http://localhost:8080/health" >/dev/null 2>&1; then
            log_success "✅ Flask API: Healthy"
            # Try to get health details
            local health_data
            health_data=$(curl -s "http://localhost:8080/health" 2>/dev/null)
            if [ -n "$health_data" ]; then
                echo "   Status: $(echo "$health_data" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
                echo "   Uptime: $(echo "$health_data" | grep -o '"uptime":"[^"]*"' | cut -d'"' -f4)"
            fi
        else
            log_error "❌ Flask API: Unhealthy"
        fi
    fi

    # Check Laravel API if available
    echo ""
    log_info "🔧 Laravel API Health Check:"
    if curl -f -s "http://localhost:8000/api/health" >/dev/null 2>&1; then
        log_success "✅ Laravel API: Healthy"
    else
        log_error "❌ Laravel API: Unhealthy"
    fi

    return 0
}

# Main function
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --php)
                USE_PHP=true
                COMPOSE_FILE="$PHP_COMPOSE_FILE"
                REQUIRED_COMMANDS+=("php")
                log_info "Using PHP implementation (FrankenPHP)"
                shift
                ;;
            --python)
                USE_PHP=false
                COMPOSE_FILE="docker-compose.yml"
                REQUIRED_COMMANDS+=("python3" "pip")
                log_info "Using Python implementation"
                shift
                ;;
            --build)
                create_directories
                if build; then
                    log_success "Build completed successfully!"
                    exit 0
                else
                    log_error "Build failed!"
                    exit 1
                fi
                ;;
            --deploy)
                create_directories
                if deploy; then
                    log_success "Deployment completed successfully!"
                    exit 0
                else
                    log_error "Deployment failed!"
                    exit 1
                fi
                ;;
            --restart)
                if restart; then
                    log_success "Restart completed successfully!"
                    exit 0
                else
                    log_error "Restart failed!"
                    exit 1
                fi
                ;;
            --rollback)
                if rollback; then
                    log_success "Rollback completed successfully!"
                    exit 0
                else
                    log_error "Rollback failed!"
                    exit 1
                fi
                ;;
            --status)
                status
                exit 0
                ;;
            --stop)
                stop_services
                exit 0
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Invalid option: $1"
                echo ""
                show_help
                exit 1
                ;;
        esac
    done

    # If no arguments provided, show help
    if [ $# -eq 0 ]; then
        show_help
        exit 1
    fi
}

# Run main function with all arguments
main "$@"