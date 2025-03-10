# /mnt/home2/mud/systems/inventory.py
# Imported to: room.py, living.py, export_inventory.py
# Imports from: driver.py

from typing import Dict, List, Optional, Union
from ..driver import driver, MudObject
import asyncio

class Inventory:
    def __init__(self):
        self.carried: List[MudObject] = []  # Items carried (worn/held)
        self.max_weight: int = 100  # Default max weight in units (20 units = 1 kg)
        self.encumbrance: Dict[str, int] = {}  # {item_oid: weight_penalty}

    def setup(self, obj: MudObject):
        """Sets up inventory attributes on an object."""
        obj.carried = self.carried.copy()
        obj.max_weight = self.max_weight
        obj.encumbrance = self.encumbrance.copy()

    def add_carried(self, item: MudObject) -> bool:
        """Adds an item to carried inventory."""
        if item in self.carried or self.query_loc_weight() + item.query_weight() > self.max_weight:
            return False
        self.carried.append(item)
        item.attrs["env"] = None  # No environment when carried
        self.encumbrance[item.oid] = item.query_weight()
        return True

    def remove_carried(self, item: MudObject) -> bool:
        """Removes an item from carried inventory."""
        if item not in self.carried:
            return False
        self.carried.remove(item)
        if item.oid in self.encumbrance:
            del self.encumbrance[item.oid]
        return True

    def query_carried(self) -> List[MudObject]:
        """Returns the list of carried items."""
        return self.carried.copy()

    def set_max_weight(self, weight: int):
        """Sets the maximum carry weight."""
        self.max_weight = max(0, weight)

    def query_max_weight(self) -> int:
        """Returns the maximum carry weight."""
        return self.max_weight

    def query_weight(self) -> int:
        """Returns the base weight of the object (2025 update)."""
        return sum(item.query_weight() for item in self.carried if item.query_weight() > 0)

    def query_loc_weight(self) -> int:
        """Returns the total weight including encumbrance."""
        return sum(self.encumbrance.get(item.oid, item.query_weight()) for item in self.carried)

    def query_complete_weight(self) -> int:
        """Returns total weight including nested inventory."""
        total = self.query_weight()
        for item in self.carried:
            if hasattr(item, "query_complete_weight"):
                total += item.query_complete_weight()
        return total

    async def adjust_encumbrance(self, obj: MudObject, item: MudObject, penalty: int):
        """Adjusts encumbrance for an item (2025 feature)."""
        if item not in self.carried:
            return
        base_weight = item.query_weight()
        new_weight = max(0, base_weight + penalty)
        self.encumbrance[item.oid] = new_weight
        if isinstance(obj, Player) and new_weight > base_weight * 1.5:
            await obj.send("The burden grows heavy under Mystra’s watchful eye.\n")

    async def list_inventory(self, obj: MudObject, viewer: Optional[MudObject] = None) -> str:
        """Lists carried inventory for viewing."""
        if not self.carried:
            return "Nothing is carried here.\n"
        dark = viewer.check_dark(obj.query_light()) if viewer else 0
        visible = [item for item in self.carried if item.query_visible(viewer)]
        if not visible:
            return "No visible burdens are borne.\n"

        items = {}
        for item in visible:
            short = item.a_short(dark)
            items[short] = items.get(short, 0) + 1

        desc = "Carried across Faerûn:\n" if not dark else "Shrouded burdens:\n"
        for short, count in items.items():
            desc += f"  {short}{' (' + str(count) + ')' if count > 1 else ''}\n"
        return desc

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Inventory is a mixin class for objects like Living and Room