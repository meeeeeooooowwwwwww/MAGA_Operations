import logging
import sys
import os

def setup_logging(log_level=logging.INFO, log_file=None):
    """Configures logging for the application.
    
    Args:
        log_level: The minimum logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a file for logging output.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    
    # Use basicConfig which sets up the root logger. 
    # This works well if called early before any other logging happens.
    handlers = [logging.StreamHandler(sys.stderr)] # Log to stderr by default
    if log_file:
        try:
            # Ensure log directory exists if log_file includes a path
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            handlers.append(logging.FileHandler(log_file, mode='a')) # Append mode
        except Exception as e:
            print(f"Error setting up file logging to {log_file}: {e}", file=sys.stderr)

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True # Force reconfig if basicConfig was called before (e.g., by a library)
    )

    # Optionally silence overly verbose libraries
    # logging.getLogger('some_verbose_library').setLevel(logging.WARNING)

    logging.info("Logging configured.")

# Example usage (if you want to test this file directly)
if __name__ == '__main__':
    log_path = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "backend.log")
    print(f"Setting up test logging. Log file path: {log_path}")
    # setup_logging(log_level=logging.DEBUG, log_file=log_path)
    setup_logging(log_level=logging.DEBUG) # Log to stderr for simple test

    logger = logging.getLogger("TestLogger")
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    try:
        x = 1 / 0
    except ZeroDivisionError:
        logger.exception("Caught an exception!") # Logs exception info automatically 