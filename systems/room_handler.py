# /mnt/home2/mud/systems/room_handler.py
from typing import Dict, List, Tuple, Optional
from ..driver import driver, MudObject

# Constants based on Discworld room.h and room_handler.c
EXIT_TYPES = {
    "road": {"size": 10, "obvious": 1, "relative": 0},
    "path": {"size": 5, "obvious": 1, "relative": 0},
    "door": {"size": 3, "obvious": 1, "relative": 0, "door": True},
    "secret": {"size": 2, "obvious": 0, "relative": 0, "door": True},
    "corridor": {"size": 4, "obvious": 1, "relative": 0},
    "hidden": {"size": 2, "obvious": 0, "relative": 0}
}

DOOR_TYPES = {
    "door": {"default_state": "closed", "default_locked": False},
    "secret": {"default_state": "closed", "default_locked": False}
}

class RoomHandler:
    def __init__(self):
        self.exit_types: Dict[str, dict] = EXIT_TYPES
        self.door_types: Dict[str, dict] = DOOR_TYPES

    def query_exit_type(self, type: str, direc: str) -> List:
        """Returns exit configuration based on type."""
        config = self.exit_types.get(type.lower(), {"size": 0, "obvious": 0, "relative": 0})
        return [
            config.get("size", 0),  # ROOM_SIZE
            "",  # ROOM_EXIT (empty message)
            "",  # ROOM_MESS (empty move message)
            config.get("obvious", 0),  # ROOM_OBV
            config.get("relative", 0),  # ROOM_REL
            "",  # ROOM_FUNC (empty function)
            config.get("size", 0),  # ROOM_SIZE (repeated for consistency)
            0,  # ROOM_GRADE (no upgrade/downgrade by default)
            None,  # ROOM_DELTA (no delta by default)
            "",  # ROOM_LOOK (empty look)
            None  # ROOM_LOOK_FUNC (no look function)
        ]

    def query_door_type(self, type: str, direc: str, dest: str) -> Optional[dict]:
        """Returns door configuration based on type."""
        door_config = self.door_types.get(type.lower())
        if not door_config:
            return None
        return {
            "state": door_config["default_state"],
            "locked": door_config["default_locked"],
            "direction": direc,
            "destination": dest
        }

room_handler = RoomHandler()

async def init(driver_instance):
    driver = driver_instance
