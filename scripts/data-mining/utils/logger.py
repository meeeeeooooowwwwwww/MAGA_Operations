#!/usr/bin/env python3
"""
Logger utility for data mining operations.
Provides a standardized way to create and configure loggers.
"""
import os
import sys
import logging
from typing import Optional
from datetime import datetime

# Default log directory
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), 'logs')

# Ensure log directory exists
os.makedirs(DEFAULT_LOG_DIR, exist_ok=True)

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Log levels
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

def get_logger(
    name: str, 
    level: str = 'info', 
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Get a logger with the specified name and configuration
    
    Args:
        name (str): Logger name
        level (str, optional): Log level (debug, info, warning, error, critical)
        log_file (str, optional): Path to log file
        console (bool, optional): Whether to log to console
        
    Returns:
        logging.Logger: Logger
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Add file handler if log file specified
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # Use default log file based on module name and date
        timestamp = datetime.now().strftime('%Y%m%d')
        default_log_file = os.path.join(DEFAULT_LOG_DIR, f"{name.replace('.', '_')}_{timestamp}.log")
        
        file_handler = logging.FileHandler(default_log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

if __name__ == "__main__":
    # Test logger
    logger = get_logger(__name__, level='debug')
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message") 