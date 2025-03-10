# /mnt/home2/mud/systems/extra_look.py
# Imported to: room.py, living.py
# Imports from: driver.py

from typing import List, Optional, Union
from ..driver import driver, MudObject
import asyncio

class ExtraLook:
    def __init__(self):
        self.extra_looks: List[Union[str, tuple]] = []  # List of strings or (obj, func) tuples
        self.temp_looks: List[tuple] = []  # (text, duration, start_time) for timed looks

    def setup(self, obj: MudObject):
        """Sets up extra look attributes on an object."""
        obj.extra_looks = self.extra_looks.copy()
        obj.temp_looks = self.temp_looks.copy()

    def add_extra_look(self, look: Union[str, tuple]):
        """Adds a permanent extra look description."""
        if isinstance(look, str):
            if look not in self.extra_looks:
                self.extra_looks.append(look.strip())
        elif isinstance(look, tuple) and len(look) == 2:
            # Tuple of (object, function) for dynamic looks
            if look not in self.extra_looks:
                self.extra_looks.append(look)

    def remove_extra_look(self, look: Union[str, tuple]) -> bool:
        """Removes a permanent extra look description."""
        if look in self.extra_looks:
            self.extra_looks.remove(look)
            return True
        return False

    def add_temp_look(self, text: str, duration: int):
        """Adds a temporary extra look with a duration (2025 feature)."""
        if not isinstance(text, str) or duration <= 0:
            return
        temp = (text.strip(), duration, int(time.time()))
        self.temp_looks.append(temp)
        driver.call_out(lambda: self.remove_temp_look(temp), duration)

    def remove_temp_look(self, look: tuple) -> bool:
        """Removes a temporary extra look."""
        if look in self.temp_looks:
            self.temp_looks.remove(look)
            return True
        return False

    def query_extra_looks(self) -> List[Union[str, tuple]]:
        """Returns the list of permanent extra looks."""
        return self.extra_looks.copy()

    def query_temp_looks(self) -> List[tuple]:
        """Returns the list of temporary extra looks."""
        return [look for look in self.temp_looks if look[2] + look[1] > int(time.time())]

    async def calc_extra_look(self, obj: MudObject) -> str:
        """Calculates the combined extra look description."""
        desc = ""
        # Permanent looks
        for look in self.extra_looks:
            if isinstance(look, str):
                desc += look + "\n"
            elif isinstance(look, tuple):
                try:
                    result = getattr(look[0], look[1])(obj)
                    if result:
                        desc += result + "\n"
                except AttributeError:
                    driver.log_file("ERRORS", f"Invalid extra look function {look[1]} on {look[0].oid}\n")

        # Temporary looks (2025 feature)
        current_time = int(time.time())
        for look in self.temp_looks[:]:  # Copy to avoid modification during iteration
            if look[2] + look[1] <= current_time:
                self.temp_looks.remove(look)
            else:
                desc += look[0] + "\n"

        # Forgotten Realms flair (2025)
        if obj.query_enchant() > 100 and "A faint arcane shimmer lingers here." not in desc:
            desc += "A faint arcane shimmer lingers here, touched by Mystra’s Weave.\n"

        return desc.rstrip()

async def init(driver_instance):
    driver = driver_instance
    # No global instance; ExtraLook is a mixin class for objects like Room and Living