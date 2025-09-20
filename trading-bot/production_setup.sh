#!/bin/bash

echo "🔧 PRODUCTION MODE SETUP FOR KRAKEN TRADING BOT"
echo "================================================"

# Step 1: Update .env file for production
echo "📝 Step 1: Configuring .env for production..."
if [ -f ".env" ]; then
    sed -i.bak 's/TEST_MODE=true/TEST_MODE=false/' .env
else
    echo "⚠️  .env file not found. Please create it with your API keys."
fi

echo "🔑 Step 2: Add your real API keys to .env file:"
echo "   Edit .env and replace the following with your real credentials:"
echo "   - BINANCE_API_KEY=your_real_binance_api_key"
echo "   - BINANCE_API_SECRET=your_real_binance_api_secret"
echo "   - KRAKEN_API_KEY=your_real_kraken_api_key"
echo "   - KRAKEN_API_SECRET=your_real_kraken_api_secret"
echo "   - KUCOIN_API_KEY=your_real_kucoin_api_key"
echo "   - KUCOIN_API_SECRET=your_real_kucoin_api_secret"
echo "   - KUCOIN_API_PASSPHRASE=your_real_kucoin_passphrase"

# Step 2: Stop current container
echo "🛑 Step 3: Stopping current test container..."
docker-compose down

# Step 3: Rebuild and start in production mode with retry
echo "🚀 Step 4: Starting production container..."
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    docker-compose up -d kraken-trading-bot && break
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "⚠️  Attempt $RETRY_COUNT failed. Retrying in 10 seconds..."
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Failed to start after $MAX_RETRIES attempts. Please check Docker daemon."
    exit 1
fi

# Step 4: Verify production setup
echo "✅ Step 5: Verifying production setup..."
sleep 5
curl -s http://localhost:8080/health | jq '.test_mode'

echo ""
echo "🎯 PRODUCTION BOT IS NOW RUNNING!"
echo "=================================="
echo "📊 Dashboard: http://localhost:8080/health"
echo "📋 Logs: http://localhost:8080/logs"
echo "💰 Portfolio: http://localhost:8080/portfolio"
echo "📈 Signals: http://localhost:8080/signals"
echo ""
echo "⚠️  WARNING: Bot is now running with REAL MONEY!"
echo "   Monitor closely and ensure proper risk management."
