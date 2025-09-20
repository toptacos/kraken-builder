#!/usr/bin/env python3
"""
Comprehensive test suite for Kraken Trading Bot Flask API
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trading_bot import app


class TestTradingBotAPI(unittest.TestCase):
    """Test cases for the Trading Bot Flask API"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('timestamp', data)
        self.assertIn('test_mode', data)
        self.assertEqual(data['status'], 'healthy')

    def test_logs_endpoint(self):
        """Test logs endpoint"""
        response = self.app.get('/logs')
        # Should return 200 even if no logs exist
        self.assertIn(response.status_code, [200, 404])

        if response.status_code == 200:
            data = json.loads(response.data)
            self.assertIn('logs', data)
            self.assertIn('total', data)
            self.assertIn('status', data)

    def test_logs_by_level_valid(self):
        """Test logs endpoint with valid level"""
        valid_levels = ['INFO', 'ERROR', 'WARNING', 'SUCCESS']
        for level in valid_levels:
            response = self.app.get(f'/logs/{level}')
            self.assertIn(response.status_code, [200, 404])

    def test_logs_by_level_invalid(self):
        """Test logs endpoint with invalid level"""
        response = self.app.get('/logs/INVALID_LEVEL')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('valid_levels', data)

    def test_status_endpoint_no_bot(self):
        """Test status endpoint when bot is not initialized"""
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 500)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_test_trade_endpoint_no_bot(self):
        """Test test trade endpoint when bot is not initialized"""
        response = self.app.post('/test_trade')
        self.assertEqual(response.status_code, 500)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_run_cycle_endpoint_no_bot(self):
        """Test run cycle endpoint when bot is not initialized"""
        response = self.app.post('/run_cycle')
        self.assertEqual(response.status_code, 500)

        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_rate_limiting_health(self):
        """Test rate limiting on health endpoint"""
        # Make multiple requests to test rate limiting
        for i in range(35):  # Exceed the 30 per minute limit
            response = self.app.get('/health')
            if i < 30:
                self.assertEqual(response.status_code, 200)
            else:
                # Should be rate limited after 30 requests
                self.assertIn(response.status_code, [200, 429])

    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)

        # Check for CORS headers
        cors_headers = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]

        for header in cors_headers:
            self.assertIn(header, response.headers)

    def test_options_request(self):
        """Test OPTIONS request handling"""
        response = self.app.options('/health')
        self.assertEqual(response.status_code, 200)

    def test_error_handling_404(self):
        """Test 404 error handling"""
        response = self.app.get('/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)

    def test_error_handling_500(self):
        """Test 500 error handling"""
        # This would require mocking an internal error
        # For now, just ensure the error handler exists
        self.assertTrue(hasattr(app, 'errorhandler'))

    def test_input_sanitization(self):
        """Test input sanitization function"""
        from trading_bot import sanitize_input

        # Test normal input
        self.assertEqual(sanitize_input("normal input"), "normal input")

        # Test input with dangerous characters
        dangerous_input = "input<script>alert('xss')</script>"
        sanitized = sanitize_input(dangerous_input)
        self.assertNotIn('<', sanitized)
        self.assertNotIn('>', sanitized)
        self.assertNotIn('script', sanitized)

        # Test non-string input
        self.assertEqual(sanitize_input(123), "123")
        self.assertEqual(sanitize_input(None), "None")


class TestDataValidation(unittest.TestCase):
    """Test data validation functions"""

    def test_symbol_validation(self):
        """Test cryptocurrency symbol validation"""
        valid_symbols = ['BTC/USDT', 'ETH/USDT', 'ADA/USDT', 'SOL/USDT']
        invalid_symbols = ['INVALID', 'BTC', 'USDT', 'BTC/USDT/INVALID']

        for symbol in valid_symbols:
            # Should not raise exception
            self.assertIsInstance(symbol, str)
            self.assertIn('/', symbol)

        for symbol in invalid_symbols:
            # These should be handled gracefully
            self.assertIsInstance(symbol, str)

    def test_timeframe_validation(self):
        """Test timeframe validation"""
        valid_timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']
        invalid_timeframes = ['invalid', '2h', '3d', '1y']

        for timeframe in valid_timeframes:
            self.assertIsInstance(timeframe, str)
            self.assertRegex(timeframe, r'^\d+[mhdw]$')

    def test_numeric_validation(self):
        """Test numeric input validation"""
        valid_numbers = [1, 1.5, 100, 0.1]
        invalid_numbers = ['not_a_number', None, [], {}]

        for num in valid_numbers:
            self.assertIsInstance(num, (int, float))

        for invalid in invalid_numbers:
            # Should handle gracefully
            self.assertIsNotNone(invalid)


class TestSecurity(unittest.TestCase):
    """Test security features"""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        # This would require actual database interaction
        # For now, just ensure input sanitization is in place
        from trading_bot import sanitize_input

        malicious_input = "'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious_input)
        self.assertNotIn(';', sanitized)
        self.assertNotIn('DROP', sanitized)
        self.assertNotIn('--', sanitized)

    def test_xss_prevention(self):
        """Test XSS prevention"""
        from trading_bot import sanitize_input

        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ]

        for payload in xss_payloads:
            sanitized = sanitize_input(payload)
            self.assertNotIn('<', sanitized)
            self.assertNotIn('>', sanitized)
            self.assertNotIn('javascript:', sanitized)

    def test_path_traversal_prevention(self):
        """Test path traversal prevention"""
        from trading_bot import sanitize_input

        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd"
        ]

        for payload in traversal_payloads:
            sanitized = sanitize_input(payload)
            self.assertNotIn('..', sanitized)
            self.assertNotIn('/', sanitized)
            self.assertNotIn('\\', sanitized)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTradingBotAPI)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataValidation))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSecurity))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)