"""
Main game instance that manages the game state
"""

import random
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from core.character import Character, CharacterStats
from core.dice import DiceSet, Dice, DiceFace
from core.enums import DiceType, FaceCategory, RoomType, Rarity
from core.inventory import Inventory, Item, ItemFactory
from game.dungeon import Floor, Room, Enemy, DungeonGenerator, Event
from game.combat import CombatSystem, CombatResult
import logging

logger = logging.getLogger(__name__)


@dataclass
class GameState:
    """
    Represents the current state of the game.
    """
    player: Character
    inventory: Inventory
    current_floor: Optional[Floor] = None
    floors: List[Floor] = field(default_factory=list)
    floor_level: int = 1
    in_combat: bool = False
    combat_enemies: List[Enemy] = field(default_factory=list)
    game_over: bool = False
    victory: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "player": self.player.to_dict(),
            "inventory": self.inventory.to_dict(),
            "current_floor": self.current_floor.to_dict() if self.current_floor else None,
            "floors": [floor.to_dict() for floor in self.floors],
            "floor_level": self.floor_level,
            "in_combat": self.in_combat,
            "combat_enemies": [enemy.to_dict() for enemy in self.combat_enemies],
            "game_over": self.game_over,
            "victory": self.victory
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GameState':
        """Create a GameState from a dictionary."""
        from core.character import Character
        from core.inventory import Inventory
        from game.dungeon import Floor, Enemy
        
        # Create player
        player_data = data.get("player", {})
        player = Character.from_dict(player_data)
        
        # Create inventory
        inventory_data = data.get("inventory", {})
        inventory = Inventory.from_dict(inventory_data)
        
        # Create floors
        floors_data = data.get("floors", [])
        floors = [Floor.from_dict(floor_data) for floor_data in floors_data]
        
        # Create current floor
        current_floor_data = data.get("current_floor")
        current_floor = Floor.from_dict(current_floor_data) if current_floor_data else None
        
        # Create combat enemies
        combat_enemies_data = data.get("combat_enemies", [])
        combat_enemies = [Enemy.from_dict(enemy_data) for enemy_data in combat_enemies_data]
        
        # Create game state
        return cls(
            player=player,
            inventory=inventory,
            current_floor=current_floor,
            floors=floors,
            floor_level=data.get("floor_level", 1),
            in_combat=data.get("in_combat", False),
            combat_enemies=combat_enemies,
            game_over=data.get("game_over", False),
            victory=data.get("victory", False)
        )


