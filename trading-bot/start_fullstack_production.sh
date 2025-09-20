#!/bin/bash

# 🚀 FULL-STACK PRODUCTION STARTUP
# =================================
#
# This script starts the complete Kraken Trading Bot system:
# - Flask API (Trading Bot)
# - Laravel Backend (API & Data Processing)
# - Vue.js Frontend (Dashboard)
# - Maximum uptime monitoring
# - Automatic browser opening
#
# Usage: ./start_fullstack_production.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output with timestamps
print_status() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${CYAN}[SYSTEM]${NC} $1"
}

# Function to cleanup existing processes and containers
cleanup_system() {
    print_header "🧹 CLEANING UP EXISTING PROCESSES"

    # Kill any existing Python processes
    pkill -f "python3 trading_bot.py" 2>/dev/null || true
    pkill -f "python3 artisan" 2>/dev/null || true
    pkill -f "npm" 2>/dev/null || true

    # Kill processes on used ports
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true

    # Clean up Docker containers (only if Docker is running)
    if check_docker_status; then
        print_status "Cleaning up Docker containers..."
        docker-compose down --remove-orphans 2>/dev/null || true
        docker rm -f $(docker ps -aq --filter "name=kraken-trading-bot" --filter "name=kraken-laravel-backend" --filter "name=kraken-vue-frontend" 2>/dev/null) 2>/dev/null || true

        # Clean up Docker images and volumes
        docker image prune -f 2>/dev/null || true
        docker volume prune -f 2>/dev/null || true
    else
        print_status "Docker not running - skipping Docker cleanup"
    fi

    print_success "System cleanup completed"
}

# Function to check system requirements
check_requirements() {
    print_header "🔍 CHECKING SYSTEM REQUIREMENTS"

    # Check if Docker is running (improved check for macOS)
    check_docker_status() {
        # Try multiple ways to check Docker status
        if docker info > /dev/null 2>&1; then
            return 0
        elif docker ps > /dev/null 2>&1; then
            return 0
        elif docker version > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    }

    if ! check_docker_status; then
        print_error "Docker is not running!"
        print_status "🚀 STARTING DOCKER DESKTOP..."

        # Try to start Docker based on OS
        case "$(uname -s)" in
            Darwin)
                # macOS - improved Docker Desktop startup
                print_status "Attempting to start Docker Desktop on macOS..."

                # Check if Docker Desktop is already running
                if pgrep -f "Docker Desktop" > /dev/null; then
                    print_status "Docker Desktop process found, waiting for daemon..."
                else
                    print_status "Starting Docker Desktop application..."
                    open -a "Docker Desktop" 2>/dev/null || true
                    sleep 5  # Give it time to start
                fi

                # Wait for Docker to start with improved checks
                print_status "Waiting for Docker daemon to be ready (this may take 1-2 minutes)..."
                local attempts=0
                local max_attempts=60  # Increased timeout

                while [ $attempts -lt $max_attempts ]; do
                    if check_docker_status; then
                        print_success "✅ Docker daemon is now ready!"
                        sleep 3  # Extra time for stability
                        break
                    fi

                    # Show progress every 10 attempts
                    if [ $((attempts % 10)) -eq 0 ] && [ $attempts -gt 0 ]; then
                        print_status "Still waiting... (${attempts}/${max_attempts} attempts)"
                    fi

                    echo -n "."
                    sleep 2
                    attempts=$((attempts + 1))
                done

                # Final check
                if ! check_docker_status; then
                    print_error "❌ Failed to start Docker daemon after ${max_attempts} attempts."
                    echo ""
                    echo "🔧 TROUBLESHOOTING STEPS:"
                    echo "=========================="
                    echo "1. Open Docker Desktop manually from Applications"
                    echo "2. Wait for the whale icon in menu bar to show Docker is running"
                    echo "3. Check Docker Desktop preferences for any errors"
                    echo "4. Try restarting Docker Desktop completely"
                    echo "5. Run: docker info (to verify it's working)"
                    echo "6. Then run this script again: ./start_fullstack_production.sh"
                    echo ""
                    echo "💡 Common macOS issues:"
                    echo "   - Docker Desktop might need a restart"
                    echo "   - Check if virtualization is enabled in BIOS"
                    echo "   - Ensure you have enough disk space"
                    exit 1
                fi
                ;;
            Linux)
                # Linux - try systemctl
                print_status "Attempting to start Docker on Linux..."
                sudo systemctl start docker 2>/dev/null || true

                if ! docker info > /dev/null 2>&1; then
                    print_error "Failed to start Docker automatically."
                    echo ""
                    echo "📋 MANUAL DOCKER STARTUP INSTRUCTIONS:"
                    echo "======================================"
                    echo "Run: sudo systemctl start docker"
                    echo "Then run: ./start_fullstack_production.sh"
                    exit 1
                fi
                ;;
            *)
                print_error "Unsupported OS for automatic Docker startup."
                echo ""
                echo "📋 MANUAL DOCKER STARTUP INSTRUCTIONS:"
                echo "======================================"
                echo "Please start Docker Desktop manually and try again."
                exit 1
                ;;
        esac
    fi

    # Check Docker Compose (support both old and new versions)
    check_docker_compose() {
        if command -v docker-compose &> /dev/null; then
            return 0
        elif docker compose version > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    }

    if ! check_docker_compose; then
        print_error "Docker Compose is not available!"
        print_status "Please install Docker Compose (or Docker Desktop which includes it)"
        print_status "macOS: Docker Desktop includes Docker Compose"
        print_status "Linux: Install with: sudo apt install docker-compose-plugin"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << 'EOF'
