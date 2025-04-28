"""
Centralized logging configuration for MAGA Ops scripts.
This module provides a standardized logging setup for all scripts.
"""

import os
import logging
import sys
from datetime import datetime

# Define the base log directory
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))

def setup_logging(log_level=logging.INFO, module_name=None, log_to_console=True, log_to_file=True):
    """
    Configure logging for scripts with standardized formatting.
    
    Args:
        log_level: The logging level (default: INFO)
        module_name: The name of the module for the logger (default: derived from caller)
        log_to_console: Whether to log to console (default: True)
        log_to_file: Whether to log to file (default: True)
    
    Returns:
        The configured logger
    """
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            print(f"Warning: Could not create log directory at {LOG_DIR}: {e}")
            log_to_file = False
    
    # If module_name is not provided, try to get it from the caller's module
    if module_name is None:
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        if module:
            module_name = module.__name__
        else:
            module_name = 'unknown'
    
    # Get or create logger
    logger = logging.getLogger(module_name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if log_to_file:
            # Create a filename with timestamp and module name
            timestamp = datetime.now().strftime('%Y%m%d')
            log_filename = f"{timestamp}_{module_name.replace('.', '_')}.log"
            log_path = os.path.join(LOG_DIR, log_filename)
            
            try:
                file_handler = logging.FileHandler(log_path)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not set up file logging to {log_path}: {e}")
        
        logger.info(f"Logging configured for {module_name} at level {logging.getLevelName(log_level)}")
    
    return logger

# Example usage in other scripts:
# from utils.logging_config import setup_logging
# logger = setup_logging(log_level=logging.DEBUG)
# logger.debug("This is a debug message")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
# logger.error("This is an error message")
# logger.critical("This is a critical message") 