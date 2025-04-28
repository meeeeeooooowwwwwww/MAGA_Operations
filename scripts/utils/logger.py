#!/usr/bin/env python3
"""
Logger Utility Module.

Provides functions for configuring and managing logging.
Supports file and console logging with different log levels.
"""
import os
import sys
import logging
import logging.handlers
import datetime
from typing import Dict, Optional, Union, TextIO

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Default log directory
DEFAULT_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")

# Log level mapping
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

# Cache for loggers to avoid creating duplicates
_loggers = {}

def get_log_level(level: Union[str, int]) -> int:
    """
    Get log level from string or int.
    
    Args:
        level (str or int): Log level
        
    Returns:
        int: Logging level
    """
    if isinstance(level, int):
        return level
    
    return LOG_LEVELS.get(level.lower(), logging.INFO)

def get_logger(name: str, level: Union[str, int] = "info", 
               log_file: Optional[str] = None, console: bool = True, 
               format_str: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name and configuration.
    
    Args:
        name (str): Logger name
        level (str or int, optional): Log level
        log_file (str, optional): Log file path
        console (bool, optional): Whether to log to console
        format_str (str, optional): Log format string
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check cache first
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))
    
    # Use default format if not specified
    if format_str is None:
        format_str = DEFAULT_FORMAT
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler
    if log_file is not None:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger

def setup_root_logger(level: Union[str, int] = "info", 
                      log_dir: Optional[str] = None, 
                      console: bool = True, 
                      format_str: Optional[str] = None) -> logging.Logger:
    """
    Setup root logger with file and console handlers.
    
    Args:
        level (str or int, optional): Log level
        log_dir (str, optional): Log directory
        console (bool, optional): Whether to log to console
        format_str (str, optional): Log format string
        
    Returns:
        logging.Logger: Root logger
    """
    # Use default log directory if not specified
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file path
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"app_{timestamp}.log")
    
    # Create root logger
    return get_logger("root", level, log_file, console, format_str)

