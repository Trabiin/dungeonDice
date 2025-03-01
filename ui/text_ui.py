"""
Text-based UI for the dice roguelike game
"""

import os
import time
import sys
import random
from typing import Dict, List, Any, Optional, Tuple
import logging
from core.enums import DiceType, RoomType
from game.game_instance import GameInstance

logger = logging.getLogger(__name__)


class TextUI:
    """
    Text-based user interface for the game.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the text UI."""
        self.config = config or {}
        self.game = GameInstance(config)
        self.screen_width = self.config.get("ui", {}).get("screen_width", 80)
        self.running = False
    
    def clear_screen(self) -> None:
        """Clear the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str) -> None:
        """Print a section header."""
        self.clear_screen()
        print("=" * self.screen_width)
        print(f"{title:^{self.screen_width}}")
        print("=" * self.screen_width)
    
    def print_separator(self) -> None:
        """Print a separator line."""
        print("-" * self.screen_width)
    
    def print_centered(self, text: str) -> None:
        """Print centered text."""
        print(f"{text:^{self.screen_width}}")
    
    def wait_for_key(self) -> None:
        """Wait for the user to press Enter."""
        input("\nPress Enter to continue...")
    
    def get_menu_choice(self, options: List[str], prompt: str = "Choose an option: ") -> int:
        """
        Display a menu and get user choice.
        Returns the index of the chosen option.
        """
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        while True:
            try:
                choice = int(input(f"\n{prompt}"))
                if 1 <= choice <= len(options):
                    return choice - 1
                print(f"Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Please enter a valid number.")
    
    def get_yes_no(self, prompt: str = "Continue? (y/n): ") -> bool:
        """Get a yes/no response from the user."""
        while True:
            response = input(prompt).lower()
            if response in ["y", "yes"]:
                return True
            if response in ["n", "no"]:
                return False
            print("Please enter 'y' or 'n'.")
    
    def show_main_menu(self) -> str:
        """Show the main menu and return the selected action."""
        self.print_header("DICE ROGUELIKE")
        self.print_centered("A dice-based roguelike RPG")
        print("\n")
        
        options = ["New Game", "Load Game", "Exit"]
        choice = self.get_menu_choice(options, "Select an option: ")
        
        if choice == 0:
            return "new_game"
        elif choice == 1:
            return "load_game"
        else:
            return "exit"
    
    def show_character_creation(self) -> Dict[str, str]:
        """Show character creation screen and return player choices."""
        self.print_header("CHARACTER CREATION")
        
        name = input("Enter your character's name: ")
        while not name:
            print("Name cannot be empty.")
            name = input("Enter your character's name: ")
        
        classes = ["Warrior", "Mage", "Rogue"]
        print("\nChoose a class:")
        print("1. Warrior - High health and physical damage")
        print("2. Mage - High mana and magical damage")
        print("3. Rogue - High speed, dodge, and critical chance")
        
        class_choice = self.get_menu_choice(classes, "Select a class: ")
        character_class = classes[class_choice]
        
        return {"name": name, "class": character_class}
    
    def show_load_game(self) -> Optional[str]:
        """Show load game screen and return the selected save file."""
        self.print_header("LOAD GAME")
        
        save_dir = self.config.get("save_dir", "saves")
        os.makedirs(save_dir, exist_ok=True)
        
        save_files = [f for f in os.listdir(save_dir) if f.endswith(".json")]
        
        if not save_files:
            print("No save files found.")
            self.wait_for_key()
            return None
        
        print("Available save files:")
        choice = self.get_menu_choice(save_files, "Select a save file to load: ")
        
        return save_files[choice]
    
    def show_game_over(self, victory: bool) -> None:
        """Show game over screen."""
        if victory:
            self.print_header("VICTORY!")
            self.print_centered("Congratulations! You have completed the dungeon!")
        else:
            self.print_header("GAME OVER")
            self.print_centered("You have been defeated...")
        
        self.wait_for_key()
    
    def show_character_info(self) -> None:
        """Show character information."""
        if not self.game.state:
            return
        
        info = self.game.get_player_info()
        
        self.print_header(f"{info['name']} the {info['class']}")
        print(f"Level: {info['level']} ({info['xp']}/{info['xp_to_next_level']} XP)")
        print(f"Health: {info['health']}/{info['max_health']}")
        print(f"Mana: {info['mana']}/{info['max_mana']}")
        print(f"Physical Damage: {info['physical_damage']}")
        print(f"Magic Damage: {info['magic_damage']}")
        print(f"Speed: {info['speed']}")
        print(f"Dodge: {info['dodge']:.1%}")
        print(f"Critical Chance: {info['crit_chance']:.1%}")
        print(f"Critical Damage: {info['crit_damage']:.1f}x")
        
        if info['status_effects']:
            self.print_separator()
            print("Status Effects:")
            for effect in info['status_effects']:
                print(f"- {effect['name']}: {effect['turns']} turns remaining")
        
        if info['passive_bonuses']:
            self.print_separator()
            print("Passive Bonuses:")
            for bonus in info['passive_bonuses']:
                print(f"- {bonus['name']}: {bonus['value']}")
        
        self.wait_for_key()
    
    def show_inventory(self) -> None:
        """Show inventory screen."""
        if not self.game.state:
            return
        
        while True:
            result = self.game.handle_inventory("view")
            
            self.print_header("INVENTORY")
            print(f"Gold: {result['gold']}")
            print(f"Capacity: {result['capacity']}")
            
            if not result['items']:
                print("\nYour inventory is empty.")
                self.wait_for_key()
                return
            
            self.print_separator()
            print("Items:")
            for i, item in enumerate(result['items']):
                print(f"{i+1}. {item['name']} - {item['effect']}")
            
            options = ["Use Item", "Drop Item", "Back"]
            choice = self.get_menu_choice(options, "Select an action: ")
            
            if choice == 0:  # Use Item
                item_index = self.get_menu_choice([item['name'] for item in result['items']], "Select an item to use: ")
                use_result = self.game.handle_inventory("use", item_index)
                
                if 'error' in use_result:
                    print(f"Error: {use_result['error']}")
                else:
                    print(use_result['message'])
                
                self.wait_for_key()
            
            elif choice == 1:  # Drop Item
                item_index = self.get_menu_choice([item['name'] for item in result['items']], "Select an item to drop: ")
                if self.get_yes_no(f"Are you sure you want to drop {result['items'][item_index]['name']}? (y/n): "):
                    drop_result = self.game.handle_inventory("drop", item_index)
                    print(drop_result['message'])
                
                self.wait_for_key()
            
            else:  # Back
                return
    
    def show_dice(self) -> None:
        """Show dice information."""
        if not self.game.state:
            return
        
        dice_info = self.game.get_dice_info()
        
        while True:
            self.print_header("DICE COLLECTION")
            
            # Get all dice categories with dice
            dice_categories = [category for category in dice_info.keys() if dice_info[category]]
            
            if not dice_categories:
                print("You don't have any dice yet.")
                self.wait_for_key()
                return
            
            # Print categories
            print("Select a dice category:")
            category_choice = self.get_menu_choice(dice_categories, "Select a category: ")
            selected_category = dice_categories[category_choice]
            
            # Show dice in selected category
            while True:
                self.print_header(f"{selected_category} DICE")
                dice_list = dice_info[selected_category]
                
                for i, die in enumerate(dice_list):
                    print(f"{i+1}. {die['name']} (d{die['size']}, {die['rarity']})")
                    
                print(f"{len(dice_list)+1}. Back")
                
                die_choice = int(input("\nSelect a die to examine (or back): ")) - 1
                
                if die_choice == len(dice_list):
                    break
                
                if 0 <= die_choice < len(dice_list):
                    self.show_die_details(dice_list[die_choice])
            
            if self.get_yes_no("Return to main menu? (y/n): "):
                return
    
    def show_die_details(self, die: Dict[str, Any]) -> None:
        """Show detailed information about a specific die."""
        self.print_header(f"{die['name']}")
        print(f"Type: d{die['size']}")
        print(f"Rarity: {die['rarity']}")
        print(f"Level: {die['level']}")
        
        if die['description']:
            print(f"\n{die['description']}")
        
        print(f"\nBalance: {die['balance_value']} ({die['imbalance_effect']})")
        print(f"Imbalance Severity: {die['imbalance_severity']:.2f}")
        
        if die['cooldown'] > 0:
            print(f"Cooldown: {die['cooldown']} turns remaining")
        
        self.print_separator()
        print("Faces:")
        
        for i, face in enumerate(die['faces']):
            value_str = f"+{face['value']}" if face['value'] > 0 else str(face['value'])
            print(f"{i+1}. {face['name']} ({value_str}, {face['category']})")
            print(f"   {face['description']}")
            
            if 'cost' in face and face['cost']:
                costs = ", ".join([f"{amount} {resource}" for resource, amount in face['cost'].items()])
                print(f"   Cost: {costs}")
            
            if 'synergies' in face and face['synergies']:
                print(f"   Synergies: {', '.join(face['synergies'])}")
        
        self.wait_for_key()
    
    def show_dungeon_info(self) -> None:
        """Show information about the current dungeon."""
        if not self.game.state:
            return
        
        info = self.game.get_dungeon_info()
        
        self.print_header("DUNGEON INFO")
        print(f"Floor: {info['floor_level']}")
        print(f"Current Room: {info['current_room']['name']} ({info['current_room']['type']})")
        print(f"Progress: {info['completed_rooms']}/{info['room_count']} rooms cleared")
        
        if info['current_room']['description']:
            self.print_separator()
            print(info['current_room']['description'])
        
        if info['available_paths']:
            self.print_separator()
            print("Available paths:")
            for index, name, room_type in info['available_paths']:
                print(f"- {name} ({room_type})")
        
        self.wait_for_key()
    
    def handle_combat(self, enemies: List[Dict[str, Any]]) -> None:
        """Handle combat sequences."""
        if not self.game.state or not self.game.state.in_combat:
            return
            
        while self.game.state.in_combat:
            self.print_header("COMBAT")
            
            # Display player info
            player_info = self.game.get_player_info()
            print(f"{player_info['name']} - Health: {player_info['health']}/{player_info['max_health']} | Mana: {player_info['mana']}/{player_info['max_mana']}")
            
            # Display enemies
            self.print_separator()
            print("Enemies:")
            for i, enemy in enumerate(self.game.state.combat_enemies):
                print(f"{i+1}. {enemy.name} - Health: {enemy.health}/{enemy.max_health}")
            
            # Get available dice
            dice_info = self.game.get_dice_info()
            combat_dice = []
            
            for dice_type in ["COMBAT", "SPECIAL"]:
                if dice_type in dice_info:
                    for die_index, die in enumerate(dice_info[dice_type]):
                        if die['cooldown'] == 0:
                            combat_dice.append((dice_type, die_index, die))
            
            # Display available dice
            self.print_separator()
            print("Available Dice:")
            
            if not combat_dice:
                print("No dice available! All on cooldown.")
                # Skip turn
                self.wait_for_key()
                
                # Process enemy turns directly
                for enemy in self.game.state.combat_enemies:
                    result = self.game.combat_system.enemy_turn(enemy, self.game.state.player)
                    print(f"{result.message}")
                    
                    if result.target_defeated:
                        self.game.state.game_over = True
                        print("You have been defeated!")
                        self.wait_for_key()
                        return
                
                self.wait_for_key()
                continue
            
            for i, (dice_type, dice_index, die) in enumerate(combat_dice):
                print(f"{i+1}. {die['name']} (d{die['size']}, {die['rarity']})")
            
            # Add inventory and run away options
            print(f"{len(combat_dice)+1}. Use Item")
            print(f"{len(combat_dice)+2}. Run Away")
            
            # Get player action
            choice = int(input("\nChoose a die to roll (or other action): ")) - 1
            
            if choice == len(combat_dice):
                # Show inventory
                inventory_result = self.game.handle_inventory("view")
                
                if not inventory_result['items']:
                    print("Your inventory is empty.")
                    self.wait_for_key()
                    continue
                
                item_index = self.get_menu_choice([item['name'] for item in inventory_result['items']], "Select an item to use: ")
                use_result = self.game.handle_inventory("use", item_index)
                
                if 'error' in use_result:
                    print(f"Error: {use_result['error']}")
                else:
                    print(use_result['message'])
                
                self.wait_for_key()
                continue
                
            elif choice == len(combat_dice) + 1:
                # Run away
                if self.get_yes_no("Are you sure you want to run away? You may take damage while fleeing. (y/n): "):
                    # 50% chance to escape
                    if random.random() < 0.5:
                        print("You successfully escape from combat!")
                        self.game.state.in_combat = False
                        self.game.state.combat_enemies = []
                        self.wait_for_key()
                        return
                    else:
                        # Take damage for failing to escape
                        damage = random.randint(5, 15)
                        self.game.state.player.stats.health -= damage
                        print(f"You failed to escape and took {damage} damage!")
                        
                        # Check if player died
                        if self.game.state.player.stats.health <= 0:
                            self.game.state.player.stats.health = 0
                            self.game.state.game_over = True
                            self.game.state.in_combat = False
                            print("You have been defeated while trying to escape!")
                            self.wait_for_key()
                            return
                        
                        self.wait_for_key()
                        continue
                else:
                    continue
            
            if 0 <= choice < len(combat_dice):
                # Roll selected die
                dice_type, dice_index, die = combat_dice[choice]
                
                # If multiple enemies, select target
                target_index = 0
                if len(self.game.state.combat_enemies) > 1:
                    target_index = self.get_menu_choice(
                        [f"{i+1}. {e.name} - Health: {e.health}/{e.max_health}" for i, e in enumerate(self.game.state.combat_enemies)],
                        "Select a target: "
                    )
                
                # Execute combat turn
                result = self.game.handle_combat_turn(DiceType[dice_type], dice_index, target_index)
                
                if 'error' in result:
                    print(f"Error: {result['error']}")
                    self.wait_for_key()
                    continue
                
                # Display results
                print(f"\n{result['message']}")
                
                if 'combat_over' in result and result['combat_over']:
                    if 'player_defeated' in result and result['player_defeated']:
                        print("You have been defeated!")
                        self.wait_for_key()
                        return
                    else:
                        print("All enemies defeated!")
                        if 'gold_reward' in result:
                            print(f"You gained {result['gold_reward']} gold and {result['xp_reward']} XP.")
                        self.wait_for_key()
                        return
                
                # Display enemy turns
                if 'enemy_turns' in result:
                    self.print_separator()
                    print("Enemy Turns:")
                    for enemy_result in result['enemy_turns']:
                        print(f"- {enemy_result['message']}")
                
                if 'combat_log' in result:
                    self.print_separator()
                    print("Combat Log:")
                    for entry in result['combat_log']:
                        print(f"- {entry}")
                
                self.wait_for_key()
    
    def handle_rest_site(self) -> None:
        """Handle interactions at a rest site."""
        self.print_separator()
        print("You've found a safe place to rest.")
        
        if self.get_yes_no("Would you like to rest? (y/n): "):
            result = self.game.handle_rest()
            print(result['message'])
            
            if result['cleared_effects']:
                print(f"Cleared status effects: {', '.join(result['cleared_effects'])}")
            
            self.wait_for_key()
    
    def handle_shop(self, room_info: Dict[str, Any]) -> None:
        """Handle shop interactions."""
        self.print_separator()
        print("A merchant has set up shop here.")
        
        if self.get_yes_no("Would you like to browse the shop? (y/n): "):
            while True:
                # Get shop inventory
                shop_info = self.game.handle_shop("browse")
                
                self.print_header("SHOP")
                print(f"Your Gold: {shop_info['gold']}")
                
                if not shop_info['items']:
                    print("\nThe shop is empty.")
                    self.wait_for_key()
                    return
                
                self.print_separator()
                print("Items for Sale:")
                for i, item in enumerate(shop_info['items']):
                    print(f"{i+1}. {item['name']} - {item['value']} gold")
                    print(f"   {item['description']}")
                    print(f"   Effect: {item['effect']}")
                
                print(f"{len(shop_info['items'])+1}. Leave Shop")
                
                choice = int(input("\nSelect an item to buy (or leave): ")) - 1
                
                if choice == len(shop_info['items']):
                    return
                
                if 0 <= choice < len(shop_info['items']):
                    item = shop_info['items'][choice]
                    
                    if shop_info['gold'] < item['value']:
                        print(f"You don't have enough gold. You need {item['value']} gold.")
                        self.wait_for_key()
                        continue
                    
                    if self.get_yes_no(f"Buy {item['name']} for {item['value']} gold? (y/n): "):
                        result = self.game.handle_shop("buy", choice)
                        
                        if 'error' in result:
                            print(f"Error: {result['error']}")
                        else:
                            print(result['message'])
                        
                        self.wait_for_key()
    
    def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle event interactions."""
        self.print_separator()
        print(f"{event['name']}")
        print(event['description'])
        
        self.print_separator()
        print("Choices:")
        for i, choice in enumerate(event['choices']):
            print(f"{i+1}. {choice}")
        
        choice = self.get_menu_choice(event['choices'], "What will you do? ")
        result = self.game.handle_event(choice)
        
        print(f"\n{result['message']}")
        self.wait_for_key()
    
    def show_room(self) -> None:
        """Show the current room and available actions."""
        if not self.game.state:
            return
        
        room_info = self.game.handle_room()
        
        # Handle game over
        if self.game.state.game_over:
            return
        
        # Display room
        self.print_header(f"{room_info['name']} - {room_info['room_type']}")
        print(room_info['description'])
        
        # If in combat, handle combat
        if room_info['in_combat']:
            self.handle_combat(room_info['enemies'])
            return
        
        # Display room contents
        if room_info['enemies']:
            self.print_separator()
            print("Enemies:")
            for enemy in room_info['enemies']:
                print(f"- {enemy['name']} ({enemy['health']}/{enemy['max_health']} HP)")
        
        if room_info['items']:
            self.print_separator()
            print("Items:")
            for item in room_info['items']:
                print(f"- {item['name']}: {item['description']}")
        
        if room_info['gold'] > 0:
            self.print_separator()
            print(f"Gold: {room_info['gold']}")
        
        # Handle room specific actions
        if room_info['room_type'] == "REST":
            self.handle_rest_site()
        elif room_info['room_type'] == "SHOP":
            self.handle_shop(room_info)
        elif room_info['room_type'] == "EVENT" and room_info['event']:
            self.handle_event(room_info['event'])
        elif room_info['room_type'] == "TRAP" and room_info['event']:
            self.handle_event(room_info['event'])
        elif room_info['room_type'] == "EXIT":
            print("\nYou've found the exit to the next floor!")
            if self.get_yes_no("Proceed to the next floor? (y/n): "):
                return  # Proceed to next floor
        
        # Show available actions
        self.show_room_actions(room_info)
    
    def show_room_actions(self, room_info: Dict[str, Any]) -> None:
        """Show available actions in the current room."""
        self.print_separator()
        print("Actions:")
        
        options = ["Character Info", "Inventory", "Dice Collection", "Dungeon Info"]
        
        # Add navigation if paths are available
        if room_info['paths']:
            options.append("Move to Next Room")
        
        options.append("Save Game")
        options.append("Quit Game")
        
        choice = self.get_menu_choice(options, "What would you like to do? ")
        
        if choice == 0:  # Character Info
            self.show_character_info()
        elif choice == 1:  # Inventory
            self.show_inventory()
        elif choice == 2:  # Dice Collection
            self.show_dice()
        elif choice == 3:  # Dungeon Info
            self.show_dungeon_info()
        elif choice == 4 and room_info['paths']:  # Move to Next Room
            path_choice = self.get_menu_choice(
                [f"{name} ({room_type})" for _, name, room_type in room_info['paths']],
                "Select a path: "
            )
            room_index = room_info['paths'][path_choice][0]
            self.game.handle_navigation(room_index)
        elif choice == len(options) - 2:  # Save Game
            filename = input("Enter save file name: ")
            if filename:
                success = self.game.save_game(filename)
                if success:
                    print(f"Game saved as {filename}.")
                else:
                    print("Failed to save game.")
                self.wait_for_key()
        elif choice == len(options) - 1:  # Quit Game
            if self.get_yes_no("Are you sure you want to quit? Progress since last save will be lost. (y/n): "):
                self.running = False
    
    def run(self) -> None:
        """Run the main game loop."""
        self.running = True
        
        while self.running:
            # If no game is active, show main menu
            if not self.game.state:
                action = self.show_main_menu()
                
                if action == "new_game":
                    player_choices = self.show_character_creation()
                    success = self.game.new_game(player_choices["name"], player_choices["class"])
                    
                    if not success:
                        print("Failed to create new game.")
                        self.wait_for_key()
                
                elif action == "load_game":
                    save_file = self.show_load_game()
                    if save_file:
                        success = self.game.load_game(save_file)
                        
                        if not success:
                            print(f"Failed to load game from {save_file}.")
                            self.wait_for_key()
                
                elif action == "exit":
                    self.running = False
                    print("Thanks for playing!")
                    break
            
            # If game is active, show the current room
            else:
                self.show_room()
                
                # Check for game over
                if self.game.state and self.game.state.game_over:
                    self.show_game_over(self.game.state.victory)
                    # Reset game state
                    self.game.state = None