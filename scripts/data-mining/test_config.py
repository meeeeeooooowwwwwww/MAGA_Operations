#!/usr/bin/env python3
"""
Test script for configuration system.

This script verifies that the configuration manager is working correctly
by loading the default configuration and displaying its contents.
"""
import os
import sys
import json
import yaml
from pprint import pprint

# Add project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import configuration manager
from scripts.utils.config import get_config, get, set, load_config, save

def print_config(title, config):
    """Print configuration in a formatted way."""
    print(f"\n{title}:")
    
    # Convert to JSON for pretty printing
    print(json.dumps(config, indent=2))
    print()

def main():
    """Test configuration manager functionality."""
    print("Testing configuration manager...\n")
    
    # Get configuration manager
    config = get_config()
    
    # Display default configuration
    print_config("Default configuration", config.get_all())
    
    # Test getting values
    print("Testing get() function:")
    print(f"  FEC API Key: {get('sources.fec.api_key')}")
    print(f"  Debug Mode: {get('general.debug')}")
    print(f"  Non-existent key with default: {get('does.not.exist', 'default_value')}")
    
    # Test setting values
    print("\nTesting set() function:")
    set('sources.fec.api_key', 'test_api_key')
    set('new.nested.key', 'new_nested_value')
    
    # Display updated configuration
    print_config("Updated configuration", config.get_all())
    
    # Test environment variable override
    print("Testing environment variable override:")
    os.environ['MAGA_SOURCES_FEC_API_KEY'] = 'env_var_api_key'
    
    # Reload configuration
    config.load()
    
    # Display overridden configuration
    print_config("Configuration after env var override", config.get_all())
    
    # Save test configuration to temporary file
    test_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_config.yaml')
    if save(test_config_file):
        print(f"Saved test configuration to {test_config_file}")
    
    # Cleanup
    if os.path.exists(test_config_file):
        os.remove(test_config_file)
        print(f"Removed test configuration file")

if __name__ == "__main__":
    main() 