# Imported to: terrain_handler.py, room.py
# Imports from: driver.py
# /mnt/home2/mud/systems/map_handler.py
from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject, Player
import random

class MapHandler(MudObject):
    def __init__(self, oid: str = "map_handler", name: str = "map_handler"):
        super().__init__(oid, name)
        self.terrain_handler = driver.terrain_handler
        self.newline_mode: bool = False
        self.feature_chats: Dict[str, List[str]] = {
            "waterdeep": ["The bustle of Waterdeep echoes nearby.", "A merchant’s call drifts from the city."],
            "underdark": ["Distant drips echo through the caverns.", "A faint skittering unsettles the silence."]
        }
        self.outside_chats: Dict[str, List[str]] = {
            "urban": ["A cart rattles down the cobblestones.", "Voices murmur from a nearby tavern."],
            "cave": ["The air grows damp and heavy.", "Stalactites gleam faintly above."]
        }
        self.room_sizes: Dict[str, int] = {}
        self.weather_effects: Dict[str, str] = {}  # 2025 weather integration

    def setup(self):
        """Initializes the map handler."""
        self.set_name("map handler")
        self.set_short("map handler")
        self.set_long("This object manages the mapping of vast terrains.\n")
        self.add_adjective("map")

    def query_newline_mode(self) -> bool:
        """Returns whether to use newlines in descriptions."""
        return self.newline_mode

    def set_newline_mode(self, mode: bool):
        """Sets the newline mode."""
        self.newline_mode = mode

   def query_player_map_template(self, x: int, y: int, z: int, visibility: int, size: int) -> str:
    map_lines = []
    center_x, center_y = x // 10, y // 10
    weather = self.weather_effects.get(f"{x},{y},{z}", "clear")  # From weather.py
    for i in range(center_y - size // 2, center_y + size // 2 + 1):
        line = ""
        for j in range(center_x - size // 2, center_x + size // 2 + 1):
            char = self._get_terrain_char(j * 10, i * 10, z)
            if visibility < 30 and weather in ["fog", "rain"]:
                char = "~" if weather == "fog" else "`"
            elif visibility < 50 and abs(j - center_x) > 1 or abs(i - center_y) > 1:
                char = "?"
            line += char
        map_lines.append(line)
    return "\n".join(map_lines) if self.newline_mode else " ".join(map_lines)

    def _get_terrain_char(self, x: int, y: int, z: int) -> str:
        """Determines the terrain character for a coordinate."""
        co_ords = [x, y, z]
        terrain = self.terrain_handler.terrain_name
        if self.terrain_handler.member_fixed_locations(co_ords):
            return "F"  # Fixed room
        locations = self.terrain_handler.member_floating_locations(co_ords)
        if locations:
            return "f" if locations[0][0] != "nothing" else " "  # Floating or nothing
        return "."  # Default terrain

    def query_feature_desc(self, title: str, direcs: Dict, visibility: int) -> List[str]:
        """Returns feature descriptions based on visibility."""
        if visibility < 50 or not direcs:
            return []
        # Placeholder: Assume handler has feature data
        return [f"You see a {title} to the {direcs.get('dir', 'unknown')}."]

    def query_distant_feature_desc(self, title: str, feature: Dict, visibility: int) -> List[str]:
        """Returns distant feature descriptions."""
        if visibility < 30:
            return []
        return [f"In the distance, you notice a {title}."]

    def query_feature_item_desc(self, title: str) -> str:
        """Returns the item description for a feature."""
        # Placeholder: Assume feature data exists
        return f"This is a {title} you can interact with."

    def get_a_feature_chat(self, title: str, index: int, direc: str) -> Optional[str]:
        """Returns a random feature chat."""
        chats = self.feature_chats.get(title, [])
        return random.choice(chats) if chats else None

    def get_an_outside_chat(self, types: str) -> Optional[str]:
        """Returns a random outside chat based on type."""
        chats = self.outside_chats.get(types, ["The wind rustles softly."])
        return random.choice(chats) if chats else None

    def query_room_size(self, bname: str) -> List[int]:
        """Returns the room size for a given base name."""
        if bname not in self.room_sizes:
            self.room_sizes[bname] = driver.terrain_handler.get_room_size(f"{bname}.c")
        return [self.room_sizes[bname]]

    def add_room_to_zone(self, room: MudObject, zone: str):
        """Adds a room to a zone (placeholder for zone management)."""
        room.add_zone(zone)

    def query_debug_map(self, x: int, y: int, size: int, center_x: int, center_y: int) -> str:
        """Generates a debug map for creators."""
        map_lines = []
        for i in range(y - size // 2, y + size // 2 + 1):
            line = ""
            for j in range(x - size // 2, x + size // 2 + 1):
                char = self._get_terrain_char(j * 10, i * 10, 0)
                line += char
            map_lines.append(line)
        return "\n".join(map_lines)

    def query_direction_distance(self, dir: str) -> int:
        """Returns the distance for a direction (simplified)."""
        return 10  # Placeholder value

def sync_weather(self, x: int, y: int, z: int, weather: str):
    """Syncs weather effects with the map."""
    self.weather_effects[f"{x},{y},{z}"] = weather

async def init(driver_instance):
    global driver
    driver = driver_instance
    map_handler = MapHandler()
    driver.objects[map_handler.oid] = map_handler
    driver.map_handler = map_handler