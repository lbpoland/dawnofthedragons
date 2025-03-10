# /mnt/home2/mud/systems/light.py
# Imported to: room.py, living.py
# Imports from: driver.py

from typing import Optional
from ..driver import driver, MudObject
import asyncio

class Light:
    def __init__(self):
        self.light_level: int = 0  # Base light (0-100)
        self.temp_light: int = 0  # Temporary light modifier (2025 feature)
        self.temp_duration: int = 0  # Duration in seconds for temp light
        self.temp_start: int = 0  # Start time of temp light

    def setup(self, obj: MudObject):
        """Sets up light attributes on an object."""
        obj.light_level = self.light_level
        obj.temp_light = self.temp_light
        obj.temp_duration = self.temp_duration
        obj.temp_start = self.temp_start

    def set_light(self, level: int):
        """Sets the base light level."""
        self.light_level = max(0, min(100, level))

    def query_light(self) -> int:
        """Returns the total light level, including temporary effects."""
        total = self.light_level
        if self.temp_duration > 0:
            if int(time.time()) < self.temp_start + self.temp_duration:
                total += self.temp_light
            else:
                self.temp_light = 0
                self.temp_duration = 0
                self.temp_start = 0
        return max(0, min(100, total))

    def adjust_light(self, amount: int):
        """Adjusts the base light level."""
        self.light_level = max(0, min(100, self.light_level + amount))

    def add_temp_light(self, amount: int, duration: int):
        """Adds a temporary light effect (2025 feature)."""
        if duration <= 0:
            return
        self.temp_light = amount
        self.temp_duration = duration
        self.temp_start = int(time.time())
        driver.call_out(lambda: self.clear_temp_light(), duration)

    def clear_temp_light(self):
        """Clears the temporary light effect."""
        self.temp_light = 0
        self.temp_duration = 0
        self.temp_start = 0

    async def check_dark(self, obj: MudObject, viewer: Optional[MudObject] = None) -> int:
        """Determines visibility based on light (2025 update)."""
        env_light = obj.query_light() if obj else 0
        viewer_light = viewer.query_light() if viewer else 0
        total_light = max(env_light, viewer_light)

        # Forgotten Realms: Moonlight from Selûne
        if viewer and viewer.environment() and viewer.environment().query_property("location") == "outside":
            moon_state = driver.weather_handler.query_moon_state()
            total_light += moon_state * 5  # 0-30 from moon phases

        if total_light < 10:
            return -1  # Too dark
        elif total_light > 90:
            return 1  # Too bright
        return 0  # Visible

    def stats(self, obj: MudObject) -> List[tuple]:
        """Returns light-related stats for debugging."""
        return [
            ("light level", self.light_level),
            ("temp light", self.temp_light if self.temp_duration > 0 else 0),
            ("temp duration", max(0, self.temp_start + self.temp_duration - int(time.time())))
        ]

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Light is a mixin class for objects like Room and Living