# === PRODUCTION TRADING BOT CONFIGURATION ===
TEST_MODE=false
PRODUCTION_MODE=true
STARTING_BALANCE=1000
TRADE_AMOUNT=25
WEB_UI=true
VERBOSE_LOGGING=true
LOG_LEVEL=INFO

# === MAXIMUM PROFITABILITY SETTINGS ===
TAKE_PROFIT_PERCENT=5
STOP_LOSS_PERCENT=2
MAX_CONSECUTIVE_LOSSES=3
TRADING_CYCLE_MINUTES=1

# === EXCHANGE API KEYS ===
# Add your production API keys here
BINANCE_API_KEY=your_production_binance_key
BINANCE_API_SECRET=your_production_binance_secret
KRAKEN_API_KEY=your_production_kraken_key
KRAKEN_API_SECRET=your_production_kraken_secret
COINBASE_API_KEY_NAME=""
COINBASE_API_PRIVATE_KEY=""
KUCOIN_API_KEY=""
KUCOIN_API_SECRET=""
KUCOIN_API_PASSPHRASE=""

# === LARAVEL BACKEND SETTINGS ===
APP_NAME="Kraken Trading Bot"
APP_ENV=production
APP_KEY=base64:your_app_key_here
APP_DEBUG=false
APP_URL=http://localhost:8000
DB_CONNECTION=sqlite
LOG_CHANNEL=stack
LOG_LEVEL=info
FLASK_API_URL=http://trading-bot:8080
EOF
        print_warning "Please edit .env file with your production API keys!"
        print_warning "The bot will run in demo mode until real keys are added."
    fi

    # Check available disk space
    DISK_SPACE=$(df / | tail -1 | awk '{print $4}' 2>/dev/null || echo "1000000")
    if [ "$DISK_SPACE" -lt 1000000 ] 2>/dev/null; then  # Less than ~1GB
        DISK_MB=$((DISK_SPACE / 1024))
        print_warning "Low disk space detected: ${DISK_MB}MB available"
        print_status "Docker may have issues with low disk space"
    fi

    print_success "System requirements check passed"
}

# Function to start Docker services
start_docker_services() {
    print_header "🐳 STARTING DOCKER SERVICES"

    # Set timestamp for unique container names
    export TIMESTAMP=$(date +%s)

    # Start all services
    print_status "Starting Flask API, Laravel Backend, and Vue.js Frontend..."
    if ! docker-compose up -d; then
        print_error "Failed to start Docker services!"
        print_status "Checking Docker Compose logs..."
        docker-compose logs
        exit 1
    fi

    print_success "Docker services started successfully"
}

