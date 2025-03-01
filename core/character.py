"""
Character system implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from core.dice import DiceSet
from core.enums import DiceType, FaceCategory

@dataclass
class CharacterStats:
    """
    Represents the stats for a character.
    """
    health: int = 100
    max_health: int = 100
    mana: int = 50
    max_mana: int = 50
    physical_damage: int = 10
    magic_damage: int = 10
    speed: int = 5
    dodge: float = 0.1
    crit_chance: float = 0.05
    crit_damage: float = 1.5
    resistances: Dict[str, float] = field(default_factory=lambda: {
        "physical": 0.0,
        "magic": 0.0,
        "fire": 0.0,
        "ice": 0.0,
        "poison": 0.0
    })
    status_effects: Dict[str, int] = field(default_factory=dict)
    passive_bonuses: Dict[str, float] = field(default_factory=dict)
    
    def apply_trait(self, name: str, value: int) -> str:
        """Apply a trait modification and return a description of the effect."""
        result = ""
        
        # Handle different traits
        if name == "Strength":
            self.physical_damage += value
            result = f"Physical damage {'increased' if value > 0 else 'decreased'} by {abs(value)}"
        elif name == "Intelligence":
            self.magic_damage += value
            result = f"Magic damage {'increased' if value > 0 else 'decreased'} by {abs(value)}"
        elif name == "Vitality":
            percent = value * 10
            health_change = int(self.max_health * percent / 100)
            self.max_health += health_change
            self.health += health_change
            result = f"Max health {'increased' if value > 0 else 'decreased'} by {abs(percent)}%"
        elif name == "Agility":
            self.speed += value
            self.dodge += value * 0.02
            result = f"Speed {'increased' if value > 0 else 'decreased'} by {abs(value)}"
        elif name in ["Weakness", "Frailty", "Slowness", "Stupidity"]:
            # These are handled by the positive counterparts
            if name == "Weakness":
                self.physical_damage = max(1, self.physical_damage + value)  # value is negative
                result = f"Physical damage decreased by {abs(value)}"
            elif name == "Frailty":
                percent = value * 10  # value is negative
                health_change = int(self.max_health * percent / 100)
                self.max_health = max(1, self.max_health + health_change)
                self.health = min(self.health, self.max_health)
                result = f"Max health decreased by {abs(percent)}%"
            elif name == "Slowness":
                self.speed = max(1, self.speed + value)  # value is negative
                self.dodge = max(0, self.dodge + value * 0.02)  # value is negative
                result = f"Speed decreased by {abs(value)}"
            elif name == "Stupidity":
                self.magic_damage = max(1, self.magic_damage + value)  # value is negative
                result = f"Magic damage decreased by {abs(value)}"
        else:
            # Generic trait handling
            stat_name = name.lower()
            if hasattr(self, stat_name):
                old_value = getattr(self, stat_name)
                setattr(self, stat_name, old_value + value)
                result = f"{name} {'increased' if value > 0 else 'decreased'} by {abs(value)}"
            else:
                # Add as a passive bonus for unknown traits
                self.passive_bonuses[name] = value
                result = f"Added {name} ({value}) as a passive bonus"
        
        return result
    
    def apply_status_effect(self, effect_name: str, duration: int) -> None:
        """Apply a status effect to the character."""
        if effect_name in self.status_effects:
            # Extend the duration if the effect already exists
            self.status_effects[effect_name] = max(self.status_effects[effect_name], duration)
        else:
            # Add the new effect
            self.status_effects[effect_name] = duration
    
    def process_status_effects(self) -> List[str]:
        """
        Process all status effects for one turn and return messages about the effects.
        """
        messages = []
        effects_to_remove = []
        
        for effect, turns in self.status_effects.items():
            # Apply effect based on its type
            if effect == "Bleeding":
                damage = max(1, int(self.max_health * 0.05))
                self.health -= damage
                messages.append(f"Suffered {damage} bleeding damage")
            elif effect == "Poisoned":
                damage = max(1, int(self.max_health * 0.03))
                self.health -= damage
                messages.append(f"Suffered {damage} poison damage")
            elif effect == "Burning":
                damage = max(1, int(self.max_health * 0.07))
                self.health -= damage
                messages.append(f"Suffered {damage} burning damage")
            
            # Decrease remaining duration
            self.status_effects[effect] = turns - 1
            
            # Mark for removal if duration is up
            if self.status_effects[effect] <= 0:
                effects_to_remove.append(effect)
                messages.append(f"{effect} effect has worn off")
        
        # Remove expired effects
        for effect in effects_to_remove:
            del self.status_effects[effect]
        
        return messages
    
    def is_alive(self) -> bool:
        """Check if the character is still alive."""
        return self.health > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "health": self.health,
            "max_health": self.max_health,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "physical_damage": self.physical_damage,
            "magic_damage": self.magic_damage,
            "speed": self.speed,
            "dodge": self.dodge,
            "crit_chance": self.crit_chance,
            "crit_damage": self.crit_damage,
            "resistances": self.resistances,
            "status_effects": self.status_effects,
            "passive_bonuses": self.passive_bonuses
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CharacterStats':
        """Create a CharacterStats from a dictionary."""
        return cls(**data)


@dataclass
class Character:
    """
    Represents a player character in the game.
    """
    name: str
    stats: CharacterStats = field(default_factory=CharacterStats)
    dice_set: DiceSet = field(default_factory=DiceSet)
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100
    active_faces: List[str] = field(default_factory=list)
    character_class: str = "Adventurer"
    
    def add_xp(self, amount: int) -> bool:
        """
        Add XP to the character and level up if necessary.
        Returns True if the character leveled up.
        """
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True
        return False
    
    def level_up(self) -> str:
        """
        Level up the character, improving stats.
        Returns a message describing the level up effects.
        """
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        
        # Improve stats based on level
        health_increase = self.level * 5
        self.stats.max_health += health_increase
        self.stats.health += health_increase
        
        self.stats.max_mana += self.level * 2
        self.stats.mana = self.stats.max_mana
        
        self.stats.physical_damage += 1
        self.stats.magic_damage += 1
        
        if self.level % 3 == 0:
            self.stats.speed += 1
        
        return f"Reached level {self.level}! Health +{health_increase}, damage +1"
    
    def roll_die(self, dice_type: DiceType, index: int) -> Tuple[Optional[dict], str]:
        """
        Roll a specific die and apply the result.
        Returns a tuple with the roll result and a message.
        """
        dice_list = self.dice_set.get_dice_list(dice_type)
        
        if index < 0 or index >= len(dice_list):
            return None, "Invalid die selection"
        
        die = dice_list[index]
        result, message, effects = die.roll()
        
        if result:
            # Apply the effect if applicable
            effect_message = ""
            if result.category == FaceCategory.TRAIT:
                effect_message = self.stats.apply_trait(result.name, result.value)
            
            # Track active faces
            self.active_faces.append(result.name)
            
            # Limit active faces history
            if len(self.active_faces) > 10:
                self.active_faces = self.active_faces[-10:]
            
            return {
                "name": result.name,
                "value": result.value,
                "category": result.category.name,
                "description": result.effect_description,
                "effects": effects
            }, f"{message} {effect_message}"
        
        return None, message
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "stats": self.stats.to_dict(),
            "dice_set": self.dice_set.to_dict(),
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "active_faces": self.active_faces,
            "character_class": self.character_class
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Character':
        """Create a Character from a dictionary."""
        # Make a copy to avoid modifying the input
        data_copy = data.copy()
        
        # Convert nested dictionaries to objects
        stats_data = data_copy.pop("stats", {})
        stats = CharacterStats.from_dict(stats_data)
        
        dice_set_data = data_copy.pop("dice_set", {})
        from core.dice import DiceSet  # Import here to avoid circular imports
        dice_set = DiceSet.from_dict(dice_set_data)
        
        # Create the character
        return cls(stats=stats, dice_set=dice_set, **data_copy)