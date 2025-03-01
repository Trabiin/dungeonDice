"""
Dice system implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Callable
from core.enums import DiceType, FaceCategory, ImbalanceEffect, Rarity
import random

@dataclass
class DiceFace:
    """
    Represents a single face on a die with associated properties and effects.
    """
    name: str
    value: int  # Positive for buffs, negative for debuffs
    category: FaceCategory
    effect_description: str
    rarity: Rarity = Rarity.COMMON
    cost: Dict[str, int] = field(default_factory=dict)  # Resource costs (e.g., {"mana": 5})
    synergies: List[str] = field(default_factory=list)  # Other face names this synergizes with
    effect_function: Optional[Callable] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "name": self.name,
            "value": self.value,
            "category": self.category.name,
            "effect_description": self.effect_description,
            "rarity": self.rarity.name,
            "cost": self.cost,
            "synergies": self.synergies,
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiceFace':
        """Create a DiceFace from a dictionary."""
        from core.enums import FaceCategory, Rarity
        
        # Convert string representations back to enums
        data_copy = data.copy()
        data_copy["category"] = FaceCategory[data_copy["category"]]
        data_copy["rarity"] = Rarity[data_copy["rarity"]]
        
        # Effect function can't be serialized
        if "effect_function" in data_copy:
            data_copy.pop("effect_function")
            
        return cls(**data_copy)

@dataclass
class Dice:
    """
    Represents a complete die with multiple faces and associated properties.
    """
    name: str
    dice_type: DiceType
    size: int  # Number of faces (e.g., 4 for d4, 6 for d6)
    rarity: Rarity = Rarity.COMMON
    description: str = ""
    faces: List[DiceFace] = field(default_factory=list)
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100
    cooldown: int = 0  # Turns until the die can be used again
    
    # Balance properties
    balance_value: int = 0
    imbalance_effect: ImbalanceEffect = ImbalanceEffect.NONE
    imbalance_severity: float = 0.0  # 0.0 to 1.0, representing severity
    
    # Dice modifiers
    modifiers: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Calculate balance if faces are provided
        if self.faces:
            self._calculate_balance()
    
    def add_face(self, face: DiceFace) -> bool:
        """Add a face to the die if there's room."""
        if len(self.faces) >= self.size:
            return False
        
        self.faces.append(face)
        self._calculate_balance()
        return True
    
    def remove_face(self, index: int) -> Optional[DiceFace]:
        """Remove and return a face at the given index."""
        if 0 <= index < len(self.faces):
            face = self.faces.pop(index)
            self._calculate_balance()
            return face
        return None
    
    def replace_face(self, index: int, new_face: DiceFace) -> Optional[DiceFace]:
        """Replace a face at the given index and return the old one."""
        if 0 <= index < len(self.faces):
            old_face = self.faces[index]
            self.faces[index] = new_face
            self._calculate_balance()
            return old_face
        return None
    
    def roll(self) -> Tuple[Optional[DiceFace], str, List[str]]:
        """
        Roll the die and return the result face along with any special effects from imbalance.
        Returns (face, message, effect_list)
        """
        if not self.faces:
            return None, "Die has no faces!", []
        
        # Check if die is on cooldown
        if self.cooldown > 0:
            self.cooldown -= 1
            return None, f"{self.name} is on cooldown for {self.cooldown+1} more turns.", []
        
        effects = []
        message = ""
        
        # Handle imbalance effects
        if self.imbalance_effect == ImbalanceEffect.UNSTABLE:
            # Roll twice and take the worse result if RNG triggers the effect
            if random.random() < self.imbalance_severity:
                roll1 = random.choice(self.faces)
                roll2 = random.choice(self.faces)
                # For simplicity, consider lower value as "worse" in this prototype
                result = roll1 if roll1.value < roll2.value else roll2
                message = f"UNSTABLE: Rolled {roll1.name} and {roll2.name}, took worse result {result.name}."
                effects.append("Unstable: Double Roll")
                return result, message, effects
        
        # Standard roll
        result = random.choice(self.faces)
        
        # Add XP for rolling this die
        self.add_xp(10)
        
        return result, (message if message else "Normal roll."), effects
    
    def _calculate_balance(self) -> None:
        """Calculate the balance value of the die and set imbalance effects."""
        self.balance_value = sum(face.value for face in self.faces)
        
        # Simplified imbalance calculation
        if self.balance_value == 0:
            self.imbalance_effect = ImbalanceEffect.NONE
            self.imbalance_severity = 0.0
        elif self.balance_value < 0:
            self.imbalance_effect = ImbalanceEffect.UNSTABLE
            self.imbalance_severity = min(1.0, abs(self.balance_value) / (self.size * 2))
        else:
            self.imbalance_effect = ImbalanceEffect.OVERLOADED
            self.imbalance_severity = min(1.0, self.balance_value / (self.size * 2))
    
    def add_xp(self, amount: int) -> bool:
        """
        Add XP to the die and level up if necessary.
        Returns True if the die leveled up.
        """
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.level_up()
            return True
        return False
    
    def level_up(self) -> None:
        """Level up the die, improving its properties."""
        self.level += 1
        self.xp -= self.xp_to_next_level
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)  # Increase XP needed for next level
        
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "dice_type": self.dice_type.name,
            "size": self.size,
            "rarity": self.rarity.name,
            "description": self.description,
            "faces": [face.to_dict() for face in self.faces],
            "level": self.level,
            "xp": self.xp,
            "xp_to_next_level": self.xp_to_next_level,
            "cooldown": self.cooldown,
            "balance_value": self.balance_value,
            "imbalance_effect": self.imbalance_effect.name,
            "imbalance_severity": self.imbalance_severity,
            "modifiers": self.modifiers
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Dice':
        """Create a Dice from a dictionary."""
        from core.enums import DiceType, Rarity, ImbalanceEffect
        
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Handle faces separately
        faces_data = data_copy.pop("faces", [])
        faces = [DiceFace.from_dict(face_data) for face_data in faces_data]
        
        # Convert string representations to enums
        data_copy["dice_type"] = DiceType[data_copy["dice_type"]]
        data_copy["rarity"] = Rarity[data_copy["rarity"]]
        data_copy["imbalance_effect"] = ImbalanceEffect[data_copy["imbalance_effect"]]
        
        # Create the die
        die = cls(**data_copy)
        
        # Add faces
        for face in faces:
            die.add_face(face)
            
        return die

