# /mnt/home2/mud/systems/effects.py
# Imported to: room.py, living.py, weather_handler.py
# Imports from: driver.py

from typing import Dict, List, Optional, Union
from ..driver import driver, MudObject
import asyncio
import time

class Effects:
    def __init__(self):
        self.effects: Dict[str, tuple] = {}  # {effect_id: (handler_oid, arg, duration, start_time)}
        self.active_effects: List[str] = []  # List of currently active effect IDs

    def setup(self, obj: MudObject):
        """Sets up effects attributes on an object."""
        obj.effects = self.effects.copy()
        obj.active_effects = self.active_effects.copy()

    def add_effect(self, effect: str, arg: Union[int, str, list], duration: int = -1) -> bool:
        """Adds an effect to the object (2025 update)."""
        if not effect.startswith("/"):
            effect = f"/std/effects/{effect}"
        handler = driver.load_object(effect)
        if not handler or not hasattr(handler, "apply_effect"):
            return False

        effect_id = f"{effect}_{len(self.effects)}"
        start_time = int(time.time())
        self.effects[effect_id] = (effect, arg, duration, start_time)
        self.active_effects.append(effect_id)
        
        # Apply effect immediately
        handler.apply_effect(obj, arg)
        if duration > 0:
            driver.call_out(lambda: self.remove_effect(obj, effect_id), duration)
        return True

    def remove_effect(self, obj: MudObject, effect_id: str) -> bool:
        """Removes an effect from the object."""
        if effect_id not in self.effects:
            return False
        effect, arg, _, _ = self.effects[effect_id]
        handler = driver.load_object(effect)
        if handler and hasattr(handler, "remove_effect"):
            handler.remove_effect(obj, arg)
        del self.effects[effect_id]
        if effect_id in self.active_effects:
            self.active_effects.remove(effect_id)
        return True

    def query_effects(self) -> Dict[str, tuple]:
        """Returns all current effects."""
        current_time = int(time.time())
        expired = [eid for eid, (_, _, dur, start) in self.effects.items() if dur > 0 and current_time >= start + dur]
        for eid in expired:
            self.remove_effect(None, eid)  # Pass None as obj since it’s expired
        return self.effects.copy()

    def query_active_effects(self) -> List[str]:
        """Returns the list of active effect IDs."""
        return self.active_effects.copy()

    async def check_effects(self, obj: MudObject):
        """Checks and updates effects, notifying if needed."""
        current_time = int(time.time())
        for effect_id, (effect, arg, duration, start) in list(self.effects.items()):
            if duration > 0 and current_time >= start + duration:
                self.remove_effect(obj, effect_id)
            else:
                handler = driver.load_object(effect)
                if handler and hasattr(handler, "update_effect"):
                    await handler.update_effect(obj, arg)
        
        # Forgotten Realms flair (2025)
        if "mystra_blessing" in [eid.split("_")[0] for eid in self.active_effects]:
            await obj.send("The Weave pulses around you, Mystra’s favor enduring.\n")

    def stats(self, obj: MudObject) -> List[tuple]:
        """Returns effect stats for debugging."""
        current_time = int(time.time())
        stats = []
        for eid, (effect, arg, duration, start) in self.effects.items():
            remaining = "Permanent" if duration < 0 else max(0, start + duration - current_time)
            stats.append((eid, f"{effect} (arg: {arg}, time: {remaining}s)"))
        return stats

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Effects is a mixin class for objects like Room and Living