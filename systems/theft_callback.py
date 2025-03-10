# /mnt/home2/mud/systems/theft_callback.py
# Imported to: object.py
# Imports from: driver.py

from typing import List, Tuple
from ..driver import driver, MudObject

class TheftCallbackHandler:
    def __init__(self):
        self.callbacks: List[Tuple[str, str]] = []  # (func_name, path)

    async def event_theft(self, command_ob: MudObject, thief: MudObject, victim: MudObject, stolen: List[MudObject]):
        if not self.callbacks:
            return
        if not stolen:  # Object itself stolen
            for func_name, path in self.callbacks:
                target = driver.load_object(path)
                if target:
                    await driver.call_other(target, func_name, self, thief, victim)

    def add_theft_callback(self, func_name: str, path: str) -> int:
        if not isinstance(func_name, str) or not isinstance(path, str):
            return -1
        self.callbacks.append((func_name, path))
        print(f"Added theft callback: {func_name} {path}")  # debug_printf stub
        return len(self.callbacks) - 1

    def remove_theft_callback(self, id_: int) -> int:
        if id_ < 0 or id_ >= len(self.callbacks):
            return -1
        func_name, path = self.callbacks.pop(id_)
        print(f"Deleting callback: {func_name} {path}")  # debug_printf stub
        return 1

    def query_theft_callbacks(self) -> str:
        if not self.callbacks:
            return "No theft callbacks found!\n"
        return "".join(f"{i}. {func}: {path}\n" for i, (func, path) in enumerate(self.callbacks))

async def init(driver_instance):
    driver = driver_instance