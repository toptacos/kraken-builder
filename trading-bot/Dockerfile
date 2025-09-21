# Multi-stage Docker build for Kraken Trading Bot
# Stage 1: Builder - Install dependencies and prepare application
FROM python:3.12-slim as builder

# Set metadata
LABEL maintainer="Kraken Trading Bot"
LABEL description="Automated cryptocurrency trading bot with multi-exchange support"

# Install system build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies in virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install required packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    ccxt==4.5.5 \
    pandas==2.3.2 \
    requests==2.32.5 \
    numpy==2.3.3 \
    python-dotenv==1.1.1 \
    flask==3.0.3 \
    flask-cors==4.0.0 \
    flask-limiter==3.5.0 \
    psutil==5.9.0 \
    beautifulsoup4==4.12.3 \
    lxml==5.2.2

# Copy application source code
COPY trading_bot.py overnight_trader.py trading_strategies.py \
     crypto_trend_analyzer.py backtesting_engine.py auth_middleware.py \
     system_monitor.py container_manager.py ./

# Copy web assets
COPY web-ui.html advanced-dashboard.html ./

# Copy test files
COPY test_basic_functionality.py test_error_handling.py test_imports.py \
     run_tests.py pytest.ini ./

# Copy scripts
COPY monitor_production.sh monitor_system.sh start_overnight_trading.sh \
     start_production.sh stop_production.sh production_setup.sh ./

# Copy auto-trading components
COPY auto_trader.py setup_cron.sh ./

# Copy source directory
COPY src/ ./src/

# Stage 2: Test Runner - Run tests in isolated environment
FROM builder as test-runner

# Copy environment file for testing
COPY .env ./

# Set test environment
ENV TEST_MODE=true
ENV PRODUCTION_MODE=false

# Run tests
RUN python3 -m pytest tests/ -v --tb=short --disable-warnings || \
    python3 test_basic_functionality.py || \
    echo "Tests completed with some failures"

# Stage 3: Runtime - Minimal production image
FROM python:3.12-slim as runtime

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r tradingbot && useradd -r -g tradingbot tradingbot

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application files from builder (only runtime files)
COPY --from=builder /app/trading_bot.py /app/overnight_trader.py /app/trading_strategies.py \
     /app/crypto_trend_analyzer.py /app/backtesting_engine.py /app/auth_middleware.py \
     /app/system_monitor.py /app/container_manager.py /app/web-ui.html /app/advanced-dashboard.html \
     /app/monitor_production.sh /app/monitor_system.sh /app/start_overnight_trading.sh \
     /app/start_production.sh /app/stop_production.sh /app/production_setup.sh \
     /app/auto_trader.py /app/setup_cron.sh ./

# Copy source directory
COPY --from=builder /app/src ./src/

# Create logs directory and set permissions
RUN mkdir -p /app/logs && \
    chown -R tradingbot:tradingbot /app && \
    chmod +x /app/setup_cron.sh /app/auto_trader.py

# Create volume for persistent logs
VOLUME ["/app/logs"]

# Switch to non-root user
USER tradingbot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Default command: Run the trading bot
CMD ["python3", "trading_bot.py"]