class DiceManager:
    """
    Manages dice creation and modification.
    """
    @staticmethod
    def create_starter_dice(character_class: str) -> DiceSet:
        """
        Create starter dice for a new character based on their class.
        """
        dice_set = DiceSet()
        
        # Add character dice
        if character_class.lower() == "warrior":
            character_die = DiceManager._create_warrior_character_die()
        elif character_class.lower() == "mage":
            character_die = DiceManager._create_mage_character_die()
        elif character_class.lower() == "rogue":
            character_die = DiceManager._create_rogue_character_die()
        else:
            # Default to warrior
            character_die = DiceManager._create_warrior_character_die()
            
        dice_set.add_dice(character_die)
        
        # Add combat dice
        combat_die = DiceManager._create_basic_combat_die(character_class)
        dice_set.add_dice(combat_die)
        
        # Add encounter dice
        encounter_die = DiceManager._create_basic_encounter_die()
        dice_set.add_dice(encounter_die)
        
        return dice_set
    
    @staticmethod
    def _create_warrior_character_die() -> Dice:
        """
        Create a character die for a warrior.
        """
        die = Dice(
            name="Warrior's Soul",
            dice_type=DiceType.CHARACTER,
            size=6,
            rarity=Rarity.COMMON,
            description="A balanced character die representing a warrior's core attributes."
        )
        
        # Add faces with balanced positive and negative traits
        die.add_face(DiceFace(
            name="Strength",
            value=2,
            category=FaceCategory.TRAIT,
            effect_description="Increases physical damage by 2"
        ))
        
        die.add_face(DiceFace(
            name="Vitality",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases max health by 10%"
        ))
        
        die.add_face(DiceFace(
            name="Battle Sense",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases dodge by 5% and crit chance by 5%"
        ))
        
        die.add_face(DiceFace(
            name="Weakness",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases physical damage by 1"
        ))
        
        die.add_face(DiceFace(
            name="Slowness",
            value=-2,
            category=FaceCategory.TRAIT,
            effect_description="Decreases speed by 2 and dodge by 4%"
        ))
        
        die.add_face(DiceFace(
            name="Battle Focus",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases magic damage by 1"
        ))
        
        return die
    
    @staticmethod
    def _create_mage_character_die() -> Dice:
        """
        Create a character die for a mage.
        """
        die = Dice(
            name="Arcane Mind",
            dice_type=DiceType.CHARACTER,
            size=6,
            rarity=Rarity.COMMON,
            description="A balanced character die representing a mage's core attributes."
        )
        
        # Add faces with balanced positive and negative traits
        die.add_face(DiceFace(
            name="Intelligence",
            value=2,
            category=FaceCategory.TRAIT,
            effect_description="Increases magic damage by 2"
        ))
        
        die.add_face(DiceFace(
            name="Mana Affinity",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases max mana by 10%"
        ))
        
        die.add_face(DiceFace(
            name="Arcane Insight",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases spell critical chance by 5%"
        ))
        
        die.add_face(DiceFace(
            name="Physical Frailty",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases max health by 5%"
        ))
        
        die.add_face(DiceFace(
            name="Clumsy",
            value=-2,
            category=FaceCategory.TRAIT,
            effect_description="Decreases dodge by 8%"
        ))
        
        die.add_face(DiceFace(
            name="Magically Focused",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases physical damage by 1"
        ))
        
        return die
    
    @staticmethod
    def _create_rogue_character_die() -> Dice:
        """
        Create a character die for a rogue.
        """
        die = Dice(
            name="Shadow Step",
            dice_type=DiceType.CHARACTER,
            size=6,
            rarity=Rarity.COMMON,
            description="A balanced character die representing a rogue's core attributes."
        )
        
        # Add faces with balanced positive and negative traits
        die.add_face(DiceFace(
            name="Agility",
            value=2,
            category=FaceCategory.TRAIT,
            effect_description="Increases dodge by 8% and speed by 1"
        ))
        
        die.add_face(DiceFace(
            name="Precision",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases critical chance by 7%"
        ))
        
        die.add_face(DiceFace(
            name="Stealth",
            value=1,
            category=FaceCategory.TRAIT,
            effect_description="Increases dodge by 5% and crit damage by 10%"
        ))
        
        die.add_face(DiceFace(
            name="Frail Frame",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases max health by 5%"
        ))
        
        die.add_face(DiceFace(
            name="Impulsive",
            value=-2,
            category=FaceCategory.TRAIT,
            effect_description="Decreases resistances by 10%"
        ))
        
        die.add_face(DiceFace(
            name="Untrained Magic",
            value=-1,
            category=FaceCategory.TRAIT,
            effect_description="Decreases magic damage by 1"
        ))
        
        return die
    
    @staticmethod
    def _create_basic_combat_die(character_class: str) -> Dice:
        """
        Create a basic combat die based on character class.
        """
        if character_class.lower() == "warrior":
            die = Dice(
                name="Warrior's Blade",
                dice_type=DiceType.COMBAT,
                size=6,
                rarity=Rarity.COMMON,
                description="A basic combat die for warriors."
            )
            
            die.add_face(DiceFace(
                name="Strike",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="A basic attack"
            ))
            
            die.add_face(DiceFace(
                name="Heavy Strike",
                value=2,
                category=FaceCategory.COMBAT,
                effect_description="A powerful attack that deals extra damage"
            ))
            
            die.add_face(DiceFace(
                name="Block",
                value=-1,
                category=FaceCategory.COMBAT,
                effect_description="Reduce incoming damage"
            ))
            
            die.add_face(DiceFace(
                name="Taunt",
                value=0,
                category=FaceCategory.EFFECT,
                effect_description="Force enemies to attack you"
            ))
            
            die.add_face(DiceFace(
                name="Minor Heal",
                value=1,
                category=FaceCategory.EFFECT,
                effect_description="Restore a small amount of health"
            ))
            
            die.add_face(DiceFace(
                name="Cleave",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="Attack all enemies for reduced damage"
            ))
            
        elif character_class.lower() == "mage":
            die = Dice(
                name="Arcane Staff",
                dice_type=DiceType.COMBAT,
                size=6,
                rarity=Rarity.COMMON,
                description="A basic combat die for mages."
            )
            
            die.add_face(DiceFace(
                name="Magic Bolt",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="A basic magical attack"
            ))
            
            die.add_face(DiceFace(
                name="Fireball",
                value=2,
                category=FaceCategory.COMBAT,
                effect_description="A powerful area attack"
            ))
            
            die.add_face(DiceFace(
                name="Arcane Barrier",
                value=-1,
                category=FaceCategory.COMBAT,
                effect_description="Create a barrier that reduces incoming damage"
            ))
            
            die.add_face(DiceFace(
                name="Frost Nova",
                value=0,
                category=FaceCategory.EFFECT,
                effect_description="Slow all enemies"
            ))
            
            die.add_face(DiceFace(
                name="Mana Surge",
                value=1,
                category=FaceCategory.EFFECT,
                effect_description="Restore a small amount of mana"
            ))
            
            die.add_face(DiceFace(
                name="Magic Missile",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="Attack a single target with multiple small hits"
            ))
            
        else:  # Rogue
            die = Dice(
                name="Rogue's Daggers",
                dice_type=DiceType.COMBAT,
                size=6,
                rarity=Rarity.COMMON,
                description="A basic combat die for rogues."
            )
            
            die.add_face(DiceFace(
                name="Quick Strike",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="A fast attack with high crit chance"
            ))
            
            die.add_face(DiceFace(
                name="Backstab",
                value=2,
                category=FaceCategory.COMBAT,
                effect_description="A powerful attack with very high crit chance"
            ))
            
            die.add_face(DiceFace(
                name="Dodge",
                value=-1,
                category=FaceCategory.COMBAT,
                effect_description="Greatly increase dodge chance for one turn"
            ))
            
            die.add_face(DiceFace(
                name="Poison Blade",
                value=0,
                category=FaceCategory.EFFECT,
                effect_description="Apply poison to the target"
            ))
            
            die.add_face(DiceFace(
                name="Shadow Step",
                value=1,
                category=FaceCategory.EFFECT,
                effect_description="Increase dodge and crit chance"
            ))
            
            die.add_face(DiceFace(
                name="Fan of Knives",
                value=1,
                category=FaceCategory.COMBAT,
                effect_description="Attack all enemies for small damage"
            ))
        
        return die
    
    @staticmethod
    def _create_basic_encounter_die() -> Dice:
        """
        Create a basic encounter die suitable for any character.
        """
        die = Dice(
            name="Adventurer's Luck",
            dice_type=DiceType.ENCOUNTER,
            size=4,
            rarity=Rarity.COMMON,
            description="A basic encounter die for navigating non-combat situations."
        )
        
        die.add_face(DiceFace(
            name="Perception",
            value=1,
            category=FaceCategory.UTILITY,
            effect_description="Notice hidden details or traps"
        ))
        
        die.add_face(DiceFace(
            name="Diplomacy",
            value=1,
            category=FaceCategory.UTILITY,
            effect_description="Convince or persuade others"
        ))
        
        die.add_face(DiceFace(
            name="Lore",
            value=1,
            category=FaceCategory.UTILITY,
            effect_description="Recall useful knowledge"
        ))
        
        die.add_face(DiceFace(
            name="Luck",
            value=1,
            category=FaceCategory.UTILITY,
            effect_description="Improve chances of favorable outcomes"
        ))
        
        return die


