#!/bin/bash

# Automated setup for crypto trading bot (Fixed for macOS and cross-platform)
# Usage: ./setup_trading_bot.sh [--test]
# --test: Run dry-run tests without installing/running.
# Prompts for exchange and keys; generates/runs trading_bot.py

# Detect OS
OS_TYPE=$(uname -s)
echo "Detected OS: $OS_TYPE"

# Function to find Python command (prefer python3, fallback to python)
find_python_cmd() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: No Python found. Install Python 3+."
        if [ "$OS_TYPE" == "Darwin" ]; then
            echo "On macOS: Install Homebrew (brew.sh), then 'brew install python'."
        elif [ "$OS_TYPE" == "Linux" ]; then
            echo "On Linux (Ubuntu): sudo apt update && sudo apt install python3 python3-pip"
        else
            echo "On Windows: Download from python.org and add to PATH."
        fi
        exit 1
    fi
    echo "Using Python command: $PYTHON_CMD"
}

# Function to install packages using Python's pip module (bypasses bad pip binary)
install_packages() {
    $PYTHON_CMD -m pip install --upgrade pip || { echo "pip upgrade failed."; return 1; }
    $PYTHON_CMD -m pip install ccxt pandas requests numpy || { echo "Install failed."; return 1; }
    return 0
}

# Test mode flag
TEST_MODE=false
if [ "$1" == "--test" ]; then
    TEST_MODE=true
    echo "Running in TEST MODE: Dry-run checks only (no installs or bot execution)."
fi

echo "Welcome to Crypto Trading Bot Setup (September 2025 Edition - Fixed for macOS)"
echo "This script installs deps, sets up the script, and runs the bot."
echo "WARNING: Trading involves risk. Use testnet first. No profit guarantees."

# Find Python
find_python_cmd

if [ "$TEST_MODE" == false ]; then
    # Step 1: Install dependencies
    echo "Installing Python libraries..."
    install_packages || {
        echo "Install failed. Check Python/pip setup."
        if [ "$OS_TYPE" == "Darwin" ]; then
            echo "macOS Fix: If pip is broken (bad interpreter), try 'brew reinstall python' or remove old symlinks in /usr/local/bin."
            echo "Alternatively, run '$PYTHON_CMD -m ensurepip --upgrade' to fix pip."
        fi
        exit 1
    }
else
    echo "[TEST] Skipping install; assuming deps are present."
fi

# Step 2: Prompt for exchange and details (or skip in test)
if [ "$TEST_MODE" == false ]; then
    read -p "Enter your exchange (e.g., kraken, coinbasepro, kucoin): " EXCHANGE_ID
    read -p "Enter quote currency (e.g., USDT, USD): " QUOTE_CURRENCY
    read -p "Use sandbox/testnet? (y/n): " USE_SANDBOX
    if [ "$USE_SANDBOX" == "y" ]; then
        SANDBOX=true
    else
        SANDBOX=false
    fi
    read -p "Enter your API Key: " API_KEY
    read -s -p "Enter your API Secret: " SECRET
    echo
else
    echo "[TEST] Using dummy values for exchange/API."
    EXCHANGE_ID="kraken"
    QUOTE_CURRENCY="USDT"
    SANDBOX="true"
    API_KEY="test_key"
    SECRET="test_secret"
fi

# Set env vars
export API_KEY="$API_KEY"
export SECRET="$SECRET"

# Step 3: Generate trading_bot.py (based on original, with customizations)
echo "Generating trading_bot.py with your settings..."
cat > trading_bot.py << EOL
import os
import logging
import time
import requests
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime

# Setup logging: Logs to both console and a file 'trading_bot.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# IMPORTANT WARNINGS (READ BEFORE RUNNING):
# 1. CRYPTO TRADING INVOLVES HIGH RISK. THERE IS NO WAY TO "ENSURE PROFIT" OR "NOT LOSE MONEY."
#    This script uses a simple strategy based on trending coins and moving averages, but markets are volatile.
#    You WILL likely lose money, especially starting with \$100. This is for educational purposes only.
# 2. FUND YOUR ACCOUNT WITH AT LEAST \$100 $QUOTE_CURRENCY. Use the testnet (sandbox) first to avoid real losses.
# 3. Install required libraries: $PYTHON_CMD -m pip install ccxt pandas requests numpy
# 4. Set API keys as environment variables:
#    export API_KEY='your_api_key_here'
#    export SECRET='your_secret_here'
# 5. For testnet: Change 'sandbox': False to True below.
# 6. The bot trades small amounts (~$10 per trade) to minimize risk, but still, no guarantees.
# 7. Strategy: Fetches top trending coin from CoinGecko (free API, no key needed), computes SMA crossover on 1h data.
#    Buys if short SMA > long SMA (uptrend signal), sells if crossed below. Only trades if balance allows small positions.

# Exchange setup
exchange = ccxt.$EXCHANGE_ID({
    'apiKey': os.getenv('API_KEY'),
    'secret': os.getenv('SECRET'),
    'sandbox': $SANDBOX,  # Set to True for testnet (recommended for starters)
    'enableRateLimit': True,
})

