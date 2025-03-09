# /mnt/home2/mud/systems/terrain_handler.py
from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject
import os
import time

# Constants from terrain.h and map.h (assumed values)
RESTORE_PATH = "/data/terrain/"
BACKUP_TIME_OUT = 1000000
TERRAIN_MAP_ONE_MILE = 1000
TERRAIN_MAP_GRID_SIZE = 100
STD_ORDERS = [
    "north", [0, 1, 0], "northeast", [1, 1, 0], "east", [1, 0, 0],
    "southeast", [1, -1, 0], "south", [0, -1, 0], "southwest", [-1, -1, 0],
    "west", [-1, 0, 0], "northwest", [-1, 1, 0], "up", [0, 0, 1],
    "down", [0, 0, -1]
]
STD_TYPES = {
    "north": "path", "south": "path", "east": "path", "west": "path",
    "northeast": "hidden", "southwest": "hidden", "southeast": "hidden",
    "northwest": "hidden", "up": "stair", "down": "stair"
}

class TerrainHandler(MudObject):
    def __init__(self):
        super().__init__("terrain_handler", "terrain_handler")
        self.terrain_name: str = ""
        self.fixed_locations: Dict[str, List[int]] = {}
        self.floating_locations: List[Tuple[str, List[int], int]] = []
        self.cloned_locations: Dict[str, Dict[int, Dict[int, Dict[int, str]]]] = {}
        self.size_cache: Dict[str, int] = {}
        self.float_cache: Dict[str, Dict[int, Dict[int, Dict[int, str]]]] = {}
        self.in_map: int = 0

    def setup(self):
        """Initializes the terrain handler."""
        self.set_name("terrain map")
        self.set_short("terrain map")
        self.add_adjective("terrain")
        self.set_long("This is a large map showing diverse landscapes. Locations of interest are marked.\n")

    def member_cloned_locations(self, co_ords: List[int]) -> Optional[str]:
        """Checks for a cloned location at the given coordinates."""
        terrain_data = self.cloned_locations.get(self.terrain_name)
        if terrain_data and co_ords[0] in terrain_data and co_ords[1] in terrain_data[co_ords[0]] and co_ords[2] in terrain_data[co_ords[0]][co_ords[1]]:
            return terrain_data[co_ords[0]][co_ords[1]][co_ords[2]]
        return None

    def member_fixed_locations(self, co_ords: List[int]) -> Optional[str]:
        """Checks for a fixed location at the given coordinates."""
        for file, loc_co_ords in self.fixed_locations.items():
            if co_ords[0] == loc_co_ords[0] and co_ords[1] == loc_co_ords[1] and co_ords[2] == loc_co_ords[2]:
                return file
        return None

    def between(self, limit1: int, val: int, limit2: int) -> bool:
        """Checks if a value is between two limits."""
        if limit1 < limit2:
            return limit1 <= val <= limit2
        return limit2 <= val <= limit1

    def member_floating_locations(self, co_ords: List[int]) -> List[Tuple[str, int]]:
        """Checks for floating locations at the given coordinates."""
        right_locations = []
        for loc in self.floating_locations:
            data = loc[1]
            if len(data) == 6:  # Bounding box
                if (self.between(data[0], co_ords[0], data[3]) and
                    self.between(data[1], co_ords[1], data[4]) and
                    self.between(data[2], co_ords[2], data[5])):
                    right_locations.append((loc[0], loc[2]))
            elif len(data) == 3:  # Single point
                if co_ords == data:
                    right_locations.append((loc[0], loc[2]))
        return right_locations

    def top_floating_location(self, co_ords: List[int]) -> Optional[str]:
        """Returns the highest priority floating location."""
        locations = self.member_floating_locations(co_ords)
        if not locations:
            return None
        highest_level = -1
        highest_location = None
        for loc, level in locations:
            if level > highest_level:
                highest_level = level
                highest_location = loc
        return None if highest_location == "nothing" else highest_location

    def get_data_file(self, word: str) -> bool:
        """Loads terrain data file."""
        if self.terrain_name != word:
            file_path = f"{RESTORE_PATH}{word}.o"
            if os.path.exists(file_path):
                # Simulated unguarded restore (placeholder for security)
                self.terrain_name = word
                self.fixed_locations.clear()
                self.floating_locations.clear()
                # Assume restore_object logic here
            else:
                self.init_data(word)
                return False
        return True

    def init_data(self, word: str):
        """Initializes terrain data."""
        self.terrain_name = word
        self.fixed_locations = {}
        self.floating_locations = []

    def save_data_file(self, word: str):
        """Saves terrain data file with backup."""
        if os.path.exists(f"{RESTORE_PATH}{word}.o"):
            backup_path = f"{RESTORE_PATH}backups/{word}.{time.time()}"
            # Simulated unguarded rename
            if os.path.exists(backup_path):
                # Cleanup old backups (simplified)
                pass
        # Simulated unguarded save
        pass

    def query_cloned_locations(self, terrain: str) -> Dict:
        """Returns cloned locations for a terrain."""
        return self.cloned_locations.get(terrain, {})

    def query_fixed_locations(self, word: str) -> Dict[str, List[int]]:
        """Returns fixed locations."""
        self.get_data_file(word)
        return self.fixed_locations.copy()

    def query_floating_locations(self, word: str) -> List[Tuple[str, List[int], int]]:
        """Returns floating locations."""
        self.get_data_file(word)
        return self.floating_locations.copy()

    def query_co_ord(self, terrain: str, file: str) -> Optional[List[int]]:
        """Returns coordinates for a file."""
        self.get_data_file(terrain)
        return self.fixed_locations.get(file)

    def query_connection(self, terrain: str, co_ords: List[int], direc: str) -> Optional[str]:
        """Returns the connecting room for a direction."""
        if not self.float_cache.get(terrain) or co_ords[0] not in self.float_cache[terrain]:
            # Simulated file read (placeholder)
            pass
        data = self.float_cache.get(terrain, {}).get(co_ords[0], {}).get(co_ords[1], {}).get(co_ords[2], {})
        return data.get(direc)

    def query_connected(self, terrain: str, co_ords: List[int]) -> bool:
        """Checks if coordinates are connected."""
        return bool(self.query_connection(terrain, co_ords, STD_ORDERS[0]))

    def add_fixed_location(self, terrain: str, file: str, co_ords: List[int]) -> bool:
        """Adds a fixed location."""
        self.get_data_file(terrain)
        if file in self.fixed_locations or len(co_ords) != 3:
            return False
        self.fixed_locations[file] = co_ords
        self.save_data_file(terrain)
        return True

    def add_floating_location(self, terrain: str, file: str, co_ords: List[int], level: int) -> bool:
        """Adds a floating location."""
        self.get_data_file(terrain)
        if (len(co_ords) not in (3, 6) or any(loc in [f[0] for f in self.floating_locations] for loc in [file])):
            return False
        self.floating_locations.append((file, co_ords, level))
        self.save_data_file(terrain)
        return True

    def add_cloned_location(self, terrain: str, file: str, co_ords: List[int]):
        """Adds a cloned location."""
        if terrain not in self.cloned_locations:
            self.cloned_locations[terrain] = {co_ords[0]: {co_ords[1]: {co_ords[2]: file}}}
        else:
            loc_data = self.cloned_locations[terrain]
            loc_data.setdefault(co_ords[0], {}).setdefault(co_ords[1], {})[co_ords[2]] = file

    def modify_fixed_location(self, terrain: str, file: str, co_ords: List[int]) -> bool:
        """Modifies a fixed location."""
        self.get_data_file(terrain)
        if file not in self.fixed_locations or len(co_ords) != 3:
            return False
        self.fixed_locations[file] = co_ords
        self.save_data_file(terrain)
        return True

    def delete_cloned_location(self, terrain: str, file: str) -> bool:
        """Deletes a cloned location."""
        if terrain in self.cloned_locations and file in self.cloned_locations[terrain]:
            co_ords = self.cloned_locations[terrain][file]
            del self.cloned_locations[terrain][file]
            if co_ords[0] in self.cloned_locations[terrain] and co_ords[1] in self.cloned_locations[terrain][co_ords[0]]:
                del self.cloned_locations[terrain][co_ords[0]][co_ords[1]][co_ords[2]]
            return True
        return False

    def delete_fixed_location(self, terrain: str, file: str) -> bool:
        """Deletes a fixed location."""
        self.get_data_file(terrain)
        if file not in self.fixed_locations:
            return False
        del self.fixed_locations[file]
        self.save_data_file(terrain)
        return True

    def delete_floating_location(self, terrain: str, file: str, co_ords: List[int]) -> bool:
        """Deletes a floating location."""
        self.get_data_file(terrain)
        for i, (f, c, _) in enumerate(self.floating_locations):
            if f == file and c == co_ords:
                self.floating_locations.pop(i)
                self.save_data_file(terrain)
                return True
        return False

    def clear_cloned_locations(self, terrain: str):
        """Clears cloned locations cache."""
        if terrain in self.cloned_locations:
            del self.cloned_locations[terrain]

    def clear_connections(self, terrain: str):
        """Clears all connections for a terrain."""
        if terrain in self.float_cache:
            del self.float_cache[terrain]
        # Simulated file cleanup
        pass

    def get_room_size(self, file: str, level: int = 0) -> int:
        """Returns the room size with caching."""
        bname = file.replace(".c", "")
        if bname in self.size_cache:
            return self.size_cache[bname]
        obj = driver.find_object(file)
        if obj:
            self.size_cache[bname] = obj.query_room_size()
            return self.size_cache[bname]
        if not self.in_map:
            self.in_map = 1
            mapsize = driver.map_handler.query_room_size(bname) if driver.map_handler else [10]
            self.in_map = 0
            if mapsize:
                self.size_cache[bname] = mapsize[0]
                return mapsize[0]
        if os.path.exists(f"{bname}.c"):  # Simulated file parsing
            self.size_cache[bname] = 10  # Default size
            return 10
        return 10

    def add_exit(self, place: MudObject, direc: str, dest: str):
        """Adds an exit to the room."""
        type = place.query_exit_type(direc, dest) or STD_TYPES.get(direc, "path")
        if type != "none":
            place.add_exit(direc, dest, type)

    def calculate_exits(self, place: MudObject, co_ords: List[int]):
        """Calculates and adds exits based on terrain connections."""
        connected = self.query_connected(self.terrain_name, co_ords)
        exit_dirs = place.query_direc()
        for i in range(0, len(STD_ORDERS), 2):
            if STD_ORDERS[i] in exit_dirs:
                continue
            actual = self.query_connection(self.terrain_name, co_ords, STD_ORDERS[i])
            if actual:
                self.add_exit(place, STD_ORDERS[i], actual)
                continue
            if connected:
                continue
            new_co_ords = [c - place.query_room_size() * v for c, v in zip(co_ords, STD_ORDERS[i + 1])]
            for _ in range(100):
                new_co_ords = [c - 5 * v for c, v in zip(new_co_ords, STD_ORDERS[i + 1])]
                actual = (self.member_fixed_locations(new_co_ords) or
                          self.member_cloned_locations(new_co_ords) or
                          self.top_floating_location(new_co_ords))
                if actual:
                    delta = place.query_room_size() + self.get_room_size(actual)
                    if all(n + delta * v == c for n, v, c in zip(new_co_ords, STD_ORDERS[i + 1], co_ords)):
                        self.add_connection(self.terrain_name, co_ords, STD_ORDERS[i], actual)
                        self.add_exit(place, STD_ORDERS[i], actual)
                        break

    def find_location(self, terrain: str, co_ords: List[int]) -> Optional[MudObject]:
        """Finds or loads a room at the given coordinates."""
        if not self.get_data_file(terrain) or len(co_ords) != 3:
            return None
        dest_name = (self.member_fixed_locations(co_ords) or
                     self.member_cloned_locations(co_ords) or
                     self.top_floating_location(co_ords))
        if not dest_name:
            return None
        destination = driver.find_object(dest_name)
        if not destination and dest_name != "nothing":
            destination = driver.load_object(dest_name)
            if not destination and dest_name == self.top_floating_location(co_ords):
                destination = driver.clone_object(dest_name)
                destination.set_co_ord(co_ords)
                destination.set_terrain(terrain)
                self.calculate_exits(destination, co_ords)
                self.add_cloned_location(terrain, file_name(destination), co_ords)
        return destination

    def setup_location(self, place: MudObject, terrain: str):
        """Sets up a fixed location with exits."""
        if base_name(place) not in self.fixed_locations:
            return
        co_ords = self.fixed_locations[base_name(place)]
        place.set_co_ord(co_ords)
        self.calculate_exits(place, co_ords)

    def add_connection(self, terrain: str, co_ords: List[int], direc: str, file: str):
        """Adds a connection between rooms."""
        if not self.float_cache.get(terrain):
            self.float_cache[terrain] = {}
        if co_ords[0] not in self.float_cache[terrain]:
            self.float_cache[terrain][co_ords[0]] = {}
        if co_ords[1] not in self.float_cache[terrain][co_ords[0]]:
            self.float_cache[terrain][co_ords[0]][co_ords[1]] = {}
        self.float_cache[terrain][co_ords[0]][co_ords[1]][co_ords[2]] = {direc: file}

async def init(driver_instance):
    driver = driver_instance
    driver.terrain_handler = TerrainHandler()