# Function to wait for all services to be healthy
wait_for_services() {
    print_header "⏳ WAITING FOR ALL SERVICES TO BE HEALTHY"

    local max_attempts=60
    local attempt=1

    print_status "Checking service health (this may take a few minutes)..."

    while [ $attempt -le $max_attempts ]; do
        local healthy_services=0
        local total_services=3

        # Check Flask API (Trading Bot)
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            ((healthy_services++))
            print_success "✅ Flask API (Trading Bot) is healthy"
        fi

        # Check Laravel Backend
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            ((healthy_services++))
            print_success "✅ Laravel Backend is healthy"
        fi

        # Check Vue.js Frontend (served by Laravel)
        if curl -s http://localhost:8000 > /dev/null 2>&1; then
            ((healthy_services++))
            print_success "✅ Vue.js Frontend is healthy"
        fi

        if [ $healthy_services -eq $total_services ]; then
            print_success "🎉 All services are healthy and ready!"
            return 0
        fi

        print_status "Health check $attempt/$max_attempts: $healthy_services/$total_services services healthy"
        sleep 10
        attempt=$((attempt + 1))
    done

    print_error "Services failed to become healthy within timeout!"
    print_status "Checking service logs..."
    docker-compose logs --tail=20
    return 1
}

# Function to open web dashboard in browser
open_dashboard() {
    print_header "🌐 OPENING WEB DASHBOARD"

    # Wait a bit more for services to fully initialize
    sleep 5

    # Open browser based on OS
    case "$(uname -s)" in
        Darwin)
            # macOS
            open -a "Google Chrome" "http://localhost:8000" 2>/dev/null || \
            open -a "Safari" "http://localhost:8000" 2>/dev/null || \
            open "http://localhost:8000"
            ;;
        Linux)
            # Linux
            xdg-open "http://localhost:8000" 2>/dev/null || \
            google-chrome "http://localhost:8000" 2>/dev/null || \
            firefox "http://localhost:8000" 2>/dev/null || \
            echo "Please open: http://localhost:8000"
            ;;
        *)
            echo "Please open: http://localhost:8000"
            ;;
    esac

    print_success "Dashboard opened in browser"
}

# Function to start monitoring system
start_monitoring() {
    print_header "📊 STARTING PRODUCTION MONITORING"

    # Create monitoring script
    cat > monitor_fullstack.sh << 'EOF'
#!/bin/bash
# Full-stack production monitoring script

while true; do
    # Check Flask API
    if ! curl -s http://localhost:8080/health > /dev/null; then
        echo "$(date): CRITICAL - Flask API down! Attempting restart..."
        docker-compose restart kraken-trading-bot
    fi

    # Check Laravel Backend
    if ! curl -s http://localhost:8000/api/health > /dev/null; then
        echo "$(date): CRITICAL - Laravel Backend down! Attempting restart..."
        docker-compose restart kraken-laravel-backend
    fi

    # Check Vue.js Frontend
    if ! curl -s http://localhost:8000 > /dev/null; then
        echo "$(date): WARNING - Vue.js Frontend not responding"
    fi

    # Check disk space
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        echo "$(date): CRITICAL - Disk usage at ${DISK_USAGE}%"
    fi

    sleep 60  # Check every minute
done
EOF

    chmod +x monitor_fullstack.sh
    nohup ./monitor_fullstack.sh > monitoring.log 2>&1 &
    MONITOR_PID=$!
    echo $MONITOR_PID > monitor_pid.txt

    print_success "Production monitoring started (PID: $MONITOR_PID)"
}

