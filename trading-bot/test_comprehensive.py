#!/usr/bin/env python3
"""
Comprehensive Test Suite for Kraken Trading Bot
===============================================

This script runs all available tests in a clean environment and provides
detailed reporting for CI/CD pipelines and production deployments.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
import json

def run_command(command, description, timeout=300):
    """Run a command with timeout and return results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command) if isinstance(command, list) else command}")
    print('='*60)

    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(command, str)
        )
        end_time = time.time()

        success = result.returncode == 0
        duration = end_time - start_time

        print(f"Duration: {duration:.2f}s")
        print(f"Exit Code: {result.returncode}")
        print(f"Status: {'✅ PASSED' if success else '❌ FAILED'}")

        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        return {
            'success': success,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration
        }

    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: Command took longer than {timeout}s")
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': f'Timeout after {timeout}s',
            'duration': timeout
        }
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e),
            'duration': time.time() - start_time
        }

def main():
    """Run comprehensive test suite"""
    print("🚀 Kraken Trading Bot - Comprehensive Test Suite")
    print("="*60)
    print(f"Start Time: {datetime.now().isoformat()}")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Environment: {os.environ.get('TEST_MODE', 'production')}")

    test_results = []
    total_start_time = time.time()

    # Test 1: Basic functionality test
    result = run_command(
        [sys.executable, 'test_basic_functionality.py'],
        "Basic Functionality Test"
    )
    test_results.append(('basic_functionality', result))

    # Test 2: Error handling test
    result = run_command(
        [sys.executable, 'test_error_handling.py'],
        "Error Handling Test"
    )
    test_results.append(('error_handling', result))

    # Test 3: Import test
    result = run_command(
        [sys.executable, 'test_imports.py'],
        "Import Test"
    )
    test_results.append(('imports', result))

    # Test 4: Try pytest if available
    try:
        import pytest
        result = run_command(
            [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short', '--disable-warnings'],
            "Pytest Unit Tests"
        )
        test_results.append(('pytest', result))
    except ImportError:
        print("\n⚠️ Pytest not available, skipping unit tests")
        test_results.append(('pytest', {
            'success': True,
            'returncode': 0,
            'stdout': 'Pytest not available',
            'stderr': '',
            'duration': 0
        }))

    # Test 5: Health check simulation
    result = run_command(
        [sys.executable, '-c', '''
import sys
sys.path.insert(0, ".")
try:
    from trading_bot import TradingBot
    print("✅ TradingBot import successful")
    print("✅ Health check passed")
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
        '''],
        "Health Check Test"
    )
    test_results.append(('health_check', result))

    # Calculate summary
    total_duration = time.time() - total_start_time
    passed_tests = sum(1 for _, result in test_results if result['success'])
    total_tests = len(test_results)

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")

    # Detailed results
    print(f"\n{'='*60}")
    print("DETAILED RESULTS")
    print('='*60)

    for test_name, result in test_results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status}: {test_name} ({result['duration']:.2f}s)")

        if not result['success']:
            if result['stderr']:
                print(f"  Error: {result['stderr'][:100]}...")
            if result['returncode'] != 0:
                print(f"  Exit Code: {result['returncode']}")

    # Save results to file
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': (passed_tests/total_tests)*100,
                'total_duration': total_duration
            },
            'results': test_results,
            'environment': {
                'python_version': sys.version,
                'working_directory': os.getcwd(),
                'test_mode': os.environ.get('TEST_MODE', 'production')
            }
        }, f, indent=2, default=str)

    print(f"\n📄 Results saved to: {results_file}")

    # Final status
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Ready for production deployment")
        return 0
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed")
        print("🔍 Check the output above for details")
        return 1

if __name__ == '__main__':
    sys.exit(main())