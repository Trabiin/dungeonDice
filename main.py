"""
Dice-Based Roguelike RPG
Main entry point for the game
"""

import argparse
import sys
from utils.config import load_config
from utils.logging import setup_logging
from ui.text_ui import TextUI

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Dice-Based Roguelike RPG')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', type=str, default='config.yaml', help='Configuration file path')
    return parser.parse_args()

def main():
    """Main entry point for the game."""
    # Parse command-line arguments
    args = parse_args()
    
    # Setup logging
    setup_logging(debug=args.debug)
    
    # Load configuration
    config = load_config(args.config)
    
    # Start the game with text UI for now
    game = TextUI(config)
    game.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated by user.")
        sys.exit(0)
