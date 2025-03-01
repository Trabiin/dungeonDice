"""
Enemy AI system for the dice-based roguelike RPG
"""

import random
from typing import Dict, List, Optional, Tuple, Any, Callable
import logging
from core.enums import DiceType, FaceCategory, EnemyType
from core.character import Character, CharacterStats
from game.dungeon import Enemy

logger = logging.getLogger(__name__)


class AIBehavior:
    """
    Base class for enemy AI behaviors.
    """
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """
        Decide which action the enemy should take.
        
        Args:
            enemy: The enemy taking the action
            player: The player character
            enemy_dice: List of (dice_type, dice_index, dice_info) tuples representing available dice
            
        Returns:
            Tuple of (selected_dice_type, selected_dice_index)
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def select_target(self, enemy: Enemy, player: Character) -> int:
        """
        Select a target for the enemy's action.
        In the current implementation, there's only one target (the player),
        but this could be extended for multiple targets.
        
        Args:
            enemy: The enemy selecting the target
            player: The player character
            
        Returns:
            Target index (always 0 in the current implementation)
        """
        return 0  # Only one target in the current implementation


class RandomBehavior(AIBehavior):
    """
    Simple AI that selects actions randomly.
    """
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """Randomly select an available die."""
        if not enemy_dice:
            logger.warning(f"{enemy.name} has no available dice!")
            # Return a default value even though it won't be used
            return (DiceType.COMBAT, 0)
        
        selected = random.choice(enemy_dice)
        return (selected[0], selected[1])


class AggressiveBehavior(AIBehavior):
    """
    Aggressive AI that prioritizes attack actions.
    """
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """Prioritize attack dice, especially powerful attacks."""
        if not enemy_dice:
            logger.warning(f"{enemy.name} has no available dice!")
            return (DiceType.COMBAT, 0)
        
        # First, look for combat dice with attack faces
        attack_dice = []
        for dice_type, dice_index, dice_info in enemy_dice:
            if dice_type == DiceType.COMBAT:
                # Check if this die has attack faces
                attack_faces = [face for face in dice_info['faces'] 
                               if face['category'] == 'COMBAT' and 'Attack' in face['name']]
                if attack_faces:
                    # Calculate an "attack score" based on attack faces and their values
                    attack_score = sum(face['value'] for face in attack_faces if face['value'] > 0)
                    attack_dice.append((dice_type, dice_index, attack_score))
        
        # If there are attack dice, choose the one with the highest attack score
        if attack_dice:
            attack_dice.sort(key=lambda x: x[2], reverse=True)
            return (attack_dice[0][0], attack_dice[0][1])
        
        # If no attack dice, fall back to any combat dice
        combat_dice = [d for d in enemy_dice if d[0] == DiceType.COMBAT]
        if combat_dice:
            return (combat_dice[0][0], combat_dice[0][1])
        
        # If no combat dice, choose randomly
        selected = random.choice(enemy_dice)
        return (selected[0], selected[1])


class DefensiveBehavior(AIBehavior):
    """
    Defensive AI that prioritizes defense when health is low.
    """
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """Prioritize defensive actions when health is low."""
        if not enemy_dice:
            logger.warning(f"{enemy.name} has no available dice!")
            return (DiceType.COMBAT, 0)
        
        # Calculate health percentage
        health_percentage = enemy.health / enemy.max_health
        
        # If health is low (below 30%), prioritize defense or healing
        if health_percentage < 0.3:
            # Look for healing or defensive dice
            for dice_type, dice_index, dice_info in enemy_dice:
                # Check if this die has healing faces
                healing_faces = [face for face in dice_info['faces'] 
                                if 'Heal' in face['name'] or 'Defense' in face['name'] or 'Block' in face['name']]
                if healing_faces:
                    return (dice_type, dice_index)
        
        # If health is moderate (below 60%), balance attack and defense
        elif health_percentage < 0.6:
            # Choose randomly between attack and defense
            combat_dice = [d for d in enemy_dice if d[0] == DiceType.COMBAT]
            if combat_dice:
                return (combat_dice[0][0], combat_dice[0][1])
        
        # If health is high, behave aggressively
        return AggressiveBehavior().decide_action(enemy, player, enemy_dice)


class TacticalBehavior(AIBehavior):
    """
    Tactical AI that adapts its strategy based on the situation.
    """
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """Adapt strategy based on situation."""
        if not enemy_dice:
            logger.warning(f"{enemy.name} has no available dice!")
            return (DiceType.COMBAT, 0)
        
        # Calculate health percentages
        enemy_health_percentage = enemy.health / enemy.max_health
        player_health_percentage = player.stats.health / player.stats.max_health
        
        # If enemy has much more health than player, be aggressive
        if enemy_health_percentage > player_health_percentage + 0.3:
            return AggressiveBehavior().decide_action(enemy, player, enemy_dice)
        
        # If enemy has much less health than player, be defensive
        elif enemy_health_percentage < player_health_percentage - 0.3:
            return DefensiveBehavior().decide_action(enemy, player, enemy_dice)
        
        # If health is similar, use a mixed strategy
        else:
            # Prioritize status effect dice if available
            status_dice = []
            for dice_type, dice_index, dice_info in enemy_dice:
                effect_faces = [face for face in dice_info['faces'] 
                               if face['category'] == 'EFFECT']
                if effect_faces:
                    status_dice.append((dice_type, dice_index))
            
            if status_dice and random.random() < 0.6:  # 60% chance to use status effect
                return random.choice(status_dice)
            
            # Otherwise, choose randomly between attack and defense
            return random.choice([
                AggressiveBehavior().decide_action(enemy, player, enemy_dice),
                DefensiveBehavior().decide_action(enemy, player, enemy_dice)
            ])


class BossBehavior(AIBehavior):
    """
    Advanced AI for boss enemies with multiple phases.
    """
    def __init__(self):
        self.turn_count = 0
        self.phase = 1
        self.phase_abilities_used = set()
    
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """Complex boss behavior with phases based on health thresholds."""
        if not enemy_dice:
            logger.warning(f"{enemy.name} has no available dice!")
            return (DiceType.COMBAT, 0)
        
        self.turn_count += 1
        
        # Calculate health percentage to determine phase
        health_percentage = enemy.health / enemy.max_health
        
        # Update phase based on health
        if health_percentage < 0.3:
            new_phase = 3  # Desperate phase
        elif health_percentage < 0.6:
            new_phase = 2  # Wounded phase
        else:
            new_phase = 1  # Normal phase
        
        # If phase changed, reset used abilities tracking
        if new_phase != self.phase:
            self.phase = new_phase
            self.phase_abilities_used = set()
            logger.info(f"{enemy.name} enters phase {self.phase}!")
        
        # Special abilities for each phase
        if self.phase == 3:  # Desperate phase - powerful attacks
            # Look for ultimate ability
            for dice_type, dice_index, dice_info in enemy_dice:
                for i, face in enumerate(dice_info['faces']):
                    if 'Ultimate' in face['name'] and face['value'] >= 4:
                        key = f"{dice_type}_{dice_index}_ultimate"
                        if key not in self.phase_abilities_used:
                            self.phase_abilities_used.add(key)
                            return (dice_type, dice_index)
        
        elif self.phase == 2:  # Wounded phase - mix of healing and attacks
            # Try to heal if not done recently
            heal_key = "phase2_heal"
            if heal_key not in self.phase_abilities_used:
                for dice_type, dice_index, dice_info in enemy_dice:
                    healing_faces = [face for face in dice_info['faces'] if 'Heal' in face['name']]
                    if healing_faces:
                        self.phase_abilities_used.add(heal_key)
                        return (dice_type, dice_index)
        
        # Every few turns, try a special attack if available
        if self.turn_count % 3 == 0:
            for dice_type, dice_index, dice_info in enemy_dice:
                if dice_type == DiceType.SPECIAL:
                    return (dice_type, dice_index)
        
        # Default to tactical behavior
        return TacticalBehavior().decide_action(enemy, player, enemy_dice)


class EnemyAI:
    """
    Main class for managing enemy AI behaviors.
    """
    def __init__(self):
        """Initialize the AI system with default behaviors."""
        self.behaviors: Dict[str, AIBehavior] = {
            "random": RandomBehavior(),
            "aggressive": AggressiveBehavior(),
            "defensive": DefensiveBehavior(),
            "tactical": TacticalBehavior(),
            "boss": BossBehavior(),
        }
        
        # Map enemy types to default behaviors
        self.enemy_type_behaviors: Dict[EnemyType, str] = {
            EnemyType.GOBLIN: "aggressive",
            EnemyType.SKELETON: "random",
            EnemyType.ORC: "aggressive",
            EnemyType.ZOMBIE: "defensive",
            EnemyType.GHOST: "tactical",
            EnemyType.SLIME: "defensive",
            EnemyType.MINOTAUR: "aggressive",
            EnemyType.DRAGON: "boss",
        }
        
        # Store custom behaviors for specific enemies
        self.custom_behaviors: Dict[str, str] = {}
    
    def get_behavior(self, enemy: Enemy) -> AIBehavior:
        """
        Get the appropriate AI behavior for an enemy.
        
        Args:
            enemy: The enemy to get behavior for
            
        Returns:
            AIBehavior instance for the enemy
        """
        # Check for custom behavior by enemy name
        if enemy.name in self.custom_behaviors:
            behavior_key = self.custom_behaviors[enemy.name]
            return self.behaviors[behavior_key]
        
        # Check for boss naming pattern
        if "Boss" in enemy.name or "Lord" in enemy.name or "King" in enemy.name or any(
            name in enemy.name for name in ["Grubnosh", "Bonecrusher", "Grimfang", "Flamescale"]
        ):
            return self.behaviors["boss"]
        
        # Use default behavior based on enemy type
        behavior_key = self.enemy_type_behaviors.get(enemy.enemy_type, "random")
        return self.behaviors[behavior_key]
    
    def decide_action(self, enemy: Enemy, player: Character, enemy_dice: List[Tuple[DiceType, int, Dict]]) -> Tuple[DiceType, int]:
        """
        Decide which action the enemy should take.
        
        Args:
            enemy: The enemy taking the action
            player: The player character
            enemy_dice: List of (dice_type, dice_index, dice_info) tuples representing available dice
            
        Returns:
            Tuple of (selected_dice_type, selected_dice_index)
        """
        behavior = self.get_behavior(enemy)
        return behavior.decide_action(enemy, player, enemy_dice)
    
    def set_custom_behavior(self, enemy_name: str, behavior_key: str) -> bool:
        """
        Set a custom behavior for a specific enemy by name.
        
        Args:
            enemy_name: Name of the enemy
            behavior_key: Key of the behavior to use
            
        Returns:
            True if successful, False if the behavior key is invalid
        """
        if behavior_key not in self.behaviors:
            logger.warning(f"Invalid behavior key: {behavior_key}")
            return False
        
        self.custom_behaviors[enemy_name] = behavior_key
        return True
    
    def register_behavior(self, key: str, behavior: AIBehavior) -> None:
        """
        Register a new AI behavior.
        
        Args:
            key: Key to identify the behavior
            behavior: AIBehavior instance
        """
        self.behaviors[key] = behavior
    
    def set_enemy_type_behavior(self, enemy_type: EnemyType, behavior_key: str) -> bool:
        """
        Set the default behavior for an enemy type.
        
        Args:
            enemy_type: Type of enemy
            behavior_key: Key of the behavior to use
            
        Returns:
            True if successful, False if the behavior key is invalid
        """
        if behavior_key not in self.behaviors:
            logger.warning(f"Invalid behavior key: {behavior_key}")
            return False
        
        self.enemy_type_behaviors[enemy_type] = behavior_key
        return True


# Create a global instance of EnemyAI for use throughout the game
enemy_ai = EnemyAI()


# Factory function to easily create custom behaviors
def create_custom_behavior(behavior_key: str, decision_function: Callable) -> None:
    """
    Create and register a custom AI behavior.
    
    Args:
        behavior_key: Key to identify the behavior
        decision_function: Function that takes (enemy, player, enemy_dice) and returns (dice_type, dice_index)
    """
    class CustomBehavior(AIBehavior):
        def decide_action(self, enemy, player, enemy_dice):
            return decision_function(enemy, player, enemy_dice)
    
    enemy_ai.register_behavior(behavior_key, CustomBehavior())