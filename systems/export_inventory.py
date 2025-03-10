# /mnt/home2/mud/systems/export_inventory.py
# Imported to: room.py, living.py
# Imports from: driver.py

from typing import List, Optional, Union
from ..driver import driver, MudObject
import asyncio

class ExportInventory:
    def __init__(self):
        self.inventory: List[MudObject] = []  # Objects in this container/room

    def setup(self, obj: MudObject):
        """Sets up inventory attributes on an object."""
        obj.inventory = self.inventory.copy()

    def add_inventory(self, item: MudObject) -> bool:
        """Adds an item to the inventory."""
        if item in self.inventory:
            return False
        self.inventory.append(item)
        item.environment = lambda: driver.objects.get(item.attrs.get("env", None))
        return True

    def remove_inventory(self, item: MudObject) -> bool:
        """Removes an item from the inventory."""
        if item not in self.inventory:
            return False
        self.inventory.remove(item)
        item.environment = None
        return True

    def query_inventory(self) -> List[MudObject]:
        """Returns the current inventory."""
        return self.inventory.copy()

    def all_inventory(self) -> List[MudObject]:
        """Returns all inventory, including nested (2025 update)."""
        all_items = self.inventory.copy()
        for item in self.inventory:
            if hasattr(item, "all_inventory"):
                all_items.extend(item.all_inventory())
        return all_items

    async def query_contents(self, obj: MudObject, pattern: str, viewer: Optional[MudObject] = None) -> str:
        """Returns a formatted string of visible inventory contents."""
        if not self.inventory:
            return ""
        dark = viewer.check_dark(obj.query_light()) if viewer else 0
        visible = [item for item in self.inventory if item.query_visible(viewer) and (not pattern or pattern in item.query_short())]
        if not visible:
            return "Nothing matches your gaze.\n" if pattern else ""

        # Forgotten Realms flair (2025)
        prefix = "Scattered across the Weave, you see " if obj.query_property("location") == "outside" else "Here rests "
        if dark:
            return f"{prefix}a few indistinct shapes.\n"

        items = {}
        for item in visible:
            short = item.the_short(dark)
            items[short] = items.get(short, 0) + 1

        desc = prefix
        if len(items) == 1:
            key, count = next(iter(items.items()))
            desc += f"{key}{' alone' if count == 1 else f' ({count})'}.\n"
        else:
            desc += driver.multiple_short([f"{k} ({v})" if v > 1 else k for k, v in items.items()]) + ".\n"
        return desc

    def find_inv_match(self, obj: MudObject, pattern: str, viewer: Optional[MudObject]) -> List[MudObject]:
        """Finds inventory items matching a pattern (2025 update)."""
        if not pattern or pattern == "all":
            return [item for item in self.inventory if item.query_visible(viewer)]
        matches = []
        for item in self.inventory:
            if item.query_visible(viewer) and (pattern in item.query_short() or any(pattern in alias for alias in item.query_aliases())):
                matches.append(item)
        return matches

async def init(driver_instance):
    driver = driver_instance
    # No global instance; ExportInventory is a mixin class for objects like Room and Living