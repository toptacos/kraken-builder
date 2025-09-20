#!/bin/bash
# Stop production trading bot gracefully

echo "🛑 Stopping production trading bot..."

# Stop monitoring
if [ -f "monitor_pid.txt" ]; then
    MONITOR_PID=$(cat monitor_pid.txt)
    kill $MONITOR_PID 2>/dev/null || true
    rm -f monitor_pid.txt
    echo "📊 Monitoring stopped"
fi

# Stop trading bot
if [ -f "bot_pid.txt" ]; then
    BOT_PID=$(cat bot_pid.txt)
    kill $BOT_PID 2>/dev/null || true
    rm -f bot_pid.txt
    echo "🤖 Trading bot stopped"
fi

# Kill any remaining processes
pkill -f "python3 trading_bot.py" 2>/dev/null || true
pkill -f "monitor_production.sh" 2>/dev/null || true

echo "✅ Production system stopped gracefully"
