"""
Logging utilities for the dice roguelike game
"""

import os
import logging
import sys
from datetime import datetime


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        debug: Whether to enable debug logging
    """
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configure file handler
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/dice_roguelike_{current_time}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Add handlers to the root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log initial message
    logging.info(f"Logging initialized. Debug mode: {debug}")
    if debug:
        logging.debug("Debug logging enabled")