#!/usr/bin/env python3
"""
Test Runner for Kraken Trading Bot
==================================

This script provides an easy way to run the test suite with various options.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit            # Run only unit tests
    python run_tests.py --integration     # Run only integration tests
    python run_tests.py --coverage        # Run with coverage report
    python run_tests.py --verbose         # Run with verbose output
    python run_tests.py --quick           # Run fast tests only
"""

import os
import sys
import subprocess
import argparse


def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)

    try:
        result = subprocess.run(command, capture_output=False, text=True)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run Kraken Trading Bot tests')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quick', action='store_true', help='Run only fast tests (skip slow tests)')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')

    args = parser.parse_args()

    # Base pytest command
    cmd = [sys.executable, '-m', 'pytest']

    # Add test markers
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    elif args.api:
        cmd.extend(['-m', 'api'])
    elif args.quick:
        cmd.extend(['-m', 'not slow'])

    # Add coverage options
    if args.coverage or args.html:
        cmd.extend(['--cov=.', '--cov-report=term-missing'])
        if args.html:
            cmd.extend(['--cov-report=html'])

    # Add verbosity
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('--tb=short')

    # Run the tests
    success = run_command(cmd, "Trading Bot Test Suite")

    if success:
        print(f"\n{'='*60}")
        print("✅ All tests passed!")
        if args.coverage or args.html:
            print("Coverage report generated in htmlcov/index.html")
        print('='*60)
    else:
        print(f"\n{'='*60}")
        print("❌ Some tests failed!")
        print("Check the output above for details")
        print('='*60)
        sys.exit(1)


if __name__ == '__main__':
    # Check if we're in the right directory
    if not os.path.exists('tests'):
        print("Error: tests directory not found. Please run from the project root.")
        sys.exit(1)

    if not os.path.exists('trading_bot.py'):
        print("Error: trading_bot.py not found. Please run from the project root.")
        sys.exit(1)

    main()