# /mnt/home2/mud/systems/terrain.py
from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject, Player
import asyncio
import random
import time
import hashlib

# Terrain types and properties based on DWWiki and Discworld sources
TERRAIN_TYPES = {
    "moorland": {"move_speed": 0.7, "visibility": 70, "track_difficulty": 0.6, "weather_factor": 1.2, "extra_look": "The moor stretches endlessly, shrouded in mist."},
    "plains": {"move_speed": 1.0, "visibility": 100, "track_difficulty": 0.8, "weather_factor": 1.0, "extra_look": "Vast plains roll out before you."},
    "deciduous_forest": {"move_speed": 0.8, "visibility": 60, "track_difficulty": 0.4, "weather_factor": 1.1, "extra_look": "Tall trees cast dappled shadows."},
    "meadow": {"move_speed": 0.9, "visibility": 90, "track_difficulty": 0.7, "weather_factor": 1.0, "extra_look": "A serene meadow sways in the breeze."},
    "seashore": {"move_speed": 0.6, "visibility": 70, "track_difficulty": 0.5, "weather_factor": 1.3, "extra_look": "The sound of waves fills the air."},
    "sandy_beach": {"move_speed": 0.5, "visibility": 70, "track_difficulty": 0.6, "weather_factor": 1.4, "extra_look": "Soft sand shifts underfoot."},
    "underdark": {"move_speed": 0.7, "visibility": 50, "track_difficulty": 0.3, "weather_factor": 0.9, "extra_look": "The air is thick with ancient stone."}
}