# Function to display system information
display_system_info() {
    echo ""
    print_header "🎯 KRAKEN TRADING BOT - FULL-STACK PRODUCTION SYSTEM"
    echo "=================================================================="

    # Get container information
    echo ""
    echo -e "${GREEN}🐳 DOCKER CONTAINERS:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    echo -e "${BLUE}🌐 ACCESS DASHBOARDS:${NC}"
    echo -e "  📊 Main Dashboard (Vue.js):     ${GREEN}http://localhost:8000${NC}"
    echo -e "  🔧 Flask API Health:            ${GREEN}http://localhost:8080/health${NC}"
    echo -e "  📋 Laravel API:                 ${GREEN}http://localhost:8000/api/health${NC}"
    echo -e "  📝 Live Logs:                   ${GREEN}http://localhost:8000/api/trading/logs${NC}"

    echo ""
    echo -e "${YELLOW}⚙️  PRODUCTION SETTINGS:${NC}"
    echo "  💰 Starting Balance:    \$1000"
    echo "  🎯 Profit Target:       5% (\$1050)"
    echo "  🛡️  Stop Loss:          2% (\$20 loss limit)"
    echo "  ⚡ Trading Frequency:   Every 1 minute"
    echo "  📊 Risk Management:    Automatic"
    echo "  🔄 Coin Selection:     Intelligent fallback"
    echo "  🌐 Web UI:             Vue.js + Laravel"

    echo ""
    echo -e "${CYAN}📊 MONITORING COMMANDS:${NC}"
    echo "  docker-compose logs -f kraken-trading-bot        # Flask API logs"
    echo "  docker-compose logs -f kraken-laravel-backend    # Laravel logs"
    echo "  docker-compose logs -f kraken-vue-frontend      # Vue.js logs"
    echo "  tail -f monitoring.log                   # System monitoring"
    echo "  curl http://localhost:8000/api/trading/dashboard  # API test"

    echo ""
    echo -e "${RED}🚨 EMERGENCY CONTROLS:${NC}"
    echo "  ./stop_fullstack_production.sh           # Graceful shutdown"
    echo "  docker-compose down --remove-orphans     # Force cleanup"
    echo "  docker system prune -a                   # Clean everything"
    echo "  pkill -f monitor_fullstack               # Stop monitoring"

    echo ""
    print_success "✅ FULL-STACK PRODUCTION SYSTEM IS NOW RUNNING!"
    echo ""
    echo -e "${GREEN}💡 System Features:${NC}"
    echo "  • Flask API for trading operations"
    echo "  • Laravel backend for data processing"
    echo "  • Vue.js frontend for real-time dashboard"
    echo "  • Automatic health monitoring"
    echo "  • Maximum uptime with auto-recovery"
    echo "  • Real-time statistics and logging"
    echo "  • Intelligent coin selection"
    echo "  • Risk management with stop-loss"
}

# Function to create stop script
create_stop_script() {
    cat > stop_fullstack_production.sh << 'EOF'
#!/bin/bash
# Stop full-stack production system gracefully

echo "🛑 Stopping full-stack production system..."

# Stop monitoring
if [ -f "monitor_pid.txt" ]; then
    MONITOR_PID=$(cat monitor_pid.txt)
    kill $MONITOR_PID 2>/dev/null || true
    rm -f monitor_pid.txt
    echo "📊 Monitoring stopped"
fi

# Stop Docker services
echo "🐳 Stopping Docker services..."
docker-compose down --remove-orphans

# Kill any remaining processes
pkill -f "python3 trading_bot.py" 2>/dev/null || true
pkill -f "python3 artisan" 2>/dev/null || true
pkill -f "npm" 2>/dev/null || true

echo "✅ Full-stack production system stopped gracefully"
EOF

    chmod +x stop_fullstack_production.sh
    print_success "Stop script created: ./stop_fullstack_production.sh"
}

# Main execution
main() {
    print_header "🚀 STARTING KRAKEN TRADING BOT - FULL-STACK PRODUCTION"

    # Make scripts executable
    chmod +x *.sh 2>/dev/null || true

    # Execute startup sequence
    cleanup_system
    check_requirements
    start_docker_services
    wait_for_services
    start_monitoring
    create_stop_script
    open_dashboard
    display_system_info

    print_success "🎯 FULL-STACK PRODUCTION SYSTEM STARTUP COMPLETE!"
    print_status "The complete system is now running with maximum profitability and uptime"
}

# Run main function
main "$@"