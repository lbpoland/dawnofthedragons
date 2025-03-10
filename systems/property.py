# /mnt/home2/mud/systems/property.py
# Imported to: room.py, living.py, rooftop.py
# Imports from: driver.py

from typing import Dict, Optional, Union
from ..driver import driver, MudObject
import asyncio
import time

class Property:
    def __init__(self):
        self.properties: Dict[str, Union[str, int, list]] = {}  # Permanent properties
        self.temp_properties: Dict[str, tuple] = {}  # (value, duration, start_time) for temp props

    def setup(self, obj: MudObject):
        """Sets up property attributes on an object."""
        obj.properties = self.properties.copy()
        obj.temp_properties = self.temp_properties.copy()

    def add_property(self, name: str, value: Union[str, int, list], duration: Optional[int] = None):
        """Adds a property, optionally temporary (2025 feature)."""
        if duration is None:
            self.properties[name] = value
        else:
            if duration > 0:
                self.temp_properties[name] = (value, duration, int(time.time()))
                driver.call_out(lambda: self.remove_property(name), duration)

    def remove_property(self, name: str) -> bool:
        """Removes a property, permanent or temporary."""
        if name in self.properties:
            del self.properties[name]
            return True
        if name in self.temp_properties:
            del self.temp_properties[name]
            return True
        return False

    def query_property(self, name: str) -> Optional[Union[str, int, list]]:
        """Queries a property, checking temp first (2025 update)."""
        if name in self.temp_properties:
            value, duration, start = self.temp_properties[name]
            if int(time.time()) < start + duration:
                return value
            del self.temp_properties[name]
        return self.properties.get(name)

    def query_properties(self) -> Dict[str, Union[str, int, list]]:
        """Returns all current properties, merging temp and permanent."""
        props = self.properties.copy()
        current_time = int(time.time())
        for name, (value, duration, start) in list(self.temp_properties.items()):
            if current_time < start + duration:
                props[name] = value
            else:
                del self.temp_properties[name]
        return props

    async def check_property(self, obj: MudObject, name: str) -> bool:
        """Checks if a property exists and is active."""
        value = self.query_property(name)
        if value is not None:
            # Forgotten Realms: Mystra’s blessing enhances certain properties
            if name == "mystra_blessing" and isinstance(value, int) and value > 0:
                await obj.send("A faint arcane hum surrounds you, blessed by Mystra.\n")
            return True
        return False

    def stats(self, obj: MudObject) -> List[tuple]:
        """Returns property stats for debugging."""
        stats = [(name, value) for name, value in self.properties.items()]
        current_time = int(time.time())
        for name, (value, duration, start) in self.temp_properties.items():
            remaining = max(0, start + duration - current_time)
            stats.append((f"{name} (temp)", f"{value} for {remaining}s"))
        return stats

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Property is a mixin class for objects like Room and Living