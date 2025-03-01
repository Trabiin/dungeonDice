"""
Combat system implementation
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from core.character import Character, CharacterStats
from core.dice import DiceFace
from core.enums import DiceType, FaceCategory
from game.dungeon import Enemy


@dataclass
class CombatAction:
    """
    Represents an action in combat.
    """
    name: str
    description: str
    damage: int = 0
    healing: int = 0
    status_effect: Optional[Tuple[str, int]] = None  # (effect_name, duration)
    target_type: str = "enemy"  # "enemy", "self", "all_enemies"
    dice_face: Optional[DiceFace] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "name": self.name,
            "description": self.description,
            "damage": self.damage,
            "healing": self.healing,
            "target_type": self.target_type
        }
        
        if self.status_effect:
            result["status_effect"] = {
                "name": self.status_effect[0],
                "duration": self.status_effect[1]
            }
            
        if self.dice_face:
            result["dice_face"] = self.dice_face.to_dict()
            
        return result


@dataclass
class CombatResult:
    """
    Represents the result of a combat action.
    """
    success: bool
    message: str
    damage_dealt: int = 0
    healing_done: int = 0
    status_applied: Optional[str] = None
    target_defeated: bool = False
    

@dataclass
class CombatLog:
    """
    Maintains a log of combat actions and results.
    """
    entries: List[str] = field(default_factory=list)
    
    def add_entry(self, entry: str) -> None:
        """Add an entry to the combat log."""
        self.entries.append(entry)
    
    def get_last_entries(self, count: int = 5) -> List[str]:
        """Get the last N entries from the combat log."""
        return self.entries[-count:]
    
    def clear(self) -> None:
        """Clear the combat log."""
        self.entries = []


class CombatSystem:
    """
    Handles combat mechanics between the player and enemies.
    """
    def __init__(self):
        self.log = CombatLog()
    
    def start_combat(self, player: Character, enemies: List[Enemy]) -> None:
        """
        Initialize a new combat session.
        """
        self.log.clear()
        self.log.add_entry(f"Combat started against {len(enemies)} enemies!")
        
        for enemy in enemies:
            self.log.add_entry(f"- {enemy.name} (Level {enemy.level}) with {enemy.health} health")
    
    def player_turn(self, player: Character, enemies: List[Enemy], dice_type: DiceType, 
                    dice_index: int, target_index: int = 0) -> CombatResult:
        """
        Execute the player's turn in combat.
        """
        # Check if target is valid
        if not enemies or target_index < 0 or target_index >= len(enemies):
            return CombatResult(
                success=False,
                message="Invalid target!"
            )
        
        # Roll the selected die
        roll_result, message = player.roll_die(dice_type, dice_index)
        
        if not roll_result:
            self.log.add_entry(f"Player rolled but got no result: {message}")
            return CombatResult(
                success=False,
                message=message
            )
        
        # Process the roll result
        target = enemies[target_index]
        return self._process_player_action(player, target, roll_result)
    
    def _process_player_action(self, player: Character, target: Enemy, roll_result: Dict[str, Any]) -> CombatResult:
        """
        Process the player's action based on the dice roll result.
        """
        face_name = roll_result["name"]
        face_category = roll_result["category"]
        face_value = roll_result["value"]
        
        # Handle different face categories
        if face_category == "COMBAT":
            return self._handle_combat_face(player, target, face_name, face_value)
        elif face_category == "EFFECT":
            return self._handle_effect_face(player, target, face_name, face_value)
        else:
            # For other face types, just log the effect
            self.log.add_entry(f"Player used {face_name}: {roll_result['description']}")
            return CombatResult(
                success=True,
                message=f"Used {face_name}"
            )
    
    def _handle_combat_face(self, player: Character, target: Enemy, face_name: str, face_value: int) -> CombatResult:
        """
        Handle a combat face result.
        """
        # Calculate damage based on face value and player stats
        base_damage = player.stats.physical_damage
        
        # Modify damage based on face name
        if "Heavy" in face_name:
            damage_multiplier = 1.5
        elif "Quick" in face_name:
            damage_multiplier = 0.8
        else:
            damage_multiplier = 1.0
        
        # Apply face value as a modifier
        damage = int(base_damage * damage_multiplier) + face_value
        
        # Check for critical hit
        is_critical = random.random() < player.stats.crit_chance
        if is_critical:
            damage = int(damage * player.stats.crit_damage)
        
        # Apply damage to target
        target.health -= damage
        
        # Check if target is defeated
        target_defeated = target.health <= 0
        if target_defeated:
            target.health = 0
            
        # Create result message
        if is_critical:
            message = f"CRITICAL HIT! {face_name} deals {damage} damage to {target.name}!"
        else:
            message = f"{face_name} deals {damage} damage to {target.name}!"
            
        if target_defeated:
            message += f" {target.name} is defeated!"
            
        self.log.add_entry(message)
        
        return CombatResult(
            success=True,
            message=message,
            damage_dealt=damage,
            target_defeated=target_defeated
        )
    
    def _handle_effect_face(self, player: Character, target: Enemy, face_name: str, face_value: int) -> CombatResult:
        """
        Handle an effect face result.
        """
        # Handle different effect types
        if "Heal" in face_name:
            return self._handle_healing(player, face_name, face_value)
        elif "Bleed" in face_name:
            return self._handle_status_effect(target, "Bleeding", 3, face_name)
        elif "Poison" in face_name:
            return self._handle_status_effect(target, "Poisoned", 3, face_name)
        elif "Stun" in face_name:
            return self._handle_status_effect(target, "Stunned", 1, face_name)
        else:
            # Generic effect
            self.log.add_entry(f"Player used {face_name} effect")
            return CombatResult(
                success=True,
                message=f"Used {face_name} effect"
            )
    
    def _handle_healing(self, player: Character, face_name: str, face_value: int) -> CombatResult:
        """
        Handle a healing effect.
        """
        # Calculate healing amount
        if "Major" in face_name:
            heal_amount = 30 + face_value * 2
        else:
            heal_amount = 15 + face_value
            
        # Apply healing
        old_health = player.stats.health
        player.stats.health = min(player.stats.health + heal_amount, player.stats.max_health)
        actual_heal = player.stats.health - old_health
        
        message = f"{face_name} restores {actual_heal} health"
        self.log.add_entry(message)
        
        return CombatResult(
            success=True,
            message=message,
            healing_done=actual_heal
        )
    
    def _handle_status_effect(self, target: Enemy, effect: str, duration: int, face_name: str) -> CombatResult:
        """
        Apply a status effect to the target.
        """
        # Apply status effect
        # In a real implementation, you would update the target's status effects
        
        message = f"{face_name} applies {effect} to {target.name} for {duration} turns"
        self.log.add_entry(message)
        
        return CombatResult(
            success=True,
            message=message,
            status_applied=effect
        )
    
    def enemy_turn(self, enemy: Enemy, player: Character) -> CombatResult:
        """
        Execute an enemy's turn in combat.
        """
        # Check if enemy can act (not stunned, etc.)
        # In a real implementation, you would check enemy status effects
        
        # Calculate damage based on enemy stats
        damage = enemy.damage
        
        # Apply random variance
        damage = int(damage * random.uniform(0.8, 1.2))
        
        # Check for dodge
        if random.random() < player.stats.dodge:
            message = f"{enemy.name} attacks but {player.name} dodges!"
            self.log.add_entry(message)
            return CombatResult(
                success=False,
                message=message
            )
        
        # Apply damage to player
        player.stats.health -= damage
        
        # Check if player is defeated
        player_defeated = player.stats.health <= 0
        if player_defeated:
            player.stats.health = 0
            message = f"{enemy.name} attacks for {damage} damage! {player.name} is defeated!"
        else:
            message = f"{enemy.name} attacks for {damage} damage!"
            
        self.log.add_entry(message)
        
        return CombatResult(
            success=True,
            message=message,
            damage_dealt=damage,
            target_defeated=player_defeated
        )
    
    def process_combat_rewards(self, player: Character, defeated_enemies: List[Enemy]) -> Tuple[int, int]:
        """
        Process rewards from defeating enemies.
        Returns a tuple of (gold_gained, xp_gained).
        """
        total_gold = 0
        total_xp = 0
        
        for enemy in defeated_enemies:
            total_gold += enemy.gold_reward
            total_xp += enemy.xp_reward
            
        # Apply XP to player
        player.add_xp(total_xp)
        
        self.log.add_entry(f"Combat rewards: {total_gold} gold and {total_xp} XP")
        
        return total_gold, total_xp