@dataclass
class DiceSet:
    """
    Manages a collection of dice grouped by type.
    """
    character_dice: List[Dice] = field(default_factory=list)
    combat_dice: List[Dice] = field(default_factory=list)
    encounter_dice: List[Dice] = field(default_factory=list)
    special_dice: List[Dice] = field(default_factory=list)
    fate_dice: List[Dice] = field(default_factory=list)
    
    def add_dice(self, dice: Dice) -> bool:
        """Add a die to the appropriate collection based on its type."""
        if dice.dice_type == DiceType.CHARACTER:
            self.character_dice.append(dice)
        elif dice.dice_type == DiceType.COMBAT:
            self.combat_dice.append(dice)
        elif dice.dice_type == DiceType.ENCOUNTER:
            self.encounter_dice.append(dice)
        elif dice.dice_type == DiceType.SPECIAL:
            self.special_dice.append(dice)
        elif dice.dice_type == DiceType.FATE:
            self.fate_dice.append(dice)
        else:
            return False
        return True
    
    def get_dice_list(self, dice_type: DiceType) -> List[Dice]:
        """Get the list of dice for the specified type."""
        if dice_type == DiceType.CHARACTER:
            return self.character_dice
        elif dice_type == DiceType.COMBAT:
            return self.combat_dice
        elif dice_type == DiceType.ENCOUNTER:
            return self.encounter_dice
        elif dice_type == DiceType.SPECIAL:
            return self.special_dice
        elif dice_type == DiceType.FATE:
            return self.fate_dice
        else:
            return []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "character_dice": [d.to_dict() for d in self.character_dice],
            "combat_dice": [d.to_dict() for d in self.combat_dice],
            "encounter_dice": [d.to_dict() for d in self.encounter_dice],
            "special_dice": [d.to_dict() for d in self.special_dice],
            "fate_dice": [d.to_dict() for d in self.fate_dice]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiceSet':
        """Create a DiceSet from a dictionary."""
        dice_set = cls()
        
        # Process each dice type
        if "character_dice" in data:
            for dice_data in data["character_dice"]:
                dice_set.character_dice.append(Dice.from_dict(dice_data))
                
        if "combat_dice" in data:
            for dice_data in data["combat_dice"]:
                dice_set.combat_dice.append(Dice.from_dict(dice_data))
                
        if "encounter_dice" in data:
            for dice_data in data["encounter_dice"]:
                dice_set.encounter_dice.append(Dice.from_dict(dice_data))
                
        if "special_dice" in data:
            for dice_data in data["special_dice"]:
                dice_set.special_dice.append(Dice.from_dict(dice_data))
                
        if "fate_dice" in data:
            for dice_data in data["fate_dice"]:
                dice_set.fate_dice.append(Dice.from_dict(dice_data))
                
        return dice_set
