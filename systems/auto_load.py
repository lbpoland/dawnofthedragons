# /mnt/home2/mud/systems/auto_load.py
# Imported to: object.py, player.py
# Imports from: driver.py

from typing import Dict, Any
from ..driver import driver, MudObject

class AutoLoadHandler:
    def __init__(self):
        self.AUTO_LOAD_TAG = "basic.object"

    def add_auto_load_value(self, map_: Dict[str, Any], file_name: str, tag: str, value: Any) -> Dict[str, Any]:
        map_[f"{file_name}  :  {tag}"] = value
        return map_

    def query_auto_load_value(self, map_: Dict[str, Any], file_name: str, tag: str) -> Any:
        if tag == "::":
            return map_
        return map_.get(f"{file_name}  :  {tag}", map_.get(tag))

async def init(driver_instance):
    driver = driver_instance
    driver.auto_load = AutoLoadHandler()