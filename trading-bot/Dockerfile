# Kraken Trading Bot - Optimized Docker Image
FROM python:3.12-slim

# Set metadata
LABEL maintainer="Kraken Trading Bot"
LABEL description="Automated cryptocurrency trading bot with multi-exchange support"

# Set working directory
WORKDIR /app

# Install system dependencies (minimal and optimized)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip

# Install required packages first
RUN pip install --no-cache-dir \
    ccxt==4.5.5 \
    pandas==2.3.2 \
    requests==2.32.5 \
    numpy==2.3.3 \
    python-dotenv==1.1.1 \
    flask==3.0.3

# Install optional packages (continue if they fail)
RUN pip install --no-cache-dir flask-cors==4.0.0 flask-limiter==3.5.0 psutil==5.9.0 beautifulsoup4==4.12.3 lxml==5.2.2 || \
    echo "Some optional packages failed to install, continuing..."

# Copy application files
COPY trading_bot.py .env ./
COPY overnight_trader.py ./
COPY trading_strategies.py ./
COPY crypto_trend_analyzer.py ./
COPY backtesting_engine.py ./
COPY auth_middleware.py ./
COPY system_monitor.py ./
COPY container_manager.py ./
COPY web-ui.html ./
COPY advanced-dashboard.html ./
COPY test_imports.py ./
COPY monitor_production.sh ./
COPY monitor_system.sh ./
COPY start_overnight_trading.sh ./
COPY start_production.sh ./
COPY stop_production.sh ./
COPY production_setup.sh ./

# Create logs directory
RUN mkdir -p /app/logs

# Create volume for persistent logs
VOLUME ["/app/logs"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port for health checks
EXPOSE 8080

# Default command: Run the trading bot
CMD ["python3", "trading_bot.py"]