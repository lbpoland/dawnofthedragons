# /mnt/home2/mud/systems/cmr_handler.py
# Imported to: object.py
# Imports from: driver.py, cmr_library.py

from typing import Dict, List, Tuple, Optional
from ..driver import driver, MudObject, Player
from .cmr_library import CMRLibraryHandler
import json
import os

SAVE_FILE = "/save/cmr_handler.json"
LEARNT = 99  # Special value for learnt-only materials

# 2025 CMR constants (simplified from cmr.h, colour.h)
COLOURS = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "grey", "orange", "purple", "brown", "pink", "violet", "indigo", "teal"]
MODIFIERS = ["", "light", "dark", "deep", "pale"]
MATERIALS = ["mineral", "metal", "wood", "cloth", "leather", "gem", "liquid", "gas"]
MATERIAL_ADJECTIVES = ["rocky", "metallic", "wooden", "fabric", "leathery", "gemlike", "fluid", "gaseous"]
SKILLS = ["crafts.materials", "crafts.smithing", "crafts.carpentry", "crafts.weaving", "crafts.leatherwork", "crafts.jewellery"]
ANSI_COLOURS = ["\033[30m", "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[35m", "\033[36m", "\033[37m", "\033[90m", "\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m", "\033[97m"]

class CMRHandler:
    def __init__(self):
        self.colour_names: List[str] = []
        self.colour_details: Dict[str, Tuple[int, int, int]] = {}  # (fine, crude, crafts_thresh)
        self.material_names: List[str] = []
        self.material_details: Dict[str, Tuple[int, int, int, int]] = {}  # (colour, type, skill_reqd, skill_thresh)
        self.load_cmr_handler()

    def load_cmr_handler(self):
        if os.path.exists(SAVE_FILE) and os.path.getsize(SAVE_FILE) > 0:
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.colour_names = data["colour_names"]
                self.colour_details = {k: tuple(v) for k, v in data["colour_details"].items()}
                self.material_names = data["material_names"]
                self.material_details = {k: tuple(v) for k, v in data["material_details"].items()}

    def save_cmr_handler(self):
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
        with open(SAVE_FILE, 'w') as f:
            json.dump({
                "colour_names": self.colour_names,
                "colour_details": {k: list(v) for k, v in self.colour_details.items()},
                "material_names": self.material_names,
                "material_details": {k: list(v) for k, v in self.material_details.items()}
            }, f)

    def add_colour(self, word: str, fine: int, crude: int, crafts_thresh: int) -> str:
        if word in self.colour_names:
            return "colour already exists"
        self.colour_names.append(word)
        self.colour_details[word] = (fine, crude, crafts_thresh)
        self.save_cmr_handler()
        return f"the colour {word}, a shade of {('pure' if fine == crude else MODIFIERS[fine])} {COLOURS[crude]}, with threshold of {crafts_thresh} crafts.points"

    def query_colour_details(self, word: str) -> Tuple[int, ...]:
        return self.colour_details.get(word, (-1,))

    def delete_colour(self, word: str) -> bool:
        if word not in self.colour_names:
            return False
        self.colour_names.remove(word)
        self.colour_details.pop(word, None)
        self.save_cmr_handler()
        return True

    def query_colour_names(self) -> List[str]:
        return self.colour_names.copy()

    def identify_colour(self, word: str, player: Optional[Player]) -> str:
        if word not in self.colour_names:
            return "unknown colour"
        if not player:
            return word
        fine, crude, thresh = self.colour_details[word]
        crafts_points = player.skills_handler.query_skill("crafts.points") if player else 0
        if crafts_points > thresh:
            return word
        elif crafts_points > thresh // 2:
            return f"{('pure' if fine == crude else MODIFIERS[fine])} {COLOURS[crude]}"
        return COLOURS[crude]

    def add_material(self, word: str, colour: int, type_: int, skill_reqd: int, skill_thresh: int) -> str:
        if word in self.material_names:
            return "material already exists"
        self.material_names.append(word)
        self.material_details[word] = (colour, type_, skill_reqd, skill_thresh)
        self.save_cmr_handler()
        text = " that is always recognised" if not skill_reqd else \
               " that is recognised through knowledge" if skill_reqd == LEARNT else \
               f" that has a threshold of {skill_thresh} in {SKILLS[skill_reqd]}"
        return f"{word}, a{'n' if colour == 9 else ''} {COLOURS[colour]} {MATERIALS[type_]}{text}"

    def query_material_details(self, word: str) -> Tuple[int, ...]:
        return self.material_details.get(word, (-1,))

    def delete_material(self, word: str) -> bool:
        if word not in self.material_names:
            return False
        self.material_names.remove(word)
        self.material_details.pop(word, None)
        self.save_cmr_handler()
        return True

    def query_material_names(self) -> List[str]:
        return self.material_names.copy()

    def identify_material(self, word: str, player: Optional[Player], article: bool) -> str:
        if word not in self.material_names:
            return "unknown material"
        colour, type_, skill_reqd, skill_thresh = self.material_details[word]
        prefix = f"a{'n' if colour == 9 else ''} " if article else ""
        if not skill_reqd or not player:
            return word
        if skill_reqd == LEARNT:
            if driver.cmr_library.query_known_material(player.name, word):
                return word
            return f"{prefix}{COLOURS[colour]} {MATERIALS[type_]}"
        bonus = player.skills_handler.query_skill_bonus(SKILLS[skill_reqd]) if 0 <= skill_reqd < len(SKILLS) else 0
        return word if bonus > skill_thresh else f"{prefix}{COLOURS[colour]} {MATERIALS[type_]}"

    def query_material_adjective(self, word: str) -> str:
        if word not in self.material_names:
            return "an unknown material"
        colour, type_, _, _ = self.material_details[word]
        return f"{COLOURS[colour]} {MATERIAL_ADJECTIVES[type_]}"

    def query_material_ansi_colour(self, word: str) -> str:
        if word not in self.material_names:
            return ""
        colour, _, _, _ = self.material_details[word]
        return ANSI_COLOURS[colour]

async def init(driver_instance):
    global CMR_HANDLER
    driver = driver_instance
    CMR_HANDLER = CMRHandler()
    driver.cmr_handler = CMR_HANDLER