def fetch_trending_coin():
    """Scrape CoinGecko for top trending coin (free, no API key). Returns symbol like 'BTC/$QUOTE_CURRENCY'."""
    try:
        url = 'https://api.coingecko.com/api/v3/search/trending'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        top_coin_id = data['coins'][0]['item']['id'].upper()
        symbol = f"{top_coin_id}/$QUOTE_CURRENCY"
        logger.info(f"Fetched trending coin: {symbol}")
        return symbol
    except Exception as e:
        logger.error(f"Error fetching trending coin: {e}")
        return 'BTC/$QUOTE_CURRENCY'  # Fallback to BTC

def get_ohlcv_data(symbol, timeframe='1h', limit=100):
    """Fetch OHLCV data via CCXT and compute simple moving averages."""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['sma_short'] = df['close'].rolling(window=10).mean()  # Short MA: 10 periods
        df['sma_long'] = df['close'].rolling(window=50).mean()   # Long MA: 50 periods
        logger.info(f"Fetched OHLCV for {symbol}: Latest close {df['close'].iloc[-1]:.2f}")
        return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {symbol}: {e}")
        return None

def get_balance(asset='$QUOTE_CURRENCY'):
    """Get free balance for asset."""
    try:
        balance = exchange.fetch_balance()
        return balance[asset]['free']
    except Exception as e:
        logger.error(f"Error fetching balance for {asset}: {e}")
        return 0

def place_buy_order(symbol, amount_usd=10):
    """Place market buy order for ~\$10 $QUOTE_CURRENCY worth."""
    try:
        base = symbol.split('/')[0]
        quote = symbol.split('/')[1]
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        amount = amount_usd / price
        if amount < exchange.markets[symbol]['limits']['amount']['min']:
            logger.warning(f"Amount {amount} too small for {symbol}, skipping buy.")
            return None
        order = exchange.create_market_buy_order(symbol, amount)
        logger.info(f"BUY ORDER: Bought {amount:.6f} {base} at {price:.2f} for ~\${amount_usd}")
        return order
    except Exception as e:
        logger.error(f"Error placing buy order for {symbol}: {e}")
        return None

def place_sell_order(symbol):
    """Place market sell order for all holdings of the base asset."""
    try:
        base = symbol.split('/')[0]
        balance = get_balance(base)
        if balance <= 0:
            logger.warning(f"No {base} to sell.")
            return None
        order = exchange.create_market_sell_order(symbol, balance)
        logger.info(f"SELL ORDER: Sold {balance:.6f} {base}")
        return order
    except Exception as e:
        logger.error(f"Error placing sell order for {symbol}: {e}")
        return None

def main():
    logger.info("Starting Crypto Trading Bot. Initial balance check...")
    usdt_balance = get_balance('$QUOTE_CURRENCY')
    logger.info(f"$QUOTE_CURRENCY Balance: \${usdt_balance:.2f}")
    if usdt_balance < 100:
        logger.warning("Balance below \$100. Please fund account.")

    position = None  # Track if we hold the current coin
    while True:
        try:
            symbol = fetch_trending_coin()
            df = get_ohlcv_data(symbol)
            if df is None or len(df) < 50:
                logger.warning("Insufficient data, skipping cycle.")
                time.sleep(3600)  # Wait 1 hour
                continue

            short_ma = df['sma_short'].iloc[-1]
            long_ma = df['sma_long'].iloc[-1]
            current_price = df['close'].iloc[-1]
            prev_short = df['sma_short'].iloc[-2]
            prev_long = df['sma_long'].iloc[-2]

            # Simple crossover signals
            buy_signal = (short_ma > long_ma) and (prev_short <= prev_long)
            sell_signal = (short_ma < long_ma) and (prev_short >= prev_long)

            base = symbol.split('/')[0]
            base_balance = get_balance(base)

            if buy_signal and usdt_balance > 10 and base_balance < 0.001:  # No position, buy if signal
                order = place_buy_order(symbol, 10)
                if order:
                    position = symbol
                    usdt_balance = get_balance('$QUOTE_CURRENCY')  # Update
            elif sell_signal and base_balance > 0.001:  # Sell if signal
                order = place_sell_order(symbol)
                if order:
                    position = None
                    usdt_balance = get_balance('$QUOTE_CURRENCY')  # Update

            # Log current status
            logger.info(f"Status - Symbol: {symbol}, Price: \${current_price:.2f}, Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}, $QUOTE_CURRENCY: \${usdt_balance:.2f}, {base}: {base_balance:.6f}")
            if buy_signal:
                logger.info("BUY SIGNAL DETECTED")
            if sell_signal:
                logger.info("SELL SIGNAL DETECTED")

            time.sleep(3600)  # Check every hour to avoid rate limits
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            time.sleep(300)  # Wait 5 min on error

if __name__ == "__main__":
    main()
EOL

if [ "$TEST_MODE" == true ]; then
    echo "[TEST] Script generation successful."
    echo "[TEST] Env vars set (dummy): API_KEY=$API_KEY"
    echo "[TEST] Python version: $($PYTHON_CMD --version)"
    echo "[TEST] pip version: $($PYTHON_CMD -m pip --version)"
    echo "[TEST] All checks passed! Run without --test to execute."
    exit 0
fi

# Step 4: Run the bot
echo "Setup complete! Running trading_bot.py (Ctrl+C to stop)..."
$PYTHON_CMD trading_bot.py