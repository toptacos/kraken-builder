#!/usr/bin/env python3
"""
Automated Setup Utility for Trading Bot
=======================================

This utility provides a one-command setup solution for the entire trading system,
eliminating manual configuration steps and ensuring consistent deployment.

Features:
- Automated dependency installation
- Environment configuration
- Docker setup validation
- System health checks
- One-command deployment
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import platform

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import get_logger, config, APIResponse

logger = get_logger('Setup')

class SetupManager:
    """Comprehensive setup manager for the trading system"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.required_files = [
            'trading_bot.py',
            'overnight_trader.py',
            'crypto_trend_analyzer.py',
            'trading_strategies.py',
            'backtesting_engine.py',
            'web-ui.html',
            'advanced-dashboard.html',
            'Dockerfile',
            'docker-compose.yml',
            'requirements.txt',
            '.env'
        ]

    def run_full_setup(self) -> bool:
        """Run complete setup process"""
        logger.info("🚀 Starting complete trading bot setup...")

        steps = [
            ("Checking system requirements", self.check_system_requirements),
            ("Validating project files", self.validate_project_files),
            ("Installing Python dependencies", self.install_dependencies),
            ("Configuring environment", self.configure_environment),
            ("Setting up Docker", self.setup_docker),
            ("Validating configuration", self.validate_configuration),
            ("Running health checks", self.run_health_checks)
        ]

        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            try:
                if not step_func():
                    logger.error(f"❌ {step_name} failed")
                    return False
                logger.info(f"✅ {step_name} completed")
            except Exception as e:
                logger.error(f"❌ {step_name} failed with error: {e}")
                return False

        logger.info("🎉 Setup completed successfully!")
        self.print_success_message()
        return True

    def check_system_requirements(self) -> bool:
        """Check if system meets requirements"""
        logger.info("🔍 Checking system requirements...")

        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")

        # Check OS
        system = platform.system().lower()
        if system not in ['linux', 'darwin', 'windows']:
            logger.warning(f"⚠️ Unsupported OS: {system}, proceeding anyway...")

        # Check for required commands
        required_commands = ['docker', 'docker-compose']
        missing_commands = []

        for cmd in required_commands:
            if not self._command_exists(cmd):
                missing_commands.append(cmd)

        if missing_commands:
            logger.error(f"❌ Missing required commands: {', '.join(missing_commands)}")
            logger.error("Please install Docker and Docker Compose first")
            return False

        logger.info("✅ Docker and Docker Compose detected")
        return True

    def validate_project_files(self) -> bool:
        """Validate that all required project files exist"""
        logger.info("📁 Validating project files...")

        missing_files = []
        for file in self.required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)

        if missing_files:
            logger.error(f"❌ Missing required files: {', '.join(missing_files)}")
            return False

        logger.info(f"✅ All {len(self.required_files)} required files found")
        return True

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        logger.info("📦 Installing Python dependencies...")

        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            logger.error("❌ requirements.txt not found")
            return False

        try:
            # Use pip to install requirements
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode != 0:
                logger.error(f"❌ pip install failed: {result.stderr}")
                return False

            logger.info("✅ Python dependencies installed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to install dependencies: {e}")
            return False

    def configure_environment(self) -> bool:
        """Configure environment variables and settings"""
        logger.info("⚙️ Configuring environment...")

        env_file = self.project_root / '.env'
        if not env_file.exists():
            logger.warning("⚠️ .env file not found, creating template...")
            if not self._create_env_template():
                return False

        # Validate .env file has required variables
        if not self._validate_env_file():
            return False

        logger.info("✅ Environment configuration completed")
        return True

    def setup_docker(self) -> bool:
        """Setup and validate Docker configuration"""
        logger.info("🐳 Setting up Docker...")

        try:
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ Docker daemon is not running")
                logger.error("Please start Docker Desktop or Docker service")
                return False

            # Build Docker image
            logger.info("🏗️ Building Docker image...")
            result = subprocess.run([
                'docker-compose', 'build', '--no-cache'
            ], capture_output=True, text=True, cwd=self.project_root)

            if result.returncode != 0:
                logger.error(f"❌ Docker build failed: {result.stderr}")
                return False

            logger.info("✅ Docker setup completed")
            return True

        except Exception as e:
            logger.error(f"❌ Docker setup failed: {e}")
            return False

    def validate_configuration(self) -> bool:
        """Validate the complete configuration"""
        logger.info("🔍 Validating configuration...")

        # Test configuration loading
        try:
            from utils.helpers import config
            logger.info(f"✅ Configuration loaded: LOG_LEVEL={config.get('LOG_LEVEL')}")
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False

        # Test imports
        try:
            import trading_bot
            import overnight_trader
            import crypto_trend_analyzer
            logger.info("✅ All main modules import successfully")
        except Exception as e:
            logger.error(f"❌ Module import failed: {e}")
            return False

        return True

    def run_health_checks(self) -> bool:
        """Run comprehensive health checks"""
        logger.info("🏥 Running health checks...")

        # Test basic functionality
        try:
            from crypto_trend_analyzer import CryptoTrendAnalyzer
            analyzer = CryptoTrendAnalyzer()
            logger.info("✅ Trend analyzer initializes successfully")
        except Exception as e:
            logger.error(f"❌ Trend analyzer test failed: {e}")
            return False

        return True

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists on the system"""
        try:
            subprocess.run([command, '--version'],
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _create_env_template(self) -> bool:
        """Create a template .env file"""
        template_content = """# Trading Bot Configuration
