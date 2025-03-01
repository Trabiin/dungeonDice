"""
Dungeon generation and room management
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union, Tuple
from core.enums import RoomType, EnemyType, Rarity
from core.inventory import Item, ItemFactory

@dataclass
class Event:
    """
    Represents an event with choices and outcomes.
    """
    name: str
    description: str
    choices: List[str]
    outcomes: List[str]  # Results of each choice
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "choices": self.choices,
            "outcomes": self.outcomes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create an Event from a dictionary."""
        return cls(**data)


@dataclass
class Enemy:
    """
    Represents an enemy in the game.
    Simplified version for the prototype.
    """
    name: str
    enemy_type: EnemyType
    level: int
    health: int
    max_health: int
    damage: int
    gold_reward: int
    xp_reward: int
    
    def is_alive(self) -> bool:
        """Check if the enemy is still alive."""
        return self.health > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "enemy_type": self.enemy_type.name,
            "level": self.level,
            "health": self.health,
            "max_health": self.max_health,
            "damage": self.damage,
            "gold_reward": self.gold_reward,
            "xp_reward": self.xp_reward
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Enemy':
        """Create an Enemy from a dictionary."""
        from core.enums import EnemyType
        
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Convert string representation to enum
        data_copy["enemy_type"] = EnemyType[data_copy["enemy_type"]]
        
        return cls(**data_copy)


@dataclass
class Room:
    """
    Represents a single room in the dungeon.
    """
    room_type: RoomType
    name: str
    description: str
    enemies: List[Enemy] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)
    gold: int = 0
    event: Optional[Event] = None
    visited: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            "room_type": self.room_type.name,
            "name": self.name,
            "description": self.description,
            "enemies": [enemy.to_dict() for enemy in self.enemies],
            "items": [item.to_dict() for item in self.items],
            "gold": self.gold,
            "visited": self.visited
        }
        
        if self.event:
            result["event"] = self.event.to_dict()
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Room':
        """Create a Room from a dictionary."""
        from core.enums import RoomType
        from core.inventory import Item
        
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Convert string representation to enum
        data_copy["room_type"] = RoomType[data_copy["room_type"]]
        
        # Handle nested objects
        enemies_data = data_copy.pop("enemies", [])
        enemies = [Enemy.from_dict(enemy_data) for enemy_data in enemies_data]
        
        items_data = data_copy.pop("items", [])
        items = [Item.from_dict(item_data) for item_data in items_data]
        
        event_data = data_copy.pop("event", None)
        event = Event.from_dict(event_data) if event_data else None
        
        # Create the room
        room = cls(**data_copy, enemies=enemies, items=items, event=event)
        
        return room


@dataclass
class Floor:
    """
    Represents a floor in the dungeon with multiple rooms.
    """
    level: int
    rooms: List[Room]
    current_room_index: int = 0
    completed: bool = False
    
    def get_current_room(self) -> Room:
        """Get the current room the player is in."""
        return self.rooms[self.current_room_index]
    
    def move_to_room(self, index: int) -> bool:
        """
        Move to a different room by index.
        Returns True if successful, False if the index is invalid.
        """
        if 0 <= index < len(self.rooms):
            self.current_room_index = index
            return True
        return False
    
    def move_to_next_room(self) -> Optional[Room]:
        """
        Move to the next room if possible.
        Returns the new room if successful, None if at the last room.
        """
        if self.current_room_index < len(self.rooms) - 1:
            self.current_room_index += 1
            return self.get_current_room()
        return None
    
    def is_completed(self) -> bool:
        """
        Check if the floor is completed.
        A floor is completed if the last room is reached and cleared.
        """
        last_room = self.rooms[-1]
        return self.current_room_index == len(self.rooms) - 1 and last_room.visited
    
    def get_available_paths(self) -> List[Tuple[int, Room]]:
        """
        Get the available paths from the current room.
        Returns a list of tuples containing the room index and room.
        """
        # In a linear dungeon, the only path is to the next room
        # This can be extended for branching paths
        if self.current_room_index < len(self.rooms) - 1:
            next_index = self.current_room_index + 1
            return [(next_index, self.rooms[next_index])]
        return []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "level": self.level,
            "rooms": [room.to_dict() for room in self.rooms],
            "current_room_index": self.current_room_index,
            "completed": self.completed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Floor':
        """Create a Floor from a dictionary."""
        # Copy the data to avoid modifying the input
        data_copy = data.copy()
        
        # Handle nested objects
        rooms_data = data_copy.pop("rooms", [])
        rooms = [Room.from_dict(room_data) for room_data in rooms_data]
        
        # Create the floor
        return cls(rooms=rooms, **data_copy)


