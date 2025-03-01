"""
Inventory and item system implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from core.enums import Rarity

@dataclass
class Item:
    """
    Represents an item in the game.
    """
    name: str
    description: str
    effect: str
    value: int
    rarity: Rarity = Rarity.COMMON
    use_function: Optional[Callable] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "effect": self.effect,
            "value": self.value,
            "rarity": self.rarity.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Item':
        """Create an Item from a dictionary."""
        from core.enums import Rarity
        
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Convert string representation to enum
        data_copy["rarity"] = Rarity[data_copy["rarity"]]
        
        # Create the item (without use_function, will need to be assigned separately)
        return cls(**data_copy)


@dataclass
class Inventory:
    """
    Manages a collection of items.
    """
    items: List[Item] = field(default_factory=list)
    max_size: int = 20
    gold: int = 0
    
    def add_item(self, item: Item) -> bool:
        """
        Add an item to the inventory if there's space.
        Returns True if successful, False if inventory is full.
        """
        if len(self.items) >= self.max_size:
            return False
        
        self.items.append(item)
        return True
    
    def remove_item(self, index: int) -> Optional[Item]:
        """
        Remove and return an item at the given index.
        Returns None if the index is invalid.
        """
        if index < 0 or index >= len(self.items):
            return None
        
        return self.items.pop(index)
    
    def get_item(self, index: int) -> Optional[Item]:
        """
        Get an item at the given index without removing it.
        Returns None if the index is invalid.
        """
        if index < 0 or index >= len(self.items):
            return None
        
        return self.items[index]
    
    def is_full(self) -> bool:
        """Check if the inventory is full."""
        return len(self.items) >= self.max_size
    
    def add_gold(self, amount: int) -> None:
        """Add gold to the inventory."""
        self.gold += amount
    
    def remove_gold(self, amount: int) -> bool:
        """
        Remove gold from the inventory if there's enough.
        Returns True if successful, False if there's not enough gold.
        """
        if amount > self.gold:
            return False
        
        self.gold -= amount
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "max_size": self.max_size,
            "gold": self.gold
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Inventory':
        """Create an Inventory from a dictionary."""
        # Create the inventory
        inventory = cls(max_size=data.get("max_size", 20), gold=data.get("gold", 0))
        
        # Add items
        for item_data in data.get("items", []):
            item = Item.from_dict(item_data)
            inventory.add_item(item)
            
        return inventory


@dataclass
class ItemFactory:
    """
    Factory for creating common items.
    """
    @staticmethod
    def create_healing_potion(tier: int = 1) -> Item:
        """Create a healing potion of the specified tier."""
        if tier == 1:
            return Item(
                name="Minor Healing Potion",
                description="A small flask containing a red liquid",
                effect="Restores 20 health",
                value=25,
                rarity=Rarity.COMMON
            )
        elif tier == 2:
            return Item(
                name="Healing Potion",
                description="A flask containing a red liquid",
                effect="Restores 40 health",
                value=50,
                rarity=Rarity.UNCOMMON
            )
        else:
            return Item(
                name="Major Healing Potion",
                description="A large flask containing a vibrant red liquid",
                effect="Restores 80 health",
                value=100,
                rarity=Rarity.RARE
            )
    
    @staticmethod
    def create_mana_potion(tier: int = 1) -> Item:
        """Create a mana potion of the specified tier."""
        if tier == 1:
            return Item(
                name="Minor Mana Potion",
                description="A small flask containing a blue liquid",
                effect="Restores 10 mana",
                value=25,
                rarity=Rarity.COMMON
            )
        elif tier == 2:
            return Item(
                name="Mana Potion",
                description="A flask containing a blue liquid",
                effect="Restores 25 mana",
                value=50,
                rarity=Rarity.UNCOMMON
            )
        else:
            return Item(
                name="Major Mana Potion",
                description="A large flask containing a vibrant blue liquid",
                effect="Restores 50 mana",
                value=100,
                rarity=Rarity.RARE
            )
    
    @staticmethod
    def create_stat_boost(stat: str, tier: int = 1) -> Item:
        """Create a stat-boosting item."""
        if stat.lower() == "strength":
            return Item(
                name=f"{'Minor ' if tier == 1 else ''}Strength Elixir",
                description=f"A {'small ' if tier == 1 else ''}flask containing a crimson liquid",
                effect=f"Permanently increases physical damage by {tier}",
                value=tier * 75,
                rarity=Rarity.UNCOMMON if tier == 1 else Rarity.RARE
            )
        elif stat.lower() == "intelligence":
            return Item(
                name=f"{'Minor ' if tier == 1 else ''}Intelligence Elixir",
                description=f"A {'small ' if tier == 1 else ''}flask containing a deep blue liquid",
                effect=f"Permanently increases magic damage by {tier}",
                value=tier * 75,
                rarity=Rarity.UNCOMMON if tier == 1 else Rarity.RARE
            )
        elif stat.lower() == "vitality":
            return Item(
                name=f"{'Minor ' if tier == 1 else ''}Vitality Elixir",
                description=f"A {'small ' if tier == 1 else ''}flask containing a golden liquid",
                effect=f"Permanently increases max health by {tier * 10}%",
                value=tier * 100,
                rarity=Rarity.UNCOMMON if tier == 1 else Rarity.RARE
            )
        else:  # Agility
            return Item(
                name=f"{'Minor ' if tier == 1 else ''}Agility Elixir",
                description=f"A {'small ' if tier == 1 else ''}flask containing a green liquid",
                effect=f"Permanently increases speed by {tier} and dodge by {tier * 2}%",
                value=tier * 75,
                rarity=Rarity.UNCOMMON if tier == 1 else Rarity.RARE
            )