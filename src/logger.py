"""
Logger Module

This module configures the logging system for the Hotel Bookings Cancellation Predictor application.
It creates a standardized logging setup that writes logs to date-stamped files in a 'logs' directory.
The module provides consistent logging format and a convenient way to obtain logger instances
throughout the application.

Features:
- Automatic creation of logs directory if it doesn't exist
- Daily log files with date stamps
- Standardized log format with timestamp, log level, and message
- Helper function to get logger instances for different components
"""

import logging
import os
from datetime import datetime

# Directory to store log files
LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

# Create log file with current date in filename
LOG_FILE = os.path.join(LOGS_DIR, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")

# Configure basic logging settings for the application
logging.basicConfig(
    filename=LOG_FILE,
    format='%(asctime)s - %(levelname)s - %(message)s',
    level = logging.INFO
)

def get_logger(name):
    """
    Creates and returns a logger instance with the specified name.
    
    This function provides a consistent way to obtain logger instances
    throughout the application, ensuring that all loggers have the same
    configuration and log to the same file.
    
    Args:
        name (str): The name for the logger, typically the module name 
                   or component name that will be using this logger.
    
    Returns:
        logging.Logger: A configured logger instance that will write logs
                       to the application's log file with INFO level.
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger