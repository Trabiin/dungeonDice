"""
Enumerations for the game
"""

from enum import Enum, auto

class DiceType(Enum):
    """Types of dice in the game."""
    CHARACTER = auto()
    COMBAT = auto()
    ENCOUNTER = auto()
    SPECIAL = auto()
    FATE = auto()

class FaceCategory(Enum):
    """Categories for dice faces."""
    TRAIT = auto()
    COMBAT = auto()
    EFFECT = auto()
    UTILITY = auto()
    META = auto()

class ImbalanceEffect(Enum):
    """Effects from dice imbalance."""
    NONE = auto()
    UNSTABLE = auto()
    OVERLOADED = auto()
    CURSED = auto()
    BLESSED = auto()
    CHAOTIC = auto()
    SYNCHRONIZED = auto()

class Rarity(Enum):
    """Rarity levels for items and dice."""
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()

class RoomType(Enum):
    """Types of rooms in the dungeon."""
    COMBAT = auto()
    ELITE = auto()
    TREASURE = auto()
    REST = auto()
    EVENT = auto()
    SHOP = auto()
    MYSTERY = auto()
    TRAP = auto()
    BOSS = auto()
    EXIT = auto()

class EnemyType(Enum):
    """Types of enemies."""
    GOBLIN = auto()
    SKELETON = auto()
    ORC = auto()
    ZOMBIE = auto()
    GHOST = auto()
    SLIME = auto()
    MINOTAUR = auto()
    DRAGON = auto()