class GameInstance:
    """
    Main game instance that manages the game state and mechanics.
    """
    def __init__(self, config=None):
        self.config = config or {}
        self.state = None
        self.combat_system = CombatSystem()
    
    def new_game(self, player_name: str, character_class: str) -> bool:
        """
        Start a new game with a new character.
        """
        try:
            # Create dice set based on character class
            dice_set = DiceManager.create_starter_dice(character_class)
            
            # Create character
            stats = CharacterStats()
            player = Character(
                name=player_name,
                stats=stats,
                dice_set=dice_set,
                character_class=character_class
            )
            
            # Apply class-specific stat modifications
            if character_class.lower() == "warrior":
                player.stats.max_health += 20
                player.stats.health += 20
                player.stats.physical_damage += 2
            elif character_class.lower() == "mage":
                player.stats.max_mana += 20
                player.stats.mana += 20
                player.stats.magic_damage += 2
            elif character_class.lower() == "rogue":
                player.stats.speed += 2
                player.stats.dodge += 0.05
                player.stats.crit_chance += 0.05
            
            # Create inventory with starting items
            inventory = Inventory(max_size=self.config.get("game", {}).get("inventory_size", 20))
            inventory.add_gold(self.config.get("game", {}).get("starting_gold", 50))
            
            # Add starter items
            item_factory = ItemFactory()
            inventory.add_item(item_factory.create_healing_potion(tier=1))
            inventory.add_item(item_factory.create_mana_potion(tier=1))
            
            # Generate first floor
            floor = DungeonGenerator.generate_floor(1)
            
            # Create game state
            self.state = GameState(
                player=player,
                inventory=inventory,
                current_floor=floor,
                floors=[floor],
                floor_level=1
            )
            
            logger.info(f"New game started with {player_name} the {character_class}")
            return True
        
        except Exception as e:
            logger.error(f"Error creating new game: {e}")
            return False
    
    def save_game(self, filename: str) -> bool:
        """
        Save the current game state to a file.
        """
        if not self.state:
            logger.error("No game state to save")
            return False
        
        try:
            # Create directory if it doesn't exist
            save_dir = self.config.get("save_dir", "saves")
            os.makedirs(save_dir, exist_ok=True)
            
            # Create full path
            filepath = os.path.join(save_dir, filename)
            if not filepath.endswith(".json"):
                filepath += ".json"
            
            # Convert state to dictionary
            state_dict = self.state.to_dict()
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump(state_dict, f, indent=2)
            
            logger.info(f"Game saved to {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving game: {e}")
            return False
    
    def load_game(self, filename: str) -> bool:
        """
        Load a game state from a file.
        """
        try:
            # Get full path
            save_dir = self.config.get("save_dir", "saves")
            filepath = os.path.join(save_dir, filename)
            if not filepath.endswith(".json"):
                filepath += ".json"
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.error(f"Save file not found: {filepath}")
                return False
            
            # Load from file
            with open(filepath, 'r') as f:
                state_dict = json.load(f)
            
            # Create state from dictionary
            self.state = GameState.from_dict(state_dict)
            
            logger.info(f"Game loaded from {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading game: {e}")
            return False
    
    def handle_room(self) -> Dict[str, Any]:
        """
        Handle the current room and return information about it.
        """
        if not self.state or not self.state.current_floor:
            return {"error": "No active game"}
        
        # Get current room
        room = self.state.current_floor.get_current_room()
        
        # Mark as visited if not already
        if not room.visited:
            room.visited = True
        
        # Handle room based on type
        if room.room_type == RoomType.COMBAT or room.room_type == RoomType.ELITE:
            # Start combat if enemies are present and not already in combat
            if room.enemies and not self.state.in_combat:
                self.state.in_combat = True
                self.state.combat_enemies = room.enemies
                self.combat_system.start_combat(self.state.player, room.enemies)
        
        elif room.room_type == RoomType.BOSS:
            # Start boss combat
            if room.enemies and not self.state.in_combat:
                self.state.in_combat = True
                self.state.combat_enemies = room.enemies
                self.combat_system.start_combat(self.state.player, room.enemies)
        
        elif room.room_type == RoomType.TREASURE:
            # Collect treasure if not already collected
            if room.items or room.gold > 0:
                # Add gold to inventory
                self.state.inventory.add_gold(room.gold)
                room.gold = 0
                
                # Add items to inventory
                for item in room.items[:]:
                    if not self.state.inventory.is_full():
                        self.state.inventory.add_item(item)
                        room.items.remove(item)
        
        elif room.room_type == RoomType.EXIT:
            # Check if this is the final floor
            if self.state.floor_level >= 9:  # Assuming 9 is the final level
                self.state.victory = True
                self.state.game_over = True
            else:
                # Generate next floor
                self.state.floor_level += 1
                next_floor = DungeonGenerator.generate_floor(self.state.floor_level)
                self.state.floors.append(next_floor)
                self.state.current_floor = next_floor
        
        # Return room information
        return {
            "room_type": room.room_type.name,
            "name": room.name,
            "description": room.description,
            "visited": room.visited,
            "enemies": [{"name": e.name, "health": e.health, "max_health": e.max_health} for e in room.enemies],
            "items": [{"name": i.name, "description": i.description} for i in room.items],
            "gold": room.gold,
            "event": {"name": room.event.name, "description": room.event.description, "choices": room.event.choices} if room.event else None,
            "in_combat": self.state.in_combat,
            "paths": [(index, r.name, r.room_type.name) for index, r in self.state.current_floor.get_available_paths()]
        }
    
    def handle_combat_turn(self, dice_type: DiceType, dice_index: int, target_index: int = 0) -> Dict[str, Any]:
        """
        Handle a player's combat turn and return the result.
        """
        if not self.state or not self.state.in_combat:
            return {"error": "Not in combat"}
        
        # Execute player turn
        result = self.combat_system.player_turn(
            self.state.player, 
            self.state.combat_enemies, 
            dice_type, 
            dice_index, 
            target_index
        )
        
        # Check if target was defeated
        if result.target_defeated:
            # Remove defeated enemy
            defeated_enemy = self.state.combat_enemies.pop(target_index)
            
            # Add rewards
            self.state.inventory.add_gold(defeated_enemy.gold_reward)
            self.state.player.add_xp(defeated_enemy.xp_reward)
            
            # Check if all enemies are defeated
            if not self.state.combat_enemies:
                self.state.in_combat = False
                return {
                    "success": True,
                    "message": result.message,
                    "combat_over": True,
                    "gold_reward": defeated_enemy.gold_reward,
                    "xp_reward": defeated_enemy.xp_reward
                }
        
        # If combat continues, process enemy turns
        enemy_results = []
        for enemy in self.state.combat_enemies:
            enemy_result = self.combat_system.enemy_turn(enemy, self.state.player)
            enemy_results.append({
                "enemy_name": enemy.name,
                "message": enemy_result.message,
                "damage_dealt": enemy_result.damage_dealt
            })
            
            # Check if player was defeated
            if enemy_result.target_defeated:
                self.state.game_over = True
                self.state.in_combat = False
                return {
                    "success": True,
                    "message": result.message,
                    "enemy_turns": enemy_results,
                    "combat_over": True,
                    "player_defeated": True
                }
        
        # Return combat results
        return {
            "success": result.success,
            "message": result.message,
            "damage_dealt": result.damage_dealt,
            "healing_done": result.healing_done,
            "enemy_turns": enemy_results,
            "combat_log": self.combat_system.log.get_last_entries()
        }
    
    def handle_event(self, choice_index: int) -> Dict[str, Any]:
        """
        Handle an event choice and return the result.
        """
        if not self.state:
            return {"error": "No active game"}
        
        room = self.state.current_floor.get_current_room()
        
        if not room.event:
            return {"error": "No event in current room"}
        
        if choice_index < 0 or choice_index >= len(room.event.choices):
            return {"error": "Invalid choice index"}
        
        # Get the outcome
        outcome = room.event.outcomes[choice_index]
        
        # Apply effects based on the choice
        # This is where you would implement the actual gameplay effects
        # For now, just return the outcome text
        
        return {
            "success": True,
            "message": outcome,
            "event_resolved": True
        }
    
    def handle_rest(self) -> Dict[str, Any]:
        """
        Handle resting at a rest site.
        """
        if not self.state:
            return {"error": "No active game"}
        
        room = self.state.current_floor.get_current_room()
        
        if room.room_type != RoomType.REST:
            return {"error": "Not at a rest site"}
        
        # Heal the player
        heal_percent = 0.3  # Heal 30% of max health
        old_health = self.state.player.stats.health
        max_health = self.state.player.stats.max_health
        
        heal_amount = int(max_health * heal_percent)
        self.state.player.stats.health = min(old_health + heal_amount, max_health)
        actual_heal = self.state.player.stats.health - old_health
        
        # Restore mana
        mana_percent = 0.5  # Restore 50% of max mana
        old_mana = self.state.player.stats.mana
        max_mana = self.state.player.stats.max_mana
        
        mana_amount = int(max_mana * mana_percent)
        self.state.player.stats.mana = min(old_mana + mana_amount, max_mana)
        actual_mana = self.state.player.stats.mana - old_mana
        
        # Clear negative status effects
        cleared_effects = []
        for effect in list(self.state.player.stats.status_effects.keys()):
            if effect in ["Bleeding", "Poisoned", "Cursed"]:
                cleared_effects.append(effect)
                del self.state.player.stats.status_effects[effect]
        
        # Reset dice cooldowns
        for dice_type in DiceType:
            dice_list = self.state.player.dice_set.get_dice_list(dice_type)
            for die in dice_list:
                die.cooldown = 0
        
        return {
            "success": True,
            "health_restored": actual_heal,
            "mana_restored": actual_mana,
            "cleared_effects": cleared_effects,
            "message": f"Rested and recovered {actual_heal} health and {actual_mana} mana."
        }
    
    def handle_shop(self, action: str, item_index: int = None) -> Dict[str, Any]:
        """
        Handle shop interactions.
        """
        if not self.state:
            return {"error": "No active game"}
        
        room = self.state.current_floor.get_current_room()
        
        if room.room_type != RoomType.SHOP:
            return {"error": "Not at a shop"}
        
        if action == "browse":
            # Return list of items for sale
            return {
                "success": True,
                "gold": self.state.inventory.gold,
                "items": [{"name": i.name, "description": i.description, "effect": i.effect, "value": i.value, "rarity": i.rarity.name} for i in room.items]
            }
        
        elif action == "buy":
            if item_index is None or item_index < 0 or item_index >= len(room.items):
                return {"error": "Invalid item index"}
            
            item = room.items[item_index]
            
            # Check if player has enough gold
            if self.state.inventory.gold < item.value:
                return {"error": "Not enough gold", "required": item.value, "available": self.state.inventory.gold}
            
            # Check if inventory has space
            if self.state.inventory.is_full():
                return {"error": "Inventory is full"}
            
            # Purchase the item
            self.state.inventory.remove_gold(item.value)
            self.state.inventory.add_item(item)
            room.items.pop(item_index)
            
            return {
                "success": True,
                "message": f"Purchased {item.name} for {item.value} gold.",
                "remaining_gold": self.state.inventory.gold
            }
        
        else:
            return {"error": "Invalid shop action"}
    
    def handle_inventory(self, action: str, item_index: int = None) -> Dict[str, Any]:
        """
        Handle inventory interactions.
        """
        if not self.state:
            return {"error": "No active game"}
        
        if action == "view":
            # Return inventory contents
            return {
                "success": True,
                "gold": self.state.inventory.gold,
                "items": [{"name": i.name, "description": i.description, "effect": i.effect} for i in self.state.inventory.items],
                "capacity": f"{len(self.state.inventory.items)}/{self.state.inventory.max_size}"
            }
        
        elif action == "use":
            if item_index is None or item_index < 0 or item_index >= len(self.state.inventory.items):
                return {"error": "Invalid item index"}
            
            item = self.state.inventory.items[item_index]
            
            # Apply item effect
            if "Healing" in item.name:
                # Healing potion
                tier = 3 if "Major" in item.name else (2 if "Minor" not in item.name else 1)
                heal_amount = 20 * tier
                
                old_health = self.state.player.stats.health
                self.state.player.stats.health = min(old_health + heal_amount, self.state.player.stats.max_health)
                actual_heal = self.state.player.stats.health - old_health
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and restored {actual_heal} health.",
                    "health_restored": actual_heal
                }
            
            elif "Mana" in item.name:
                # Mana potion
                tier = 3 if "Major" in item.name else (2 if "Minor" not in item.name else 1)
                mana_amount = 10 * tier
                
                old_mana = self.state.player.stats.mana
                self.state.player.stats.mana = min(old_mana + mana_amount, self.state.player.stats.max_mana)
                actual_mana = self.state.player.stats.mana - old_mana
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and restored {actual_mana} mana.",
                    "mana_restored": actual_mana
                }
            
            elif "Strength" in item.name:
                # Strength boost
                boost = 2 if "Minor" not in item.name else 1
                self.state.player.stats.physical_damage += boost
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and permanently increased physical damage by {boost}.",
                    "stat_boosted": "physical_damage",
                    "boost_amount": boost
                }
            
            elif "Intelligence" in item.name:
                # Intelligence boost
                boost = 2 if "Minor" not in item.name else 1
                self.state.player.stats.magic_damage += boost
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and permanently increased magic damage by {boost}.",
                    "stat_boosted": "magic_damage",
                    "boost_amount": boost
                }
            
            elif "Vitality" in item.name:
                # Vitality boost
                boost_percent = 20 if "Minor" not in item.name else 10
                health_boost = int(self.state.player.stats.max_health * boost_percent / 100)
                
                self.state.player.stats.max_health += health_boost
                self.state.player.stats.health += health_boost
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and permanently increased max health by {health_boost}.",
                    "stat_boosted": "max_health",
                    "boost_amount": health_boost
                }
            
            elif "Agility" in item.name:
                # Agility boost
                speed_boost = 2 if "Minor" not in item.name else 1
                dodge_boost = 0.04 if "Minor" not in item.name else 0.02
                
                self.state.player.stats.speed += speed_boost
                self.state.player.stats.dodge += dodge_boost
                
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name} and permanently increased speed by {speed_boost} and dodge by {dodge_boost:.0%}.",
                    "stats_boosted": ["speed", "dodge"],
                    "boost_amounts": [speed_boost, dodge_boost]
                }
            
            else:
                # Generic item handling
                # Remove the item
                self.state.inventory.remove_item(item_index)
                
                return {
                    "success": True,
                    "message": f"Used {item.name}. {item.effect}"
                }
        
        elif action == "drop":
            if item_index is None or item_index < 0 or item_index >= len(self.state.inventory.items):
                return {"error": "Invalid item index"}
            
            item = self.state.inventory.items[item_index]
            self.state.inventory.remove_item(item_index)
            
            return {
                "success": True,
                "message": f"Dropped {item.name}."
            }
        
        else:
            return {"error": "Invalid inventory action"}
    
    def handle_navigation(self, room_index: int) -> Dict[str, Any]:
        """
        Handle navigation between rooms.
        """
        if not self.state:
            return {"error": "No active game"}
        
        # Check if in combat
        if self.state.in_combat:
            return {"error": "Cannot navigate while in combat"}
        
        # Get available paths
        available_paths = self.state.current_floor.get_available_paths()
        available_indices = [index for index, _ in available_paths]
        
        # Check if the target room is valid
        if room_index not in available_indices:
            return {"error": "Invalid room destination"}
        
        # Move to the selected room
        self.state.current_floor.move_to_room(room_index)
        
        # Return information about the new room
        return self.handle_room()
    
    def get_player_info(self) -> Dict[str, Any]:
        """
        Get information about the player.
        """
        if not self.state:
            return {"error": "No active game"}
        
        player = self.state.player
        stats = player.stats
        
        return {
            "name": player.name,
            "class": player.character_class,
            "level": player.level,
            "xp": player.xp,
            "xp_to_next_level": player.xp_to_next_level,
            "health": stats.health,
            "max_health": stats.max_health,
            "mana": stats.mana,
            "max_mana": stats.max_mana,
            "physical_damage": stats.physical_damage,
            "magic_damage": stats.magic_damage,
            "speed": stats.speed,
            "dodge": stats.dodge,
            "crit_chance": stats.crit_chance,
            "crit_damage": stats.crit_damage,
            "resistances": stats.resistances,
            "status_effects": [{"name": effect, "turns": turns} for effect, turns in stats.status_effects.items()],
            "passive_bonuses": [{"name": bonus, "value": value} for bonus, value in stats.passive_bonuses.items()],
            "active_faces": player.active_faces
        }
    
    def get_dice_info(self) -> Dict[str, Any]:
        """
        Get information about the player's dice.
        """
        if not self.state:
            return {"error": "No active game"}
        
        dice_set = self.state.player.dice_set
        result = {}
        
        for dice_type in DiceType:
            dice_list = dice_set.get_dice_list(dice_type)
            if dice_list:
                result[dice_type.name] = []
                
                for die in dice_list:
                    die_info = {
                        "name": die.name,
                        "size": die.size,
                        "level": die.level,
                        "rarity": die.rarity.name,
                        "description": die.description,
                        "balance": die.balance_value,
                        "imbalance_effect": die.imbalance_effect.name,
                        "imbalance_severity": die.imbalance_severity,
                        "cooldown": die.cooldown,
                        "faces": []
                    }
                    
                    for face in die.faces:
                        face_info = {
                            "name": face.name,
                            "value": face.value,
                            "category": face.category.name,
                            "description": face.effect_description,
                            "rarity": face.rarity.name
                        }
                        
                        if face.cost:
                            face_info["cost"] = face.cost
                            
                        if face.synergies:
                            face_info["synergies"] = face.synergies
                            
                        die_info["faces"].append(face_info)
                    
                    result[dice_type.name].append(die_info)
        
        return result
    
    def get_dungeon_info(self) -> Dict[str, Any]:
        """
        Get information about the current dungeon.
        """
        if not self.state:
            return {"error": "No active game"}
        
        floor = self.state.current_floor
        room = floor.get_current_room()
        
        return {
            "floor_level": self.state.floor_level,
            "current_room_index": floor.current_room_index,
            "current_room": {
                "name": room.name,
                "type": room.room_type.name,
                "description": room.description,
                "visited": room.visited
            },
            "room_count": len(floor.rooms),
            "completed_rooms": sum(1 for r in floor.rooms if r.visited),
            "available_paths": [(index, r.name, r.room_type.name) for index, r in floor.get_available_paths()]
        }
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Get a summary of the current game state.
        """
        if not self.state:
            return {"error": "No active game"}
        
        return {
            "player": {
                "name": self.state.player.name,
                "class": self.state.player.character_class,
                "level": self.state.player.level,
                "health": f"{self.state.player.stats.health}/{self.state.player.stats.max_health}"
            },
            "floor_level": self.state.floor_level,
            "in_combat": self.state.in_combat,
            "game_over": self.state.game_over,
            "victory": self.state.victory,
            "gold": self.state.inventory.gold,
            "inventory_count": f"{len(self.state.inventory.items)}/{self.state.inventory.max_size}"
        }