class DungeonGenerator:
    """
    Generates dungeon floors and rooms.
    """
    @staticmethod
    def generate_floor(floor_level: int) -> Floor:
        """
        Generate a floor for the given level.
        """
        rooms = []
        
        # Number of rooms increases with floor level
        num_rooms = 5 + min(floor_level - 1, 5)
        
        # First room is always a safe room
        if floor_level == 1:
            # Starting room on first floor
            rooms.append(Room(
                room_type=RoomType.REST,
                name="Campfire",
                description="A safe place to rest before your adventure begins."
            ))
        else:
            # Random starting room on subsequent floors
            start_type = random.choice([RoomType.REST, RoomType.EVENT])
            rooms.append(DungeonGenerator._create_room(start_type, floor_level))
        
        # Generate middle rooms
        for i in range(1, num_rooms - 1):
            # Weighted room type selection
            weights = {
                RoomType.COMBAT: 40,
                RoomType.TREASURE: 15,
                RoomType.EVENT: 15,
                RoomType.SHOP: 10,
                RoomType.ELITE: 10,
                RoomType.TRAP: 5,
                RoomType.REST: 5
            }
            
            room_types = list(weights.keys())
            room_weights = [weights[rt] for rt in room_types]
            
            room_type = random.choices(room_types, weights=room_weights, k=1)[0]
            rooms.append(DungeonGenerator._create_room(room_type, floor_level))
        
        # Last room is always a boss or exit
        if floor_level % 3 == 0:
            # Boss room every third floor
            rooms.append(DungeonGenerator._create_room(RoomType.BOSS, floor_level))
        else:
            # Exit room otherwise
            rooms.append(Room(
                room_type=RoomType.EXIT,
                name="Exit Portal",
                description="A magical portal that leads to the next floor."
            ))
        
        return Floor(level=floor_level, rooms=rooms)
    
    @staticmethod
    def _create_room(room_type: RoomType, floor_level: int) -> Room:
        """
        Create a room of the specified type for the given floor level.
        """
        if room_type == RoomType.COMBAT:
            # Regular combat room
            num_enemies = 1 + (floor_level > 3) + (floor_level > 6)
            enemies = [DungeonGenerator._generate_enemy(floor_level, is_elite=False) for _ in range(num_enemies)]
            
            return Room(
                room_type=room_type,
                name="Monster Lair",
                description=f"A dark chamber inhabited by {num_enemies} hostile creatures.",
                enemies=enemies,
                gold=random.randint(5, 10) * floor_level
            )
        
        elif room_type == RoomType.ELITE:
            # Elite combat room
            elite_enemy = DungeonGenerator._generate_enemy(floor_level, is_elite=True)
            
            return Room(
                room_type=room_type,
                name="Elite's Domain",
                description=f"A dangerous area ruled by a powerful {elite_enemy.enemy_type.name.lower()}.",
                enemies=[elite_enemy],
                gold=random.randint(15, 25) * floor_level
            )
        
        elif room_type == RoomType.TREASURE:
            # Treasure room
            num_items = random.randint(1, 3)
            items = DungeonGenerator._generate_treasure_items(floor_level, num_items)
            
            return Room(
                room_type=room_type,
                name="Treasure Chamber",
                description="A room filled with valuable treasures and artifacts.",
                items=items,
                gold=random.randint(20, 40) * floor_level
            )
        
        elif room_type == RoomType.REST:
            # Rest site
            return Room(
                room_type=room_type,
                name="Rest Site",
                description="A safe location where you can rest and recover your strength."
            )
        
        elif room_type == RoomType.EVENT:
            # Event room
            event = DungeonGenerator._generate_event(floor_level)
            
            return Room(
                room_type=room_type,
                name="Mysterious Encounter",
                description="Something unusual is happening here...",
                event=event
            )
        
        elif room_type == RoomType.SHOP:
            # Shop room
            shop_items = DungeonGenerator._generate_shop_items(floor_level)
            
            return Room(
                room_type=room_type,
                name="Merchant's Shop",
                description="A traveling merchant has set up shop here.",
                items=shop_items
            )
        
        elif room_type == RoomType.TRAP:
            # Trap room
            trap_types = ["spike", "poison", "collapse", "magic"]
            trap_type = random.choice(trap_types)
            
            return Room(
                room_type=room_type,
                name=f"{trap_type.title()} Trap Room",
                description=f"A room filled with dangerous {trap_type} traps.",
                event=DungeonGenerator._generate_trap_event(trap_type, floor_level)
            )
        
        elif room_type == RoomType.BOSS:
            # Boss room
            boss = DungeonGenerator._generate_boss(floor_level)
            
            return Room(
                room_type=room_type,
                name=f"{boss.name}'s Chamber",
                description=f"A massive chamber where {boss.name} awaits.",
                enemies=[boss],
                gold=random.randint(50, 100) * floor_level
            )
        
        else:
            # Default to a combat room if an unknown type is provided
            return DungeonGenerator._create_room(RoomType.COMBAT, floor_level)
    
    @staticmethod
    def _generate_enemy(floor_level: int, is_elite: bool = False) -> Enemy:
        """
        Generate an enemy appropriate for the given floor level.
        """
        # Select enemy type based on floor level
        if floor_level <= 3:
            enemy_types = [EnemyType.GOBLIN, EnemyType.SKELETON, EnemyType.SLIME]
        elif floor_level <= 6:
            enemy_types = [EnemyType.ORC, EnemyType.ZOMBIE, EnemyType.GHOST]
        else:
            enemy_types = [EnemyType.MINOTAUR, EnemyType.GHOST, EnemyType.ORC]
        
        enemy_type = random.choice(enemy_types)
        
        # Apply multipliers based on if it's an elite
        level_multiplier = 1.0 if not is_elite else 1.5
        stat_multiplier = 1.0 if not is_elite else 2.0
        reward_multiplier = 1.0 if not is_elite else 2.5
        
        # Calculate stats based on floor level
        enemy_level = max(1, int(floor_level * level_multiplier))
        health = int((40 + floor_level * 15) * stat_multiplier)
        damage = int((3 + floor_level) * stat_multiplier)
        
        # Calculate rewards
        gold_reward = int(random.randint(5, 10) * floor_level * reward_multiplier)
        xp_reward = int(10 * floor_level * reward_multiplier)
        
        # Generate name with prefix if elite
        prefix = ""
        if is_elite:
            prefixes = ["Giant", "Ancient", "Elite", "Vicious", "Deadly", "Corrupted"]
            prefix = random.choice(prefixes) + " "
            
        name = f"{prefix}{enemy_type.name.title()}"
        
        return Enemy(
            name=name,
            enemy_type=enemy_type,
            level=enemy_level,
            health=health,
            max_health=health,
            damage=damage,
            gold_reward=gold_reward,
            xp_reward=xp_reward
        )
    
    @staticmethod
    def _generate_boss(floor_level: int) -> Enemy:
        """
        Generate a boss enemy for the given floor level.
        """
        # Boss stats scale significantly with floor level
        boss_health = 200 + floor_level * 30
        boss_damage = 10 + floor_level * 2
        
        # Create boss based on floor level
        if floor_level <= 3:
            name = "Grubnosh the Goblin King"
            enemy_type = EnemyType.GOBLIN
        elif floor_level <= 6:
            name = "Bonecrusher the Skeleton Lord"
            enemy_type = EnemyType.SKELETON
        elif floor_level <= 9:
            name = "Grimfang the Minotaur Berserker"
            enemy_type = EnemyType.MINOTAUR
        else:
            name = "Flamescale the Ancient Dragon"
            enemy_type = EnemyType.DRAGON
        
        return Enemy(
            name=name,
            enemy_type=enemy_type,
            level=floor_level + 3,
            health=boss_health,
            max_health=boss_health,
            damage=boss_damage,
            gold_reward=random.randint(80, 150) * floor_level,
            xp_reward=floor_level * 50
        )
    
    @staticmethod
    def _generate_treasure_items(floor_level: int, num_items: int) -> List[Item]:
        """
        Generate treasure items appropriate for the given floor level.
        """
        items = []
        factory = ItemFactory()
        
        for _ in range(num_items):
            # Determine rarity based on floor level
            rarity_roll = random.random()
            if rarity_roll < 0.6 - floor_level * 0.05:
                # Common item
                item_type = random.choice(["healing", "mana"])
                if item_type == "healing":
                    item = factory.create_healing_potion(tier=1)
                else:
                    item = factory.create_mana_potion(tier=1)
            elif rarity_roll < 0.9 - floor_level * 0.03:
                # Uncommon item
                item_type = random.choice(["healing", "mana", "strength", "intelligence", "vitality", "agility"])
                if item_type == "healing":
                    item = factory.create_healing_potion(tier=2)
                elif item_type == "mana":
                    item = factory.create_mana_potion(tier=2)
                else:
                    item = factory.create_stat_boost(item_type, tier=1)
            else:
                # Rare item
                item_type = random.choice(["healing", "mana", "strength", "intelligence", "vitality", "agility"])
                if item_type == "healing":
                    item = factory.create_healing_potion(tier=3)
                elif item_type == "mana":
                    item = factory.create_mana_potion(tier=3)
                else:
                    item = factory.create_stat_boost(item_type, tier=2)
            
            items.append(item)
        
        return items
    
    @staticmethod
    def _generate_shop_items(floor_level: int) -> List[Item]:
        """
        Generate shop items appropriate for the given floor level.
        """
        # Shop has more items than treasure room
        num_items = random.randint(3, 6)
        return DungeonGenerator._generate_treasure_items(floor_level, num_items)
    
    @staticmethod
    def _generate_event(floor_level: int) -> Event:
        """
        Generate a random event for the given floor level.
        """
        # List of possible events
        events = [
            Event(
                name="Strange Altar",
                description="You find a strange altar with glowing runes. It seems to be waiting for an offering.",
                choices=[
                    "Make an offering of gold (50 gold)",
                    "Place one of your items on the altar",
                    "Touch the altar with your hand",
                    "Leave it alone"
                ],
                outcomes=[
                    "The altar glows with golden light. You feel a surge of power!",
                    "The altar consumes your offering. In return, you receive a mysterious item!",
                    "A strange energy flows through you as you touch the altar.",
                    "You decide not to mess with unknown magic and walk away."
                ]
            ),
            Event(
                name="Mysterious Stranger",
                description="A hooded figure stands in the corner of the room, watching you silently.",
                choices=[
                    "Approach and greet them",
                    "Throw them some gold (25 gold)",
                    "Demand they identify themselves",
                    "Ignore them and continue on"
                ],
                outcomes=[
                    "The stranger nods and hands you a small package before vanishing.",
                    "The stranger accepts your gold with a nod. They hand you a small vial.",
                    "The stranger's eyes narrow. A flash of magic strikes you!",
                    "You ignore the stranger and move on. When you look back, they're gone."
                ]
            ),
            Event(
                name="Dice Gambler",
                description="A sly-looking person offers to play a game of chance with you.",
                choices=[
                    "Bet small (25 gold)",
                    "Bet medium (50 gold)",
                    "Bet large (100 gold)",
                    "Decline the offer"
                ],
                outcomes=[
                    "You win the gamble and double your gold!",
                    "You win the gamble and double your gold!",
                    "You lose the gamble and your gold is gone.",
                    "You decline the offer. The gambler shrugs and walks away."
                ]
            ),
            Event(
                name="Ancient Fountain",
                description="You discover an ancient fountain filled with shimmering water.",
                choices=[
                    "Drink from the fountain",
                    "Throw in a coin (10 gold)",
                    "Wash your wounds in the water",
                    "Leave it alone"
                ],
                outcomes=[
                    "The water tastes sweet and refreshing. You feel revitalized!",
                    "The fountain bubbles happily. Something shiny appears at the bottom!",
                    "The water soothes your wounds. You feel much better!",
                    "You decide not to mess with the fountain and continue on your way."
                ]
            )
        ]
        
        # Select a random event
        return random.choice(events)
    
    @staticmethod
    def _generate_trap_event(trap_type: str, floor_level: int) -> Event:
        """
        Generate a trap event based on the trap type.
        """
        if trap_type == "spike":
            return Event(
                name="Spike Trap",
                description="The floor is covered with concealed spike plates. You'll need to carefully navigate through.",
                choices=[
                    "Move carefully (using Agility)",
                    "Look for a safe path (using Intelligence)",
                    "Use a tool or item to trigger the traps safely",
                    "Rush through and hope for the best"
                ],
                outcomes=[
                    "With careful movements, you navigate through the spike plates without triggering any.",
                    "You carefully study the patterns of the floor plates and identify a safe path through.",
                    "Using your item, you carefully trigger the spike traps from a safe distance.",
                    "You dash through the room! The spikes activate all around you."
                ]
            )
        elif trap_type == "poison":
            return Event(
                name="Poison Gas Trap",
                description="The room is filling with a sickly green gas that burns your lungs.",
                choices=[
                    "Hold your breath and run through (using Vitality)",
                    "Look for the gas source and disable it (using Intelligence)",
                    "Use an item to protect yourself",
                    "Cover your face with cloth and push through"
                ],
                outcomes=[
                    "You hold your breath and run through the gas cloud with minimal exposure.",
                    "You locate the gas vents and manage to block them, dispersing the poison cloud safely.",
                    "You use your item to protect yourself from the gas and pass through safely.",
                    "The cloth provides some protection, but you still feel the effects of the poison."
                ]
            )
        elif trap_type == "collapse":
            return Event(
                name="Collapsing Ceiling",
                description="The ceiling begins to rumble and crack, threatening to collapse on you.",
                choices=[
                    "Dash through quickly (using Speed)",
                    "Brace and protect yourself (using Strength)",
                    "Look for structural weaknesses (using Intelligence)",
                    "Use an item to create a safe passage"
                ],
                outcomes=[
                    "You sprint through the room just as large chunks of ceiling crash down behind you!",
                    "You brace yourself and endure falling debris as you push through the collapsing room.",
                    "You identify the most stable path through the room and navigate it safely.",
                    "Your item creates a temporary shelter, allowing you safe passage through the room."
                ]
            )
        else:  # magic trap
            return Event(
                name="Arcane Ward Trap",
                description="The room is filled with shimmering arcane runes that pulse with dangerous energy.",
                choices=[
                    "Use magical knowledge to disarm (using Intelligence)",
                    "Carefully navigate between the wards (using Agility)",
                    "Overpower the wards with brute force (using Strength)",
                    "Use an item to absorb or deflect the magic"
                ],
                outcomes=[
                    "You recognize the rune patterns and carefully disarm them one by one.",
                    "You deftly weave between the magical wards, avoiding their effects.",
                    "You push through the magical barriers with sheer force of will, taking some damage in the process.",
                    "Your item absorbs the magical energy, allowing you to pass safely."
                ]
            )