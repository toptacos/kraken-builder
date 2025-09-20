#!/usr/bin/env python3
"""
Test script to check imports and basic functionality
"""

import sys
import os

print("=== Testing Imports ===")

try:
    import ccxt
    print("✅ ccxt imported successfully")
except ImportError as e:
    print(f"❌ ccxt import failed: {e}")

try:
    import pandas as pd
    print("✅ pandas imported successfully")
except ImportError as e:
    print(f"❌ pandas import failed: {e}")

try:
    import requests
    print("✅ requests imported successfully")
except ImportError as e:
    print(f"❌ requests import failed: {e}")

try:
    import numpy as np
    print("✅ numpy imported successfully")
except ImportError as e:
    print(f"❌ numpy import failed: {e}")

try:
    from flask import Flask
    print("✅ flask imported successfully")
except ImportError as e:
    print(f"❌ flask import failed: {e}")

try:
    from flask_cors import CORS
    print("✅ flask-cors imported successfully")
except ImportError as e:
    print(f"❌ flask-cors import failed: {e}")

try:
    from flask_limiter import Limiter
    print("✅ flask-limiter imported successfully")
except ImportError as e:
    print(f"❌ flask-limiter import failed: {e}")

try:
    import psutil
    print("✅ psutil imported successfully")
except ImportError as e:
    print(f"❌ psutil import failed: {e}")

print("\n=== Testing Environment Variables ===")
print(f"TEST_MODE: {os.getenv('TEST_MODE', 'not set')}")
print(f"COINBASE_API_KEY_NAME: {os.getenv('COINBASE_API_KEY_NAME', 'not set')[:50]}...")
print(f"COINBASE_API_PRIVATE_KEY length: {len(os.getenv('COINBASE_API_PRIVATE_KEY', ''))}")

print("\n=== Testing TradingBot Import ===")
try:
    from trading_bot import TradingBot
    print("✅ TradingBot imported successfully")
except ImportError as e:
    print(f"❌ TradingBot import failed: {e}")
except Exception as e:
    print(f"❌ TradingBot import error: {e}")

print("\n=== Test Complete ===")