class Terrain(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.room: Optional[MudObject] = None
        self.terrain_name: str = ""
        self.x_coord: int = -1
        self.y_coord: int = -1
        self.z_coord: int = -1
        self.zones: List[str] = []
        self.features: Dict[str, dict] = {}
        self.dist_features: Dict[str, dict] = {}
        self.extra_long: str = ""
        self.random_desc: str = ""
        self.variable_exits: List[str] = []
        self.default_exits: Dict[str, str] = {}
        self.terrain_handler: str = "/systems/terrain_handler"  # Default handler
        self.terrain_chatter: Optional[MudObject] = None
        self.weather_handler = driver.weather_handler
        self.track_handler = driver.terrain_track_handler
        self.last_weather_update: float = 0
        self.blocking_flag: int = 0
        self.installed_flag: int = 0
        self.terrain_char: str = "."

    def setup_shadow(self, room: MudObject, terrain_name: str):
        """Sets up the terrain shadow with coordinates and effects."""
        self.room = room
        self.terrain_name = terrain_name.lower()
        self.zones = self._determine_zones()
        self.apply_terrain_effects()
        self.set_terrain_coords(0, 0, 0)  # Default coords, overrideable
        driver.event_handler.add_listener("weather_change", self._on_weather_change)
        driver.call_out(self._update_weather_effects, 300)
        self.room.add_property("terrain_map", 1)
        self.setup_room_chat()

    def _determine_zones(self) -> List[str]:
        """Determines zones based on terrain type."""
        zone_map = {
            "moorland": ["wilderness", "open"],
            "plains": ["wilderness", "open"],
            "deciduous_forest": ["wilderness", "forest"],
            "meadow": ["wilderness", "open"],
            "seashore": ["wilderness", "coastal"],
            "sandy_beach": ["wilderness", "coastal"],
            "underdark": ["underdark", "subterranean"]
        }
        return zone_map.get(self.terrain_name, ["wilderness"])

    def set_terrain_coords(self, x: int, y: int, z: int):
        """Sets the terrain coordinates."""
        self.x_coord = x
        self.y_coord = y
        self.z_coord = z
        self.room.set_co_ord([x, y, z])

    def apply_terrain_effects(self):
        """Applies terrain-specific effects."""
        if not self.room or self.terrain_name not in TERRAIN_TYPES:
            return
        effects = TERRAIN_TYPES[self.terrain_name]
        self.room.attrs["move_speed"] = effects["move_speed"]
        self.room.attrs["visibility"] = effects["visibility"]
        self.room.attrs["track_difficulty"] = effects["track_difficulty"]
        if "extra_look" in effects:
            self.room.add_extra_look(effects["extra_look"])
        for zone in self.zones:
            self.room.add_zone(zone)

    def _update_weather_effects(self):
        """Updates terrain effects based on weather."""
        if not self.room or time.time() - self.last_weather_update < 300:
            driver.call_out(self._update_weather_effects, 300)
            return
        weather = self.weather_handler.query_weather(self.room.attrs.get("co_ord", [0, 0, 0]))
        factor = TERRAIN_TYPES.get(self.terrain_name, {}).get("weather_factor", 1.0)
        visibility_adjust = max(10, self.room.attrs["visibility"] * (weather["visibility"] / 100) * factor)
        self.room.attrs["visibility"] = min(visibility_adjust, 100)
        self.last_weather_update = time.time()
        driver.call_out(self._update_weather_effects, 300)

    def tell_zones(self, player: Player):
        """Tells the player about the terrain zones."""
        if not self.zones:
            return
        player.tell(f"This area is part of the {', '.join(self.zones)} zones.")

    def query_track_difficulty(self) -> float:
        """Returns the difficulty of tracking in this terrain."""
        return self.room.attrs.get("track_difficulty", 0.5)

    def add_track(self, tracker: Player, target: str):
        """Adds a track record."""
        if not self.track_handler:
            return
        difficulty = self.query_track_difficulty()
        self.track_handler.add_track(self.room, tracker.name, target, difficulty)

    def query_visibility(self) -> int:
        """Returns the room's visibility, adjusted by terrain."""
        return self.room.attrs.get("visibility", 100)

    def long(self, word: str = "", dark: int = 0) -> str:
        """Returns the long description with terrain map and features."""
        base_long = self.room.query_long(word, dark)
        if self.x_coord >= 0 and self.y_coord >= 0:
            map_template = driver.terrain_handler.query_player_map_template(self.x_coord, self.y_coord, self.z_coord, self.query_visibility(), 9)
            map_lines = [line + "   " for line in map_template.split("\n")]
            base_long = f"$COLUMN$12={''.join(map_lines)}$COLUMN${base_long}"
        return base_long + self.extra_look()

    def hash(self, mod: int) -> int:
        """Generates a deterministic hash based on coordinates."""
        coord_str = f"{self.x_coord}:{self.y_coord}:{self.z_coord}"
        val = int(hashlib.md5(coord_str.encode()).hexdigest(), 16) % mod
        return val if val >= 0 else -val

    def hash_time(self, mod: int, period: int) -> int:
        """Generates a time-based deterministic hash."""
        coord_str = f"{self.x_coord}:{self.y_coord}:{self.z_coord}:{time.time() // period}"
        val = int(hashlib.md5(coord_str.encode()).hexdigest(), 16) % mod
        return val if val >= 0 else -val

    def set_terrain_handler(self, handler: str):
        """Sets the terrain handler path."""
        self.terrain_handler = handler

    def query_terrain_handler(self) -> str:
        """Returns the terrain handler path."""
        return self.terrain_handler

    def query_terrain_coords(self) -> List[int]:
        """Returns the terrain coordinates."""
        return [self.x_coord, self.y_coord, self.z_coord]

    def setup_room_chat(self):
        """Sets up terrain-specific chats."""
        if self.room.do_outside_chats():
            self.room.terrain_chat([60, 120, ["#do_a_feature_chat", "#do_an_outside_chat"]])

    def terrain_chat(self, args: List, chatobj: Optional[MudObject] = None):
        """Handles terrain chat setup."""
        if not args or not isinstance(args[2], list):
            print("Error: second argument of room_chat args is not an array.")
            return
        if self.terrain_chatter:
            self.terrain_chatter.setup_chatter(self.room, args)
            return
        self.terrain_chatter = MudObject(f"chatter_{self.room.oid}", "chatter")
        self.terrain_chatter.setup_chatter(self.room, args)
        driver.log_file("CHATTER", f"{time.ctime()[4:19]}: {self.room.oid} cloned terrain chatter: {self.terrain_chatter}\n")

    def do_a_feature_chat(self):
        """Generates a feature-based chat."""
        if self.x_coord < 0 or self.y_coord < 0:
            return
        chats = []
        for title, feature in self.features.items():
            feature_chat = driver.terrain_handler.get_a_feature_chat(title, feature["index"], feature["direc"])
            if feature_chat:
                chats.append(feature_chat)
        if chats:
            self.room.tell_room(random.choice(chats) + "\n")

    def do_an_outside_chat(self):
        """Generates an outside-type chat."""
        chat = driver.terrain_handler.get_an_outside_chat(self.room.attrs.get("outside_types", ""))
        if chat and len(chat):
            self.room.tell_room(chat + "\n")

    def add_feature(self, title: str, direcs: dict, items: Union[str, List], sentence: int = 0):
        """Adds a visible feature to the room."""
        self.features[title] = {"direcs": direcs, "items": items, "sentence": sentence, "index": 0, "visible": 1}
        if items:
            self.room.add_item(items, lambda t=title: self.query_feature_item_desc(t))

    def add_distant_feature(self, title: str, bits: dict):
        """Adds a distant feature to the room."""
        self.dist_features[title] = bits

    def remove_feature(self, title: str):
        """Removes a feature from the room."""
        if title in self.features:
            feature = self.features[title]
            if feature["items"]:
                self.room.remove_item(feature["items"] if isinstance(feature["items"], str) else feature["items"][0])
            del self.features[title]

    def query_feature_item_desc(self, title: str) -> str:
        """Returns the item description for a feature."""
        if self.features.get(title, {}).get("visible", 0):
            return driver.terrain_handler.query_feature_item_desc(title)
        return ""

    def extra_look(self) -> str:
        """Returns extra look description with features."""
        result = self.extra_long
        descs = []
        visibility = self.query_visibility()
        for title, feature in self.features.items():
            tmp = driver.terrain_handler.query_feature_desc(title, feature["direcs"], visibility)
            if tmp:
                descs.extend(tmp)
        for title, feature in self.dist_features.items():
            tmp = driver.terrain_handler.query_distant_feature_desc(title, feature, visibility)
            if tmp:
                descs.extend(tmp)
        if descs:
            result += "  " + self.room.query_multiple_short(descs) + "."
        if self.random_desc:
            result += self.random_desc
        return result + "\n" if driver.terrain_handler.query_newline_mode() else result

    def set_extra_long(self, extra: str):
        """Sets the extra long description."""
        self.extra_long = extra

    def set_outside_types(self, types: str):
        """Sets the outside types for chats."""
        self.room.attrs["outside_types"] = types

    def add_random_desc(self, desc: str):
        """Adds a random description to the terrain."""
        self.random_desc += desc + " "

    def add_zone(self, zone: str):
        """Adds a zone to the room."""
        self.room.add_zone(zone)
        driver.terrain_handler.add_room_to_zone(self.room, zone)

    def query_dest_other(self, exit: str, data: List) -> List:
        """Modifies exit destinations based on terrain logic."""
        if not isinstance(exit, str) or not self.default_exits:
            return data
        if exit in self.default_exits:
            if driver.this_player() and driver.this_player().query_property("terrain_map_long_jump") and \
               f"{self.query_terrain_map_journey_exit()}{exit}" in self.variable_exits:
                exit = f"{self.query_terrain_map_journey_exit()}{exit}"
            else:
                data[ROOM_DEST] = self.default_exits[exit]
                return data
        if exit in self.variable_exits:
            bing = driver.terrain_handler.find_next_room_from(self.x_coord, self.y_coord, self.z_coord, exit[len(self.query_terrain_map_journey_exit()):])
            if bing:
                if data[ROOM_DEST] != bing[0]:
                    data[ROOM_DEST] = bing[0]
                    bits = []
                    cur_dir = None
                    num = 0
                    for dir in bing[1:]:
                        if dir == cur_dir:
                            num += 1
                        else:
                            if cur_dir:
                                bits.append(self.query_direction_distance_str(num, cur_dir))
                            cur_dir = dir
                            num = 1
                    if cur_dir:
                        bits.append(self.query_direction_distance_str(num, cur_dir))
                    if len(bits) > 1:
                        data[ROOM_MESS] = f"You arrive after having journeyed {', '.join(bits[:-1])}, and {bits[-1]}.\n"
                    else:
                        data[ROOM_MESS] = f"You arrive after having journeyed {bits[0]}.\n"
                    if not data[ROOM_ENTER] or not data[ROOM_ENTER][0]:
                        data[ROOM_ENTER] = f"$N journey$s in from {driver.room_handler.query_opposite_direction(bing[-1])}.\n"
                    if not data[ROOM_EXIT]:
                        data[ROOM_EXIT] = f"$N journey$s to the {bing[1]}.\n"
        return data

    def query_direction_distance_str(self, num: int, dir: str) -> str:
        """Returns a distance string for a direction."""
        dist = driver.terrain_handler.query_direction_distance(dir)
        dist_mess = "section"
        if 0 <= dist <= 2:
            dist_mess = "foot" if dist <= 1 else f"{dist} foot"
        elif 3 <= dist < (TERRAIN_MAP_ONE_MILE / 2):
            dist //= 3
            dist_mess = "yard" if dist <= 1 else f"{dist} yard"
        elif (TERRAIN_MAP_ONE_MILE / 2) <= dist < TERRAIN_MAP_ONE_MILE:
            dist //= (TERRAIN_MAP_ONE_MILE / 2)
            dist_mess = "mile" if dist <= 1 else f"{dist} miles"
        else:
            dist //= TERRAIN_MAP_ONE_MILE
            dist_mess = "mile" if dist <= 1 else f"{dist} miles"
        return f"{self.room.query_num(num)} {dist_mess}{'s' if num > 1 else ''} {dir}"

    def query_terrain_map_walk_exit(self) -> str:
        """Returns the prefix for walk exits."""
        return TERRAIN_MAP_WALK_EXIT

    def query_terrain_map_journey_exit(self) -> str:
        """Returns the prefix for journey exits."""
        return TERRAIN_MAP_JOURNEY_EXIT

    def add_variable_exit(self, exit: str):
        """Adds a variable exit."""
        self.variable_exits.append(exit)

    def add_default_exit(self, exit: str, location: str):
        """Adds a default exit."""
        self.default_exits[exit] = location

    def query_default_exits(self) -> Dict[str, str]:
        """Returns the default exits mapping."""
        return self.default_exits.copy()

    def set_terrain_map_block(self, blocking: int):
        """Sets the blocking flag."""
        self.blocking_flag = 1 if blocking else 0

    def query_terrain_map_block(self) -> int:
        """Returns the blocking flag."""
        return self.blocking_flag

    def set_terrain_map_character(self, terr: str):
        """Sets the terrain map character."""
        self.terrain_char = terr

    def query_terrain_map_character(self) -> str:
        """Returns the terrain map character."""
        return self.terrain_char

    def destruct_shadow(self):
        """Removes terrain effects and destroys the shadow."""
        if self.room:
            self.room.attrs.pop("move_speed", None)
            self.room.attrs.pop("visibility", None)
            self.room.attrs.pop("track_difficulty", None)
            if "extra_look" in TERRAIN_TYPES.get(self.terrain_name, {}):
                self.room.remove_extra_look(TERRAIN_TYPES[self.terrain_name]["extra_look"])
            for zone in self.zones:
                self.room.remove_zone(zone)
            driver.event_handler.remove_listener("weather_change", self._on_weather_change)
            if self.terrain_chatter:
                driver.log_file("CHATTER", f"{time.ctime()[4:19]}: {self.room.oid} dested terrain chatter: {self.terrain_chatter}\n")
                self.terrain_chatter.dest_me()
        self.room = None
        self.destruct()

    def _on_weather_change(self, event_data: Dict):
        """Handles weather change events."""
        if self.room and "coords" in event_data and event_data["coords"] == [self.x_coord, self.y_coord, self.z_coord]:
            self._update_weather_effects()

    async def init(self):
        """Initializes terrain-specific behavior."""
        if driver.this_player() and driver.this_player().query_creator():
            driver.this_player().tell(f"Coords: ({self.x_coord}, {self.y_coord}, {self.z_coord})\n")
            self.room.add_command("cremap", "", lambda: self.do_map())
            self.room.add_command("cremap", "all", lambda: self.do_map_terrain())
        if driver.this_player():
            self.add_effect("/std/effects/terrain_dont_unload", [])

    def do_map(self) -> int:
        """Displays a debug map for the creator."""
        map_data = driver.terrain_handler.query_debug_map(self.x_coord, self.y_coord, 13, self.x_coord, self.y_coord)
        driver.this_player().tell(map_data)
        self.room.add_succeeded_mess("")
        return 1

    def do_map_terrain(self) -> int:
        """Displays a terrain-wide debug map."""
        map_data = driver.terrain_handler.query_debug_map(20, 20, 40, self.x_coord, self.y_coord)
        driver.this_player().tell(map_data)
        self.room.add_succeeded_mess("")
        return 1

async def init(driver_instance):
    driver = driver_instance
    driver.terrain_handler = Terrain  # Simplified handler reference
    driver.terrain_track_handler = MudObject("terrain_track_handler", "terrain_track")  # Placeholder

# Constants from terrain_map.h (assumed values)
TERRAIN_MAP_ONE_MILE = 1000  # Placeholder value
TERRAIN_MAP_WALK_EXIT = "walk_"
TERRAIN_MAP_JOURNEY_EXIT = "journey_"
TERRAIN_MAP_GRID_SIZE = 100  # Placeholder value