def setup_rotating_logger(name: str, level: Union[str, int] = "info", 
                         log_dir: Optional[str] = None, 
                         max_bytes: int = 10485760, backup_count: int = 5, 
                         console: bool = True, 
                         format_str: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with rotating file handler.
    
    Args:
        name (str): Logger name
        level (str or int, optional): Log level
        log_dir (str, optional): Log directory
        max_bytes (int, optional): Maximum bytes per file
        backup_count (int, optional): Number of backup files
        console (bool, optional): Whether to log to console
        format_str (str, optional): Log format string
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check cache first
    if name in _loggers:
        return _loggers[name]
    
    # Use default log directory if not specified
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file path
    log_file = os.path.join(log_dir, f"{name}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))
    
    # Use default format if not specified
    if format_str is None:
        format_str = DEFAULT_FORMAT
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger

def setup_timed_rotating_logger(name: str, level: Union[str, int] = "info", 
                               log_dir: Optional[str] = None, 
                               when: str = "midnight", interval: int = 1, backup_count: int = 7, 
                               console: bool = True, 
                               format_str: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with timed rotating file handler.
    
    Args:
        name (str): Logger name
        level (str or int, optional): Log level
        log_dir (str, optional): Log directory
        when (str, optional): Rotation interval type
        interval (int, optional): Interval of specified type
        backup_count (int, optional): Number of backup files
        console (bool, optional): Whether to log to console
        format_str (str, optional): Log format string
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check cache first
    if name in _loggers:
        return _loggers[name]
    
    # Use default log directory if not specified
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log file path
    log_file = os.path.join(log_dir, f"{name}.log")
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))
    
    # Use default format if not specified
    if format_str is None:
        format_str = DEFAULT_FORMAT
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Create timed rotating file handler
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when=when,
        interval=interval,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger

def get_null_logger(name: str) -> logging.Logger:
    """
    Get a logger that doesn't output anything.
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Null logger
    """
    # Check cache first
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.addHandler(logging.NullHandler())
    
    # Cache logger
    _loggers[name] = logger
    
    return logger

def get_json_logger(name: str, level: Union[str, int] = "info", 
                   log_file: Optional[str] = None, console: bool = False) -> logging.Logger:
    """
    Get a logger that outputs JSON formatted logs.
    
    Args:
        name (str): Logger name
        level (str or int, optional): Log level
        log_file (str, optional): Log file path
        console (bool, optional): Whether to log to console
        
    Returns:
        logging.Logger: JSON logger
    """
    # Check cache first
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))
    
    # Create JSON formatter
    import json
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
                "name": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if hasattr(record, "props"):
                log_record["props"] = record.props
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_record)
    
    formatter = JsonFormatter()
    
    # Add console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Add file handler
    if log_file is not None:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        os.makedirs(log_dir, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Cache logger
    _loggers[name] = logger
    
    return logger

def clear_logger_cache() -> None:
    """Clear the logger cache."""
    _loggers.clear()

def set_log_level(name: str, level: Union[str, int]) -> None:
    """
    Set log level for a logger.
    
    Args:
        name (str): Logger name
        level (str or int): Log level
    """
    logger = logging.getLogger(name)
    logger.setLevel(get_log_level(level))

class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter for adding context to log messages."""
    
    def __init__(self, logger, extra=None):
        """
        Initialize adapter with logger and extra context.
        
        Args:
            logger (logging.Logger): Logger to adapt
            extra (dict, optional): Extra context
        """
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """
        Process the logging message and kwargs.
        
        Args:
            msg (str): Log message
            kwargs (dict): Keyword arguments
            
        Returns:
            tuple: (msg, kwargs)
        """
        # Add context to message
        if self.extra:
            context_str = " ".join(f"{k}={v}" for k, v in self.extra.items())
            msg = f"{msg} [{context_str}]"
        return msg, kwargs

def get_context_logger(name: str, context: Dict[str, str]) -> LoggerAdapter:
    """
    Get a logger with context information.
    
    Args:
        name (str): Logger name
        context (dict): Context information
        
    Returns:
        LoggerAdapter: Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)

class LogCapture:
    """Capture log output for testing."""
    
    def __init__(self, logger_name: str = None, level: Union[str, int] = "debug"):
        """
        Initialize log capture.
        
        Args:
            logger_name (str, optional): Logger name to capture
            level (str or int, optional): Log level
        """
        self.logger_name = logger_name
        self.level = get_log_level(level)
        self.handler = None
        self.logs = []
    
    def __enter__(self):
        """Setup log capture on enter."""
        import io
        
        # Create string IO
        self.string_io = io.StringIO()
        
        # Create handler
        self.handler = logging.StreamHandler(self.string_io)
        self.handler.setLevel(self.level)
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        
        # Get logger
        self.logger = logging.getLogger(self.logger_name) if self.logger_name else logging.getLogger()
        
        # Add handler
        self.logger.addHandler(self.handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup log capture on exit."""
        # Remove handler
        self.logger.removeHandler(self.handler)
        
        # Get logs
        self.logs = self.string_io.getvalue().splitlines()
        
        # Close string IO
        self.string_io.close()
    
    def get_logs(self) -> list:
        """
        Get captured logs.
        
        Returns:
            list: Captured logs
        """
        return self.logs
    
    def contains(self, text: str) -> bool:
        """
        Check if logs contain text.
        
        Args:
            text (str): Text to search for
            
        Returns:
            bool: True if text found
        """
        return any(text in log for log in self.logs)

if __name__ == "__main__":
    # Test logging functionality
    logger = get_logger("test")
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with context
    context_logger = get_context_logger("test", {"user": "admin", "request_id": "123456"})
    context_logger.info("This is a message with context")
    
    # Test log capture
    with LogCapture("test") as capture:
        logger.info("This message should be captured")
    
    print("Captured logs:")
    for log in capture.get_logs():
        print(f"  {log}")
    
    print(f"Contains 'captured': {capture.contains('captured')}")
    print(f"Contains 'not found': {capture.contains('not found')}") 