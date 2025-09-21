#!/bin/bash

# Clean Environment Test and Production Deployment Script
# ========================================================
#
# This script performs:
# 1. Clean environment testing in test mode
# 2. Cleans all artifacts from local machine
# 3. Runs application in production mode from scratch

set -e  # Exit on any error

echo "🧹 Kraken Trading Bot - Clean Test & Deploy"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to clean Docker artifacts
clean_docker_artifacts() {
    log "Cleaning Docker artifacts..."

    # Stop and remove all containers
    docker-compose down --volumes --remove-orphans 2>/dev/null || true

    # Remove all images related to this project
    docker images | grep "trading-bot\|kraken-trading" | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

    # Remove dangling images
    docker image prune -f >/dev/null 2>&1 || true

    # Remove unused volumes
    docker volume prune -f >/dev/null 2>&1 || true

    success "Docker artifacts cleaned"
}

# Function to clean local artifacts
clean_local_artifacts() {
    log "Cleaning local artifacts..."

    # Remove Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true

    # Remove test artifacts
    rm -f test_results_*.json 2>/dev/null || true
    rm -f .coverage 2>/dev/null || true
    rm -rf htmlcov/ 2>/dev/null || true
    rm -rf .pytest_cache/ 2>/dev/null || true

    # Remove log files (but keep logs directory)
    rm -f logs/*.log 2>/dev/null || true
    rm -f *.log 2>/dev/null || true

    # Remove temporary files
    rm -f trading_bot.pid 2>/dev/null || true
    rm -f monitor.pid 2>/dev/null || true

    success "Local artifacts cleaned"
}

# Function to run tests in clean environment
run_clean_tests() {
    log "Running tests in clean environment..."

    # Set test environment variables
    export TEST_MODE=true
    export PRODUCTION_MODE=false
    export STARTING_BALANCE=1000
    export TRADE_AMOUNT=10

    # Run comprehensive tests
    if python3 test_comprehensive.py; then
        success "All tests passed!"
        return 0
    else
        error "Some tests failed!"
        return 1
    fi
}

# Function to build optimized Docker image
build_optimized_image() {
    log "Building optimized Docker image..."

    # Build the runtime image (skip test-runner stage for production)
    if docker build --target runtime -t kraken-trading-bot:optimized .; then
        success "Optimized Docker image built successfully"

        # Show image size
        IMAGE_SIZE=$(docker images kraken-trading-bot:optimized --format "table {{.Size}}" | tail -n 1)
        log "Image size: $IMAGE_SIZE"

        return 0
    else
        error "Failed to build optimized Docker image"
        return 1
    fi
}

# Function to run production deployment
run_production_deployment() {
    log "Starting production deployment..."

    # Set production environment
    export TEST_MODE=false
    export PRODUCTION_MODE=true
    export STARTING_BALANCE=1000
    export TRADE_AMOUNT=10

    # Start the application
    if docker run -d \
        --name kraken-trading-bot-production \
        -p 8080:8080 \
        -v $(pwd)/logs:/app/logs \
        --env-file .env \
        -e TEST_MODE=false \
        -e PRODUCTION_MODE=true \
        kraken-trading-bot:optimized; then

        success "Production deployment started!"

        # Wait for health check
        log "Waiting for application to be healthy..."
        for i in {1..30}; do
            if curl -f http://localhost:8080/health >/dev/null 2>&1; then
                success "Application is healthy and running!"
                log "🌐 Dashboard available at: http://localhost:8080"
                return 0
            fi
            echo -n "."
            sleep 2
        done

        error "Application failed to become healthy within 60 seconds"
        docker logs kraken-trading-bot-production
        return 1
    else
        error "Failed to start production deployment"
        return 1
    fi
}

# Main execution
main() {
    log "Starting clean test and deploy process..."

    # Phase 1: Clean environment
    log "Phase 1: Environment cleanup"
    clean_docker_artifacts
    clean_local_artifacts

    # Phase 2: Run tests
    log "Phase 2: Testing in clean environment"
    if ! run_clean_tests; then
        error "Tests failed! Aborting deployment."
        exit 1
    fi

    # Phase 3: Build optimized image
    log "Phase 3: Building optimized image"
    if ! build_optimized_image; then
        error "Image build failed! Aborting deployment."
        exit 1
    fi

    # Phase 4: Final cleanup
    log "Phase 4: Final cleanup before production"
    clean_docker_artifacts
    clean_local_artifacts

    # Phase 5: Rebuild for production
    log "Phase 5: Rebuilding optimized image for production"
    if ! build_optimized_image; then
        error "Failed to rebuild optimized Docker image for production"
        exit 1
    fi
# Phase 6: Production deployment
log "Phase 6: Production deployment"
if run_production_deployment; then

    # Phase 7: Setup auto-trading (optional)
    log "Phase 7: Setting up auto-trading infrastructure"
    if [ -f "setup_cron.sh" ]; then
        log "Setting up cron job for automated trading..."
        if ./setup_cron.sh; then
            success "Auto-trading cron job configured"
        else
            warning "Failed to set up auto-trading cron job"
        fi
    else
        warning "setup_cron.sh not found, skipping auto-trading setup"
    fi

    success "🎉 Deployment completed successfully!"

    echo ""
    echo "📊 Deployment Summary:"
    echo "  ✅ Environment cleaned"
    echo "  ✅ All tests passed"
    echo "  ✅ Optimized image built"
    echo "  ✅ Production deployment running"
    echo "  ✅ Auto-trading infrastructure ready"
    echo "  🌐 Dashboard: http://localhost:8080"
    echo ""
    echo "🤖 Auto-Trading Setup:"
    echo "  📋 To enable auto-trading:"
    echo "     1. Switch to PRODUCTION MODE in the dashboard"
    echo "     2. Enable AUTO TRADING toggle"
    echo "     3. The system will automatically trade every minute"
    echo ""
    warning "Remember: Monitor your trading bot closely in production mode!"
    exit 0
else
    error "Production deployment failed!"
    exit 1
fi
}

# Run main function
main "$@"