#!/usr/bin/env python3
"""
Setup script for entity classification environment.

This script:
1. Checks and installs required Python packages
2. Creates necessary directories
3. Sets up API keys in .env file
4. Initializes the database schema
"""
import os
import sys
import subprocess
import sqlite3
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
ENV_FILE = os.path.join(PROJECT_ROOT, '.env')
DB_PATH = os.path.join(PROJECT_ROOT, 'maga_ops.db')

# Required packages for entity classification
REQUIRED_PACKAGES = [
    'requests',
    'python-dotenv',
    'pandas',
    'colorama',
    'tqdm'
]

def check_python_version():
    """Check if Python version is 3.7+"""
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 7):
        logger.error(f"Python 3.7+ required, but {major}.{minor} found. Please upgrade Python.")
        sys.exit(1)
    else:
        logger.info(f"Python version {major}.{minor} OK")

def install_required_packages():
    """Install required Python packages if they're not already installed"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        logger.info("Pip upgraded successfully")
        
        # Check which packages need to be installed
        to_install = []
        for package in REQUIRED_PACKAGES:
            try:
                __import__(package.split('==')[0])
                logger.info(f"Package {package} already installed")
            except ImportError:
                to_install.append(package)
        
        if to_install:
            logger.info(f"Installing packages: {', '.join(to_install)}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + to_install)
            logger.info("All required packages installed successfully")
        else:
            logger.info("All required packages already installed")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install packages: {str(e)}")
        sys.exit(1)

def create_directories():
    """Create necessary directories if they don't exist"""
    for directory in [DATA_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def setup_env_file():
    """Set up .env file with required API keys"""
    if os.path.exists(ENV_FILE):
        logger.info(f".env file already exists at {ENV_FILE}")
        return
    
    logger.info("Creating .env file for API keys")
    
    # Default template for .env file
    env_template = """# API Keys for Entity Classification
# Required for web search and AI classification

# Google Search API (https://serper.dev/)
SERPER_API_KEY=your_serper_api_key_here

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here
"""
    
    try:
        with open(ENV_FILE, 'w') as f:
            f.write(env_template)
        logger.info(f".env file created at {ENV_FILE}")
        logger.info("Please edit this file to add your actual API keys before running the classifier")
    except Exception as e:
        logger.error(f"Failed to create .env file: {str(e)}")

def initialize_database():
    """Initialize the database with entity schema"""
    try:
        # Import here to ensure path is set up correctly
        sys.path.append(PROJECT_ROOT)
        
        from scripts.db.entity_schema import init_database
        init_database()
        logger.info(f"Database initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        if "No module named" in str(e):
            logger.error("Make sure the entity_schema.py file is in the scripts/db/ directory")

def print_next_steps():
    """Print information about next steps"""
    print("\n" + "="*80)
    print("ENTITY CLASSIFICATION ENVIRONMENT SETUP COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Edit the .env file and add your API keys for:")
    print("   - Serper.dev (Google Search API)")
    print("   - OpenAI API")
    print("\n2. Run the AI classification script:")
    print("   python scripts/ai_classify_entities.py")
    print("\n3. View the results in:")
    print(f"   - JSON file: {os.path.join(DATA_DIR, 'entity_classifications.json')}")
    print(f"   - Database: {DB_PATH} (table: 'entities')")
    print("\n4. For more control, you can modify the parameters in the scripts:")
    print("   - scripts/ai_classify_entities.py")
    print("   - scripts/db/entity_schema.py")
    print("="*80)

def main():
    """Main function to set up the environment"""
    print("\nSetting up environment for entity classification...\n")
    
    check_python_version()
    install_required_packages()
    create_directories()
    setup_env_file()
    initialize_database()
    print_next_steps()

if __name__ == "__main__":
    main() 