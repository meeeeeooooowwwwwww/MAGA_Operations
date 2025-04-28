#!/usr/bin/env python3
"""
Configuration Utility Module.

Provides functions for managing application configuration.
Supports loading, saving, and accessing configuration settings.
"""
import os
import json
import yaml
import logging
from typing import Any, Dict, List, Optional, Union

# Default configuration
DEFAULT_CONFIG = {
    "general": {
        "debug": False,
        "log_level": "info",
        "log_dir": "logs",
        "data_dir": "data",
        "cache_dir": "cache"
    },
    "database": {
        "path": "maga_ops.db",
        "backup_dir": "backups",
        "auto_backup": True
    },
    "api": {
        "host": "localhost",
        "port": 5000,
        "debug": False,
        "secret_key": ""
    }
}

# Global configuration store
_config: Dict[str, Any] = {}
_config_loaded = False
_config_path = None

def init(config_path: Optional[str] = None, defaults: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize configuration.
    
    Args:
        config_path (str, optional): Path to configuration file
        defaults (dict, optional): Default configuration
        
    Returns:
        dict: Configuration dictionary
    """
    global _config, _config_loaded, _config_path
    
    # Set default configuration
    if defaults is None:
        _config = DEFAULT_CONFIG.copy()
    else:
        _config = defaults.copy()
    
    # Set configuration path
    if config_path is not None:
        _config_path = config_path
    else:
        # Use default path in project root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _config_path = os.path.join(root_dir, "config", "config.yaml")
    
    # Load configuration from file
    load()
    
    return _config

def load(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path (str, optional): Path to configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    global _config, _config_loaded, _config_path
    
    # Set configuration path if provided
    if config_path is not None:
        _config_path = config_path
    
    # Try to load configuration from file
    if _config_path and os.path.exists(_config_path):
        try:
            with open(_config_path, "r", encoding="utf-8") as f:
                # Determine file format
                if _config_path.endswith(".json"):
                    file_config = json.load(f)
                else:
                    file_config = yaml.safe_load(f)
                
                # Update configuration
                deep_update(_config, file_config)
            
            _config_loaded = True
        except Exception as e:
            logging.error(f"Error loading configuration from {_config_path}: {e}")
    
    return _config

def save(config_path: Optional[str] = None) -> bool:
    """
    Save configuration to file.
    
    Args:
        config_path (str, optional): Path to configuration file
        
    Returns:
        bool: True if successful
    """
    global _config, _config_path
    
    # Set configuration path if provided
    if config_path is not None:
        _config_path = config_path
    
    # Return if no configuration path
    if _config_path is None:
        logging.error("No configuration path specified")
        return False
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(_config_path), exist_ok=True)
        
        with open(_config_path, "w", encoding="utf-8") as f:
            # Determine file format
            if _config_path.endswith(".json"):
                json.dump(_config, f, indent=2)
            else:
                yaml.dump(_config, f, default_flow_style=False)
        
        return True
    except Exception as e:
        logging.error(f"Error saving configuration to {_config_path}: {e}")
        return False

def get(key: str, default: Any = None) -> Any:
    """
    Get configuration value by key.
    
    Args:
        key (str): Configuration key (dot notation)
        default (any, optional): Default value
        
    Returns:
        any: Configuration value
    """
    global _config, _config_loaded
    
    # Load configuration if not loaded
    if not _config_loaded:
        load()
    
    # Split key by dots
    parts = key.split(".")
    
    # Get value from configuration
    value = _config
    
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
    
    return value

def set(key: str, value: Any, save_config: bool = False) -> None:
    """
    Set configuration value by key.
    
    Args:
        key (str): Configuration key (dot notation)
        value (any): Configuration value
        save_config (bool, optional): Save configuration to file
    """
    global _config
    
    # Split key by dots
    parts = key.split(".")
    
    # Navigate to parent of target key
    config = _config
    
    for part in parts[:-1]:
        if part not in config:
            config[part] = {}
        
        config = config[part]
    
    # Set value
    config[parts[-1]] = value
    
    # Save configuration if requested
    if save_config:
        save()

def has(key: str) -> bool:
    """
    Check if configuration key exists.
    
    Args:
        key (str): Configuration key (dot notation)
        
    Returns:
        bool: True if key exists
    """
    return get(key) is not None

def delete(key: str, save_config: bool = False) -> bool:
    """
    Delete configuration value by key.
    
    Args:
        key (str): Configuration key (dot notation)
        save_config (bool, optional): Save configuration to file
        
    Returns:
        bool: True if deleted
    """
    global _config
    
    # Split key by dots
    parts = key.split(".")
    
    # Navigate to parent of target key
    config = _config
    
    for part in parts[:-1]:
        if part not in config:
            return False
        
        config = config[part]
    
    # Delete key
    if parts[-1] in config:
        del config[parts[-1]]
        
        # Save configuration if requested
        if save_config:
            save()
        
        return True
    
    return False

def reset(save_config: bool = False) -> None:
    """
    Reset configuration to defaults.
    
    Args:
        save_config (bool, optional): Save configuration to file
    """
    global _config
    
    # Reset configuration
    _config = DEFAULT_CONFIG.copy()
    
    # Save configuration if requested
    if save_config:
        save()

def get_all() -> Dict[str, Any]:
    """
    Get all configuration values.
    
    Returns:
        dict: Configuration dictionary
    """
    global _config, _config_loaded
    
    # Load configuration if not loaded
    if not _config_loaded:
        load()
    
    return _config.copy()

def update(config: Dict[str, Any], save_config: bool = False) -> None:
    """
    Update configuration with values from dictionary.
    
    Args:
        config (dict): Configuration dictionary
        save_config (bool, optional): Save configuration to file
    """
    global _config
    
    # Update configuration
    deep_update(_config, config)
    
    # Save configuration if requested
    if save_config:
        save()

def deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep update dictionary.
    
    Args:
        target (dict): Target dictionary
        source (dict): Source dictionary
        
    Returns:
        dict: Updated dictionary
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            deep_update(target[key], value)
        else:
            target[key] = value
    
    return target

def get_all_keys(prefix: str = "") -> List[str]:
    """
    Get all configuration keys.
    
    Args:
        prefix (str, optional): Key prefix
        
    Returns:
        list: Configuration keys
    """
    keys = []
    
    def collect_keys(d, current_prefix):
        for k, v in d.items():
            key = f"{current_prefix}.{k}" if current_prefix else k
            
            if isinstance(v, dict):
                collect_keys(v, key)
            else:
                keys.append(key)
    
    collect_keys(_config, prefix)
    
    return keys

def load_from_env(prefix: str = "APP_") -> None:
    """
    Load configuration from environment variables.
    
    Args:
        prefix (str, optional): Environment variable prefix
    """
    for key, value in os.environ.items():
        # Check if key starts with prefix
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower()
            
            # Replace double underscore with dot for hierarchy
            config_key = config_key.replace("__", ".")
            
            # Convert value type
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit() and value.count(".") == 1:
                value = float(value)
            
            # Set configuration value
            set(config_key, value)

def load_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        file_path (str): Path to configuration file
        
    Returns:
        dict: Configuration dictionary
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Determine file format
            if file_path.endswith(".json"):
                file_config = json.load(f)
            else:
                file_config = yaml.safe_load(f)
            
            # Update configuration
            update(file_config)
            
            return file_config
    except Exception as e:
        logging.error(f"Error loading configuration from {file_path}: {e}")
        return {}

def generate_default_config(file_path: Optional[str] = None) -> str:
    """
    Generate default configuration file.
    
    Args:
        file_path (str, optional): Path to configuration file
        
    Returns:
        str: Configuration file path
    """
    # Set default configuration path if not provided
    if file_path is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(root_dir, "config", "config.yaml")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Write default configuration to file
    with open(file_path, "w", encoding="utf-8") as f:
        if file_path.endswith(".json"):
            json.dump(DEFAULT_CONFIG, f, indent=2)
        else:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
    
    return file_path

def validate_config(schema: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Validate configuration against schema.
    
    Args:
        schema (dict, optional): Validation schema
        
    Returns:
        list: Validation errors
    """
    if schema is None:
        # Use default validation schema based on default config
        schema = {}
        
        def build_schema(d, current_schema):
            for k, v in d.items():
                if isinstance(v, dict):
                    current_schema[k] = {}
                    build_schema(v, current_schema[k])
                else:
                    current_schema[k] = type(v)
        
        build_schema(DEFAULT_CONFIG, schema)
    
    errors = []
    
    def validate(config, schema, path=""):
        for k, v in schema.items():
            key_path = f"{path}.{k}" if path else k
            
            if k not in config:
                errors.append(f"Missing required key: {key_path}")
            elif isinstance(v, dict):
                if not isinstance(config[k], dict):
                    errors.append(f"Invalid type for {key_path}: expected dict")
                else:
                    validate(config[k], v, key_path)
            elif isinstance(v, type) and not isinstance(config[k], v):
                errors.append(f"Invalid type for {key_path}: expected {v.__name__}")
    
    validate(_config, schema)
    
    return errors

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize configuration
    init()
    
    # Set some values
    set("general.app_name", "MAGA Ops")
    set("api.port", 8080)
    
    # Get values
    print(f"App name: {get('general.app_name')}")
    print(f"Log level: {get('general.log_level')}")
    print(f"Database path: {get('database.path')}")
    print(f"API port: {get('api.port')}")
    
    # Get all keys
    print("\nAll configuration keys:")
    for key in get_all_keys():
        print(f"  {key} = {get(key)}")
    
    # Update configuration
    update({
        "general": {
            "debug": True
        },
        "api": {
            "host": "0.0.0.0"
        }
    })
    
    print("\nAfter update:")
    print(f"Debug mode: {get('general.debug')}")
    print(f"API host: {get('api.host')}")
    
    # Generate default configuration file
    temp_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_config.yaml")
    
    try:
        config_path = generate_default_config(temp_config_path)
        print(f"\nGenerated default configuration at: {config_path}")
        
        # Save current configuration
        save(temp_config_path)
        print(f"Saved configuration to: {temp_config_path}")
        
        # Reset configuration
        reset()
        
        # Load from file
        load_from_file(temp_config_path)
        print(f"\nConfiguration after loading from file:")
        print(f"Debug mode: {get('general.debug')}")
        print(f"API host: {get('api.host')}")
        
        # Validate configuration
        validation_errors = validate_config()
        if validation_errors:
            print("\nValidation errors:")
            for error in validation_errors:
                print(f"  {error}")
        else:
            print("\nConfiguration is valid")
    finally:
        # Clean up
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path) 