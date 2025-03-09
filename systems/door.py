# /mnt/home2/mud/systems/door.py
from typing import Optional, Union, Dict, List
from ..driver import driver, MudObject

class Door(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.attrs["state"] = "closed"  # Default state
        self.attrs["locked"] = False  # Default unlocked
        self.attrs["direction"] = ""
        self.attrs["destination"] = ""
        self.attrs["owner_room"] = None
        self.attrs["door_name"] = ""

    def setup_door(self, direc: str, owner: MudObject, dest: str, door_data: Dict, type: str):
        """Sets up the door with given configuration."""
        self.attrs["direction"] = direc
        self.attrs["destination"] = dest
        self.attrs["owner_room"] = owner
        self.attrs["state"] = door_data.get("state", "closed")
        self.attrs["locked"] = door_data.get("locked", False)
        self.attrs["door_name"] = direc  # Default door name, can be modified
        self.set_short(f"{direc} door")
        self.set_long(f"This is a {type} door leading {direc} to {dest}.")
        self.add_alias("door")

    def query_open(self) -> bool:
        """Returns whether the door is open."""
        return self.attrs["state"] == "open"

    def set_open(self, state: bool):
        """Sets the door's open/closed state."""
        self.attrs["state"] = "open" if state else "closed"

    def query_locked(self) -> bool:
        """Returns whether the door is locked."""
        return self.attrs["locked"]

    def set_locked(self, state: bool):
        """Sets the door's locked state."""
        self.attrs["locked"] = state

    def query_door_name(self) -> str:
        """Returns the door's name."""
        return self.attrs["door_name"]

    def tell_door(self, message: str, thing: MudObject):
        """Sends a message to the room via the door."""
        if self.attrs["owner_room"]:
            self.attrs["owner_room"].tell_room(message, [thing])

    def multiple_hidden(self) -> int:
        """Returns the number of rooms this door is hidden in (simplified)."""
        return 1  # Assume single room for now

    def dest_me(self):
        """Destroys the door object."""
        self.destruct()

async def init(driver_instance):
    driver = driver_instance
