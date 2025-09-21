#!/bin/bash

# Setup Cron Job for Automated Trading
# ====================================
#
# This script sets up a cron job to run automated trading every minute
# when auto-trading is enabled in production mode.

set -e

echo "⏰ Setting up automated trading cron job..."

# Check if we're running in Docker
if [ -d "/app" ]; then
    WORKDIR="/app"
    LOGFILE="/app/logs/auto_trader.log"
    SCRIPT="/app/auto_trader.py"
else
    WORKDIR="$(pwd)"
    LOGFILE="$(pwd)/logs/auto_trader.log"
    SCRIPT="$(pwd)/auto_trader.py"
fi

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOGFILE")"

# Cron job command
# Run every minute, but only if auto-trading is enabled
CRON_COMMAND="* * * * * cd $WORKDIR && /usr/local/bin/python3 $SCRIPT >> $LOGFILE 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "auto_trader.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "auto_trader.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job set up successfully!"
echo "📋 Cron command: $CRON_COMMAND"
echo "📄 Logs will be written to: $LOGFILE"
echo ""
echo "🔍 To check cron jobs: crontab -l"
echo "🛑 To stop auto-trading: crontab -r"
echo ""
echo "⚠️  Remember: Auto-trading only runs when:"
echo "   - AUTO_TRADING_ENABLED=true"
echo "   - TRADING_MODE=production"
echo "   - The trading bot is healthy"