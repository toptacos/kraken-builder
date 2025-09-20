#!/bin/bash

# Kraken Trading Bot - Virtual Environment Setup Script
# This script creates a virtual environment for safe Python package installation

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${PURPLE}[SETUP]${NC} $1"
}

# Check if virtual environment already exists
if [ -d "venv" ]; then
    print_warning "Virtual environment 'venv' already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Using existing virtual environment"
        print_status "To activate: source venv/bin/activate"
        exit 0
    fi

    print_status "Removing existing virtual environment..."
    rm -rf venv
fi

# Check Python version
print_status "Checking Python version..."
python3 --version

# Create virtual environment
print_status "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    print_status "Installing requirements..."
    pip install -r requirements.txt
else
    print_warning "requirements.txt not found - installing basic packages..."
    pip install ccxt pandas requests flask python-dotenv
fi

print_success "Virtual environment setup complete!"
echo ""
echo -e "${GREEN}To activate the virtual environment:${NC}"
echo -e "  source venv/bin/activate"
echo ""
echo -e "${GREEN}To run the trading bot:${NC}"
echo -e "  source venv/bin/activate"
echo -e "  ./start_production.sh"
echo ""
echo -e "${GREEN}To deactivate:${NC}"
echo -e "  deactivate"