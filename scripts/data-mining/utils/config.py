#!/usr/bin/env python3
"""
Configuration utility for data mining operations.
Provides a standardized way to manage configuration for all data mining scripts.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# Add parent directory to path for relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the logger module using proper Python import syntax
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Default configuration directory
DEFAULT_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), 'config')

class ConfigManager:
    """Configuration manager for data mining operations."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir (str, optional): Path to configuration directory
        """
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_data = {}
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default configuration."""
        default_config_file = os.path.join(self.config_dir, 'data_mining.yaml')
        if os.path.exists(default_config_file):
            logger.info(f"Loading default configuration from {default_config_file}")
            with open(default_config_file, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Default configuration file not found: {default_config_file}")
            self.config_data = {}
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        
        Args:
            config_file (str): Path to configuration file
            
        Returns:
            Dict[str, Any]: Configuration data
        """
        if not os.path.exists(config_file):
            logger.error(f"Configuration file not found: {config_file}")
            return {}
        
        logger.info(f"Loading configuration from {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    config_data = json.load(f)
                elif config_file.endswith(('.yaml', '.yml')):
                    config_data = yaml.safe_load(f)
                else:
                    logger.error(f"Unsupported configuration file format: {config_file}")
                    return {}
                
                # Merge with default configuration
                self._merge_config(config_data)
                return self.config_data
                
        except Exception as e:
            logger.error(f"Error loading configuration from {config_file}: {e}")
            return {}
    
    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """
        Merge configuration data with existing configuration.
        
        Args:
            config_data (Dict[str, Any]): Configuration data to merge
        """
        def _merge_dict(source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    _merge_dict(value, target[key])
                else:
                    target[key] = value
            return target
        
        self.config_data = _merge_dict(config_data, self.config_data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key (str): Configuration key (dot notation for nested keys)
            default (Any, optional): Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        keys = key.split('.')
        current = self.config_data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key (str): Configuration key (dot notation for nested keys)
            value (Any): Configuration value
        """
        keys = key.split('.')
        current = self.config_data
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            
            if not isinstance(current[k], dict):
                current[k] = {}
            
            current = current[k]
        
        current[keys[-1]] = value
    
    def save(self, config_file: Optional[str] = None) -> bool:
        """
        Save configuration to file.
        
        Args:
            config_file (str, optional): Path to configuration file
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        if not config_file:
            config_file = os.path.join(self.config_dir, 'data_mining.yaml')
        
        logger.info(f"Saving configuration to {config_file}")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            with open(config_file, 'w') as f:
                if config_file.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                elif config_file.endswith(('.yaml', '.yml')):
                    yaml.dump(self.config_data, f, default_flow_style=False)
                else:
                    logger.error(f"Unsupported configuration file format: {config_file}")
                    return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration to {config_file}: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration data.
        
        Returns:
            Dict[str, Any]: Configuration data
        """
        return self.config_data

# Create singleton instance
config_manager = ConfigManager()

# Module-level functions for convenience
def get_config() -> ConfigManager:
    """
    Get configuration manager instance.
    
    Returns:
        ConfigManager: Configuration manager instance
    """
    return config_manager

def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration data
    """
    return config_manager.load_config(config_file)

def get(key: str, default: Any = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key (str): Configuration key (dot notation for nested keys)
        default (Any, optional): Default value if key not found
        
    Returns:
        Any: Configuration value
    """
    return config_manager.get(key, default)

def set(key: str, value: Any) -> None:
    """
    Set configuration value.
    
    Args:
        key (str): Configuration key (dot notation for nested keys)
        value (Any): Configuration value
    """
    config_manager.set(key, value)

def save(config_file: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config_file (str, optional): Path to configuration file
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    return config_manager.save(config_file)

if __name__ == "__main__":
    # Test configuration manager
    config = get_config()
    print(f"Default config: {config.get_all()}")
    
    # Set some values
    set('general.environment', 'test')
    set('sources.fec.api_key', 'test_api_key')
    
    # Get values
    print(f"Environment: {get('general.environment')}")
    print(f"FEC API Key: {get('sources.fec.api_key')}")
    
    # Save configuration
    save() 