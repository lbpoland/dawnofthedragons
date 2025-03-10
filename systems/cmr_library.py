# /mnt/home2/mud/systems/cmr_library.py
# Imported to: cmr_handler.py
# Imports from: driver.py

from typing import List
from ..driver import driver, MudObject
import os

RESTORE_PATH = "/save/cmr_library/"

class CMRLibraryHandler:
    def __init__(self):
        self.player_name = ""
        self.materials: List[str] = []

    def init_data(self, pname: str):
        self.player_name = pname
        self.materials = []

    def get_data_file(self, pname: str) -> bool:
        if self.player_name != pname:
            file_path = f"{RESTORE_PATH}{pname}.json"
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                # Placeholder for restore_object; assumes JSON save
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.player_name = data["player_name"]
                    self.materials = data["materials"]
            else:
                self.init_data(pname)
                return False
        return True

    def save_data_file(self, word: str):
        # Placeholder for save_object; uses JSON
        os.makedirs(RESTORE_PATH, exist_ok=True)
        with open(f"{RESTORE_PATH}{word}.json", 'w') as f:
            json.dump({"player_name": word, "materials": self.materials}, f)

    def query_known_materials(self, pname: str) -> List[str]:
        self.get_data_file(pname)
        return self.materials.copy() if self.materials else []

    def query_known_material(self, pname: str, material: str) -> bool:
        self.get_data_file(pname)
        return material in self.materials if self.materials else False

    def add_known_material(self, pname: str, material: str) -> bool:
        self.get_data_file(pname)
        if material in self.materials:
            return False
        self.materials.append(material)
        self.save_data_file(pname)
        return True

async def init(driver_instance):
    driver = driver_instance
    driver.cmr_library = CMRLibraryHandler()