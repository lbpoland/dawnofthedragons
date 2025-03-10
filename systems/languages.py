# /mnt/home2/mud/systems/languages.py
# Imported to: object.py, player.py
# Imports from: driver.py, taskmaster.py

from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject, Player
import asyncio
import random
import time

class LanguageHandler:
    def __init__(self):
        # Languages: name -> {spoken, written, magic, native_to, accent_regions}
        self.languages = {
            "common": {"spoken": 100, "written": 100, "magic": False, "native_to": ["human", "halfling", "gnome"], "accent_regions": ["waterdeep", "baldurs_gate"]},
            "elvish": {"spoken": 0, "written": 0, "magic": True, "native_to": ["elf", "high elf", "wood elf", "wild elf"], "accent_regions": ["evermeet", "cormanthor"]},
            "drow": {"spoken": 0, "written": 0, "magic": True, "native_to": ["drow"], "accent_regions": ["menzoberranzan"]},
            "dwarvish": {"spoken": 0, "written": 0, "magic": False, "native_to": ["dwarf", "duergar"], "accent_regions": ["mithral_hall", "gauntlgrym"]},
            "draconic": {"spoken": 0, "written": 0, "magic": True, "native_to": ["dragonborn"], "accent_regions": ["tymanther"]},
            "orcish": {"spoken": 0, "written": 0, "magic": False, "native_to": ["orc", "goblin"], "accent_regions": ["many_arrows"]},
            "abyssal": {"spoken": 0, "written": 0, "magic": True, "native_to": ["tiefling"], "accent_regions": ["nine_hells"]},
            "undercommon": {"spoken": 0, "written": 0, "magic": False, "native_to": ["drow", "duergar"], "accent_regions": ["underdark"]},
            "giant": {"spoken": 0, "written": 0, "magic": False, "native_to": ["goliath"], "accent_regions": ["hartsvale"]},
            "celestial": {"spoken": 0, "written": 0, "magic": True, "native_to": ["aasimar"], "accent_regions": ["mount_celestia"]},
            "infernal": {"spoken": 0, "written": 0, "magic": True, "native_to": ["tiefling"], "accent_regions": ["nine_hells"]},
            "sylvan": {"spoken": 0, "written": 0, "magic": True, "native_to": ["wood elf", "fey"], "accent_regions": ["feywild"]},
            "gnomish": {"spoken": 0, "written": 0, "magic": False, "native_to": ["gnome"], "accent_regions": ["lanth"]},
            "halfling": {"spoken": 0, "written": 0, "magic": False, "native_to": ["halfling"], "accent_regions": ["luiren"]},
            "grunt": {"spoken": 100, "written": 0, "magic": False, "native_to": [], "accent_regions": []},
        }
        self.garble_tables = {
            "drow": {"A": "Z", "E": "Y", "I": "X", "O": "W", "U": "V"},
            "elvish": {"A": "Q", "E": "P", "I": "O", "O": "N", "U": "M"},
            "dwarvish": {"A": "R", "E": "S", "I": "T", "O": "U", "U": "V"},
            "draconic": {"A": "H", "E": "J", "I": "K", "O": "L", "U": "M"},
            "orcish": {"A": "G", "E": "F", "I": "D", "O": "C", "U": "B"},
            "abyssal": {"A": "X", "E": "W", "I": "V", "O": "U", "U": "T"},
            "undercommon": {"A": "Y", "E": "Z", "I": "W", "O": "V", "U": "U"},
            "giant": {"A": "P", "E": "Q", "I": "R", "O": "S", "U": "T"},
            "celestial": {"A": "B", "E": "C", "I": "D", "O": "E", "U": "F"},
            "infernal": {"A": "T", "E": "S", "I": "R", "O": "Q", "U": "P"},
            "sylvan": {"A": "L", "E": "M", "I": "N", "O": "O", "U": "P"},
            "gnomish": {"A": "K", "E": "J", "I": "I", "O": "H", "U": "G"},
            "halfling": {"A": "F", "E": "E", "I": "D", "O": "C", "U": "B"},
            "grunt": {"": lambda x: "".join(random.choices("grh", k=len(x)))}
        }
        self.teachers = {
            "waterdeep": {"npc": "Librarian Elminster", "teaches": ["common", "elvish", "dwarvish", "draconic"]},
            "menzoberranzan": {"npc": "Drow Matron Quenthel", "teaches": ["drow", "undercommon"]},
            "evermeet": {"npc": "High Mage Aerith", "teaches": ["elvish", "sylvan"]},
            "mithral_hall": {"npc": "Runesmith Bruenor", "teaches": ["dwarvish", "giant"]},
            "tymanther": {"npc": "Dragon Sage Tiamat", "teaches": ["draconic"]},
            "underdark": {"npc": "Svirfneblin Elder", "teaches": ["undercommon"]},
        }
        self.player_skills: Dict[str, Dict[str, Tuple[int, int]]] = {}  # player_name: {lang: (spoken, written)}

    async def init(self, driver_instance):
        self.driver = driver_instance
        for player in self.driver.players.values():
            race = player.attrs.get("race", "human")
            region = player.attrs.get("region", "waterdeep")
            for lang, data in self.languages.items():
                if race in data["native_to"]:
                    self.player_skills[player.name] = {lang: (100, 100)}
                    player.attrs["accent"] = self.get_accent(lang, region)
                    break
            if player.name not in self.player_skills:
                self.player_skills[player.name] = {"common": (100, 100)}
                player.attrs["accent"] = "generic"

    def get_accent(self, lang: str, region: str) -> str:
        # 2025 Discworld-style accents tied to regions
        accents = {
            "common": {"waterdeep": "Waterdhavian drawl", "baldurs_gate": "Gateside twang"},
            "elvish": {"evermeet": "Evermeetan lilt", "cormanthor": "Cormanthan trill"},
            "drow": {"menzoberranzan": "Menzoberranzan hiss"},
            "dwarvish": {"mithral_hall": "Mithral rumble", "gauntlgrym": "Gauntlgrym growl"},
            "draconic": {"tymanther": "Tymantheran roar"},
            "orcish": {"many_arrows": "Many-Arrows grunt"},
            "abyssal": {"nine_hells": "Hellish screech"},
            "undercommon": {"underdark": "Underdark whisper"},
            "giant": {"hartsvale": "Hartsvale boom"},
        }
        return accents.get(lang, {}).get(region, "generic")

    async def set_language(self, player: Player, lang: str) -> bool:
        if lang in self.languages:
            player.attrs["current_lang"] = lang
            await player.send(f"You set your language to {lang} with a {player.attrs['accent']}.")
            return True
        await player.send("Unknown language!")
        return False

    async def speak(self, player: Player, msg: str) -> str:
        current_lang = player.attrs.get("current_lang", "common")
        skills = self.player_skills.get(player.name, {}).get(current_lang, (0, 0))
        if current_lang == "grunt":
            garbled = await self.garble_text("grunt", msg, player)
            await self.broadcast_speech(player, garbled, "grunts")
            return f"You grunt: {msg}"
        if skills[0] < 60:
            await player.send("Your speech is too broken to be understood!")
            return ""
        garbled = await self.garble_text(current_lang, msg, player)
        accent = player.attrs.get("accent", "generic")
        await self.broadcast_speech(player, garbled, f"speaks with a {accent}")
        return f"You say in {current_lang} with a {accent}: {msg}"

    async def broadcast_speech(self, player: Player, msg: str, verb: str):
        for oid in player.location.attrs.get("contents", []):
            if oid in self.driver.objects and oid != player.oid:
                target = self.driver.objects[oid]
                if isinstance(target, Player):
                    understood = await self.can_understand(target, player.attrs["current_lang"])
                    display_msg = msg if understood else await self.garble_text(player.attrs["current_lang"], msg, target)
                    await target.send(f"{player.cap_name} {verb}: {display_msg}")

    async def write(self, player: Player, msg: str) -> str:
        current_lang = player.attrs.get("current_lang", "common")
        skills = self.player_skills.get(player.name, {}).get(current_lang, (0, 0))
        if skills[1] < 60:
            await player.send("Your writing is illegible!")
            return ""
        return f"Written in {current_lang}: {msg}"

    async def garble_text(self, lang: str, text: str, player: Player) -> str:
        skills = self.player_skills.get(player.name, {}).get(lang, (0, 0))
        if skills[0] >= 100:  # Full fluency, no garble
            return text
        garble_table = self.garble_tables.get(lang, {})
        if not garble_table:
            return text
        words = text.split()
        garbled_words = []
        proficiency = min(1.0, skills[0] / 100)
        for word in words:
            if random.random() < (1 - proficiency):  # Garble chance decreases with skill
                if callable(garble_table.get("")):
                    garbled_words.append(garble_table[""](word))
                else:
                    garbled = "".join(garble_table.get(c.upper(), c) for c in word)
                    garbled_words.append(garbled)
            else:
                garbled_words.append(word)
        return " ".join(garbled_words)

    async def can_understand(self, player: Player, lang: str) -> bool:
        skills = self.player_skills.get(player.name, {}).get(lang, (0, 0))
        return skills[0] >= 60  # Minimum to understand speech

    async def learn_language(self, player: Player, lang: str, mode: str) -> bool:
        if lang not in self.languages or lang == "grunt":
            await player.send("Unknown or unlearnable language!")
            return False
        teacher = self.find_teacher(player.location.oid)
        if not teacher or lang not in teacher["teaches"]:
            await player.send("No teacher available here for that language!")
            return False
        skills = self.player_skills.setdefault(player.name, {})
        current = skills.get(lang, (0, 0))
        people_points = player.skills_handler.query_skill("people.points")
        cap = min(90, people_points * 2)  # 2025 TM cap based on people.points
        if mode == "spoken" and current[0] < cap:
            new_spoken = min(cap, current[0] + 10)
            skills[lang] = (new_spoken, current[1])
            await driver.tasker.award_made(player.name, teacher["npc"], f"{lang}_spoken", new_spoken)
            await player.send(f"You gain 10 spoken {lang} levels (now {new_spoken}).")
            return True
        elif mode == "written" and current[1] < cap:
            new_written = min(cap, current[1] + 10)
            skills[lang] = (current[0], new_written)
            await driver.tasker.award_made(player.name, teacher["npc"], f"{lang}_written", new_written)
            await player.send(f"You gain 10 written {lang} levels (now {new_written}).")
            return True
        await player.send(f"You’ve reached your current {mode} cap for {lang}!")
        return False

    def find_teacher(self, room_oid: str) -> Optional[dict]:
        for zone, teacher in self.teachers.items():
            if zone in room_oid.lower():
                return teacher
        return None

    def query_language_size(self, lang: str, text: str) -> int:
        # 2025: Size varies by language complexity
        base = len(text)
        if lang in ["elvish", "drow", "draconic", "sylvan"]:
            return base * 2  # Intricate scripts
        if lang in ["dwarvish", "giant"]:
            return base * 3  # Blocky runes
        return base

    def squidge_text(self, lang: str, text: str, max_size: int) -> str:
        size_per_char = self.query_language_size(lang, "a")
        return text[:int(max_size // size_per_char)]

async def init(driver_instance):
    global LANGUAGES
    LANGUAGES = LanguageHandler()
    await LANGUAGES.init(driver_instance)
    driver.languages = LANGUAGES