TEST_MODE=false
PRODUCTION_MODE=true
VERBOSE_LOGGING=true
LOG_LEVEL=DEBUG

# Trading Parameters
STARTING_BALANCE=1000
TRADE_AMOUNT=25
DAILY_PROFIT_TARGET=50
DAILY_LOSS_LIMIT=-100
MIN_ARB_PROFIT_PCT=0.5
MAX_TRADES_PER_HOUR=12

# API Keys (Configure these with your exchange API keys)
# BINANCE_API_KEY=your_binance_api_key
# BINANCE_API_SECRET=your_binance_api_secret
# KRAKEN_API_KEY=your_kraken_api_key
# KRAKEN_API_SECRET=your_kraken_api_secret
COINBASE_API_KEY_NAME=your_coinbase_key_name
COINBASE_API_PRIVATE_KEY=your_coinbase_private_key
# KUCOIN_API_KEY=your_kucoin_api_key
# KUCOIN_API_SECRET=your_kucoin_api_secret
# KUCOIN_API_PASSPHRASE=your_kucoin_passphrase

# Optional API Keys for Enhanced Analysis
# COINMARKETCAP_API_KEY=your_cmc_api_key
# LUNARCRUSH_API_KEY=your_lunarcrush_api_key

# Database Configuration (Optional)
# POSTGRES_PASSWORD=your_postgres_password
"""

        try:
            env_file = self.project_root / '.env'
            with open(env_file, 'w') as f:
                f.write(template_content)
            logger.info("✅ Created .env template file")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create .env template: {e}")
            return False

    def _validate_env_file(self) -> bool:
        """Validate .env file has required configuration"""
        env_file = self.project_root / '.env'
        if not env_file.exists():
            logger.error("❌ .env file not found")
            return False

        required_vars = ['TEST_MODE', 'STARTING_BALANCE', 'TRADE_AMOUNT']
        missing_vars = []

        with open(env_file, 'r') as f:
            content = f.read()

        for var in required_vars:
            if var not in content:
                missing_vars.append(var)

        if missing_vars:
            logger.warning(f"⚠️ Missing recommended variables: {', '.join(missing_vars)}")
            logger.warning("Using default values for missing variables")

        logger.info("✅ Environment file validation completed")
        return True

    def print_success_message(self):
        """Print success message with next steps"""
        print("\n" + "="*60)
        print("🎉 TRADING BOT SETUP COMPLETED SUCCESSFULLY!")
        print("="*60)
        print()
        print("🚀 Quick Start Commands:")
        print("  ./start_overnight_trading.sh     # Start production system")
        print("  docker-compose logs -f           # Monitor logs")
        print("  open web-ui.html                 # Open dashboard")
        print()
        print("📊 Access Points:")
        print("  Dashboard: http://localhost:8080/health")
        print("  API: http://localhost:8080/logs")
        print("  Overnight: http://localhost:8081/overnight/status")
        print()
        print("⚙️ Configuration:")
        print("  Edit .env file to configure API keys")
        print("  Modify trading parameters as needed")
        print("  Enable/disable exchanges in configuration")
        print()
        print("📈 Features Enabled:")
        print("  ✅ 1-minute trading cycles")
        print("  ✅ Multi-source trend analysis")
        print("  ✅ Verbose logging")
        print("  ✅ Production monitoring")
        print("  ✅ Real-time dashboard")
        print()
        print("Happy Trading! 📊💰🚀")
        print("="*60)

def main():
    """Main setup function"""
    print("🐙 Kraken Trading Bot - Automated Setup")
    print("=" * 50)

    setup_manager = SetupManager()

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: python utils/setup.py")
        print("This will run the complete automated setup for the trading bot")
        return

    success = setup_manager.run_full_setup()

    if not success:
        print("\n❌ Setup failed! Please check the logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()