#!/usr/bin/env python3
"""
Configuration Management Utility.

Provides functions for loading, accessing and manipulating configuration settings.
Supports multiple formats and hierarchical configuration values.
"""
import os
import json
import yaml
import dotenv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Default configuration paths
CONFIG_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.yaml"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config.json"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
]

# Global configuration
_config: Dict[str, Any] = {}

# Loaded flag
_loaded = False

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a file.
    
    Args:
        path (str, optional): Path to configuration file
        
    Returns:
        dict: Loaded configuration
    """
    global _config, _loaded
    
    # Load environment variables
    dotenv.load_dotenv()
    
    # Convert environment variables to configuration
    for key, value in os.environ.items():
        if key.startswith(("MAGA_", "MAGA_OPS_")):
            config_key = key.replace("MAGA_OPS_", "").replace("MAGA_", "").lower()
            set_value(config_key, parse_env_value(value))
    
    # If path is provided, load specific configuration file
    if path:
        _load_config_file(path)
    else:
        # Load all default configuration files if they exist
        for config_path in CONFIG_PATHS:
            if os.path.exists(config_path):
                _load_config_file(config_path)
    
    _loaded = True
    
    return _config

def _load_config_file(path: str) -> None:
    """
    Load configuration from a specific file.
    
    Args:
        path (str): Path to configuration file
    """
    global _config
    
    # Get file extension
    ext = os.path.splitext(path)[1].lower()
    
    # Load configuration based on file type
    try:
        if ext == ".yaml" or ext == ".yml":
            with open(path, "r") as f:
                config = yaml.safe_load(f) or {}
        elif ext == ".json":
            with open(path, "r") as f:
                config = json.load(f)
        elif ext == ".env":
            # Environment variables are already loaded
            return
        else:
            raise ValueError(f"Unsupported configuration file type: {ext}")
        
        # Merge with existing configuration
        _merge_configs(_config, config)
    except Exception as e:
        import logging
        logging.getLogger("config").warning(f"Error loading configuration from {path}: {e}")

def _merge_configs(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    """
    Merge source configuration into target configuration.
    
    Args:
        target (dict): Target configuration
        source (dict): Source configuration
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            # Recursively merge dictionaries
            _merge_configs(target[key], value)
        else:
            # Set value
            target[key] = value

def get_config() -> Dict[str, Any]:
    """
    Get entire configuration.
    
    Returns:
        dict: Configuration dictionary
    """
    global _config, _loaded
    
    # Load configuration if not already loaded
    if not _loaded:
        load_config()
    
    return _config

def get(key: str, default: Any = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key (str): Configuration key (dot notation)
        default (any, optional): Default value if key is not found
        
    Returns:
        any: Configuration value
    """
    global _config, _loaded
    
    # Load configuration if not already loaded
    if not _loaded:
        load_config()
    
    # Split key into parts
    parts = key.split(".")
    
    # Navigate through configuration
    current = _config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return default
    
    return current

def set_value(key: str, value: Any) -> None:
    """
    Set configuration value.
    
    Args:
        key (str): Configuration key (dot notation)
        value (any): Configuration value
    """
    global _config
    
    # Split key into parts
    parts = key.split(".")
    
    # Navigate through configuration
    current = _config
    for i, part in enumerate(parts[:-1]):
        if part not in current:
            current[part] = {}
        elif not isinstance(current[part], dict):
            # Convert non-dictionary to dictionary
            current[part] = {}
        
        current = current[part]
    
    # Set value
    current[parts[-1]] = value

def save_config(path: str) -> None:
    """
    Save configuration to a file.
    
    Args:
        path (str): Path to configuration file
    """
    global _config
    
    # Get file extension
    ext = os.path.splitext(path)[1].lower()
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Save configuration based on file type
    if ext == ".yaml" or ext == ".yml":
        with open(path, "w") as f:
            yaml.dump(_config, f, default_flow_style=False)
    elif ext == ".json":
        with open(path, "w") as f:
            json.dump(_config, f, indent=2)
    else:
        raise ValueError(f"Unsupported configuration file type: {ext}")

def parse_env_value(value: str) -> Any:
    """
    Parse environment variable value.
    
    Args:
        value (str): Environment variable value
        
    Returns:
        any: Parsed value
    """
    # Try to parse as boolean
    if value.lower() in ("true", "yes", "1"):
        return True
    elif value.lower() in ("false", "no", "0"):
        return False
    
    # Try to parse as number
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        pass
    
    # Try to parse as JSON
    try:
        return json.loads(value)
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Return as string
    return value

if __name__ == "__main__":
    # Test configuration
    import sys
    
    # Load configuration
    config = load_config()
    
    # Print configuration
    print("Configuration:")
    print(json.dumps(config, indent=2))
    
    # Test get
    print("\nTest get():")
    print(f"get('sources.fec.api_key'): {get('sources.fec.api_key')}")
    print(f"get('non.existent.key', 'default'): {get('non.existent.key', 'default')}")
    
    # Test set_value
    print("\nTest set_value():")
    set_value("test.key", "test value")
    print(f"get('test.key'): {get('test.key')}")
    
    # Test nested set_value
    set_value("test.nested.key", "nested value")
    print(f"get('test.nested.key'): {get('test.nested.key')}")
    
    # Save configuration if requested
    if len(sys.argv) > 1:
        save_config(sys.argv[1])
        print(f"\nConfiguration saved to {sys.argv[1]}")