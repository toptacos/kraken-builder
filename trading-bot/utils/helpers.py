#!/usr/bin/env python3
"""
Modular Helper Utilities for Trading Bot
========================================

This module provides reusable utilities to eliminate code repetition and
improve maintainability across the trading system.

Features:
- Centralized logging configuration
- Standardized API request handling
- Configuration management
- Error handling utilities
- Response formatting helpers
- Validation utilities
"""

import os
import json
import logging
import requests
import functools
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass
import time

# Configuration Constants
DEFAULT_CONFIG = {
    'LOG_LEVEL': 'INFO',
    'LOG_FORMAT': '%(asctime)s - [%(levelname)s] - %(name)s - %(funcName)s:%(lineno)d - %(message)s',
    'REQUEST_TIMEOUT': 10,
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 1,
    'CACHE_TTL': 300,  # 5 minutes
}

@dataclass
class APIResponse:
    """Standardized API response structure"""
    success: bool
    data: Any = None
    error: str = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'success': self.success,
            'timestamp': datetime.now().isoformat()
        }
        if self.data is not None:
            result['data'] = self.data
        if self.error:
            result['error'] = self.error
        if self.metadata:
            result['metadata'] = self.metadata
        return result

class Logger:
    """Centralized logging configuration"""

    _instances = {}

    def __init__(self, name: str, level: str = None):
        self.name = name
        self.level = level or os.getenv('LOG_LEVEL', DEFAULT_CONFIG['LOG_LEVEL'])
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with consistent configuration"""
        if self.name in self._instances:
            return self._instances[self.name]

        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, self.level.upper()))

        # Remove existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.level.upper()))

        # Create formatter
        formatter = logging.Formatter(DEFAULT_CONFIG['LOG_FORMAT'])
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

        # Store instance
        self._instances[self.name] = logger
        return logger

    def get_logger(self) -> logging.Logger:
        """Get configured logger instance"""
        return self.logger

def get_logger(name: str, level: str = None) -> logging.Logger:
    """Get a configured logger instance"""
    logger_instance = Logger(name, level)
    return logger_instance.get_logger()

class ConfigManager:
    """Centralized configuration management"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from environment and defaults"""
        self.config = DEFAULT_CONFIG.copy()

        # Override with environment variables
        for key in self.config.keys():
            env_value = os.getenv(key)
            if env_value is not None:
                # Convert string values to appropriate types
                if key in ['REQUEST_TIMEOUT', 'MAX_RETRIES', 'RETRY_DELAY', 'CACHE_TTL']:
                    self.config[key] = int(env_value)
                elif key in ['LOG_LEVEL']:
                    self.config[key] = env_value.upper()
                else:
                    self.config[key] = env_value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value

# Global config instance
config = ConfigManager()

class APIClient:
    """Standardized API client with retry logic and error handling"""

    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url
        self.timeout = timeout or config.get('REQUEST_TIMEOUT')
        self.max_retries = config.get('MAX_RETRIES')
        self.retry_delay = config.get('RETRY_DELAY')
        self.logger = get_logger('APIClient')

    def request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint

        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"📡 {method.upper()} {url}")

                start_time = time.time()
                response = requests.request(method, url, timeout=self.timeout, **kwargs)
                response_time = time.time() - start_time

                self.logger.debug(f"📊 Response: {response.status_code} ({response_time:.3f}s)")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        return APIResponse(
                            success=True,
                            data=data,
                            metadata={'response_time': response_time, 'status_code': response.status_code}
                        )
                    except json.JSONDecodeError:
                        return APIResponse(
                            success=True,
                            data=response.text,
                            metadata={'response_time': response_time, 'status_code': response.status_code}
                        )
                else:
                    if attempt < self.max_retries - 1:
                        self.logger.warning(f"⚠️ Request failed ({response.status_code}), retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return APIResponse(
                            success=False,
                            error=f"HTTP {response.status_code}: {response.text}",
                            metadata={'response_time': response_time, 'status_code': response.status_code}
                        )

            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"⚠️ Request error: {e}, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return APIResponse(
                        success=False,
                        error=str(e),
                        metadata={'attempts': attempt + 1}
                    )

        return APIResponse(success=False, error="Max retries exceeded")

    def get(self, endpoint: str, **kwargs) -> APIResponse:
        """GET request"""
        return self.request('GET', endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> APIResponse:
        """POST request"""
        return self.request('POST', endpoint, **kwargs)

class CacheManager:
    """Simple file-based cache manager"""

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.logger = get_logger('CacheManager')
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for key"""
        return os.path.join(self.cache_dir, f"{key.replace('/', '_')}.json")

    def get(self, key: str) -> Optional[Any]:
        """Get cached data if valid"""
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cached_time = datetime.fromisoformat(cache_data['timestamp'])
            ttl = config.get('CACHE_TTL', 300)

            if (datetime.now() - cached_time).seconds < ttl:
                self.logger.debug(f"📋 Cache hit for {key}")
                return cache_data['data']
            else:
                self.logger.debug(f"📋 Cache expired for {key}")
                return None

        except Exception as e:
            self.logger.debug(f"📋 Cache read error for {key}: {e}")
            return None

    def set(self, key: str, data: Any):
        """Cache data"""
        cache_path = self._get_cache_path(key)

        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)

            self.logger.debug(f"💾 Cached data for {key}")

        except Exception as e:
            self.logger.error(f"❌ Cache write error for {key}: {e}")

class ValidationUtils:
    """Utility functions for data validation"""

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """Validate cryptocurrency symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        # Should be 2-10 uppercase letters
        return bool(re.match(r'^[A-Z]{2,10}$', symbol))

    @staticmethod
    def validate_price(price: Union[int, float]) -> bool:
        """Validate price value"""
        try:
            price_float = float(price)
            return price_float > 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_percentage(value: Union[int, float]) -> bool:
        """Validate percentage value (0-100)"""
        try:
            val_float = float(value)
            return 0 <= val_float <= 100
        except (ValueError, TypeError):
            return False

    @staticmethod
    def sanitize_string(text: str, max_length: int = 100) -> str:
        """Sanitize string input"""
        if not text:
            return ""
        return str(text).strip()[:max_length]

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator for retrying functions on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__name__)
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ All {max_attempts} attempts failed: {e}")

            raise last_exception
        return wrapper
    return decorator

def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__name__)
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"⏱️ {func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

# Global instances
api_client = APIClient()
cache_manager = CacheManager()

# Convenience functions
def make_request(method: str, url: str, **kwargs) -> APIResponse:
    """Make HTTP request using global API client"""
    return api_client.request(method, url, **kwargs)

def get_cached_data(key: str) -> Optional[Any]:
    """Get cached data"""
    return cache_manager.get(key)

def set_cached_data(key: str, data: Any):
    """Cache data"""
    cache_manager.set(key, data)

# Export commonly used functions
__all__ = [
    'get_logger',
    'config',
    'APIResponse',
    'APIClient',
    'CacheManager',
    'ValidationUtils',
    'retry_on_failure',
    'log_execution_time',
    'make_request',
    'get_cached_data',
    'set_cached_data'
]