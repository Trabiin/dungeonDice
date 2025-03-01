"""
Configuration utilities for the dice roguelike game
"""

import os
import yaml
import logging

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
    """
    # Default configuration
    default_config = {
        "debug": False,
        "save_dir": "saves",
        "ui": {
            "type": "text",
            "screen_width": 80,
            "screen_height": 24
        },
        "game": {
            "difficulty": "normal",
            "starting_gold": 50,
            "inventory_size": 20
        }
    }
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}. Using default configuration.")
        return default_config
    
    try:
        # Load config from file
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Merge with default config to ensure all values exist
        merged_config = default_config.copy()
        
        # Update top-level entries
        for key, value in config.items():
            if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                # Merge nested dictionaries
                merged_config[key].update(value)
            else:
                # Replace top-level values
                merged_config[key] = value
        
        logger.info(f"Loaded configuration from {config_path}")
        return merged_config
    
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return default_config