# /mnt/home2/mud/systems/shadow.py
# Imported to: room.py, rooftop.py, wall.py, situation_changer.py
# Imports from: driver.py

from typing import Optional, Callable, Dict
from ..driver import driver, MudObject
import asyncio

class Shadow:
    def __init__(self, oid: str = "shadow", name: str = "shadow"):
        self.oid = oid
        self.name = name
        self.shadowed: Optional[MudObject] = None
        self.overrides: Dict[str, Callable] = {}  # {method_name: custom_function}

    def setup_shadow(self, obj: MudObject):
        """Attaches this shadow to an object."""
        if not obj:
            return
        self.shadowed = obj
        self.shadowed.shadow = self  # Link back to shadow
        # Default overrides can be set here if needed

    def destruct_shadow(self):
        """Removes the shadow from the object."""
        if self.shadowed:
            self.shadowed.shadow = None
        self.shadowed = None
        self.overrides.clear()
        if self.oid in driver.objects:
            del driver.objects[self.oid]

    def override_method(self, method: str, func: Callable):
        """Overrides a shadowed method with a custom function (2025 update)."""
        self.overrides[method] = func

    async def call_shadow(self, method: str, *args, **kwargs):
        """Calls a shadowed method or falls back to the original."""
        if method in self.overrides:
            return await self.overrides[method](self.shadowed, *args, **kwargs) if asyncio.iscoroutinefunction(self.overrides[method]) else self.overrides[method](self.shadowed, *args, **kwargs)
        if self.shadowed and hasattr(self.shadowed, method):
            original = getattr(self.shadowed, method)
            return await original(*args, **kwargs) if asyncio.iscoroutinefunction(original) else original(*args, **kwargs)
        return None

    async def event_enter(self, obj: MudObject, from_room: Optional[MudObject]):
        """Handles entry with Forgotten Realms flair (2025 async update)."""
        if self.shadowed:
            await self.shadowed.tell_room(f"{obj.name} emerges, shadowed by the Ethereal Veil.\n")
            return await self.call_shadow("event_enter", obj, from_room)

    def query_shadowed(self) -> Optional[MudObject]:
        """Returns the shadowed object."""
        return self.shadowed

async def init(driver_instance):
    driver = driver_instance
    # No global instance; shadows are instantiated per use (e.g., in rooftop.py)