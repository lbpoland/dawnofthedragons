# /mnt/home2/mud/systems/languages.py
from typing import Dict, Optional
from ..driver import driver, Player, MudObject
import asyncio
import random
import json

class LanguageHandler:
    def __init__(self):
        self.languages = {
            "common": {"spoken": 100, "written": 100, "garble_obj": None, "native_to": ["human", "halfling", "gnome"]},
            "drow": {"spoken": 0, "written": 0, "garble_obj": "drow_garble", "native_to": ["drow"]},
            "elvish": {"spoken": 0, "written": 0, "garble_obj": "elvish_garble", "native_to": ["elf"]},
            "dwarvish": {"spoken": 0, "written": 0, "garble_obj": "dwarvish_garble", "native_to": ["dwarf"]},
            "draconic": {"spoken": 0, "written": 0, "garble_obj": "draconic_garble", "native_to": ["dragonborn"]},
            "orcish": {"spoken": 0, "written": 0, "garble_obj": "orcish_garble", "native_to": ["orc", "goblin"]},
            "abyssal": {"spoken": 0, "written": 0, "garble_obj": "abyssal_garble", "native_to": ["tiefling"]},
            "undercommon": {"spoken": 0, "written": 0, "garble_obj": "undercommon_garble", "native_to": ["drow"]},
            "giant": {"spoken": 0, "written": 0, "garble_obj": "giant_garble", "native_to": ["goliath"]}
        }
        self.grunt = {"spoken": 100, "written": 0, "garble_obj": "grunt_garble"}  # Universal but unintelligible
        self.garble_tables = {
            "drow_garble": {"A": "Z", "E": "Y", "I": "X", "O": "W", "U": "V"},
            "elvish_garble": {"A": "Q", "E": "P", "I": "O", "O": "N", "U": "M"},
            "dwarvish_garble": {"A": "R", "E": "S", "I": "T", "O": "U", "U": "V"},
            "draconic_garble": {"A": "H", "E": "J", "I": "K", "O": "L", "U": "M"},
            "orcish_garble": {"A": "G", "E": "F", "I": "D", "O": "C", "U": "B"},
            "abyssal_garble": {"A": "X", "E": "W", "I": "V", "O": "U", "U": "T"},
            "undercommon_garble": {"A": "Y", "E": "Z", "I": "W", "O": "V", "U": "U"},
            "giant_garble": {"A": "P", "E": "Q", "I": "R", "O": "S", "U": "T"},
            "grunt_garble": {"": lambda x: "".join(random.choices("grh", k=len(x)))}
        }
        self.teachers = {
            "waterdeep": {"npc": "Librarian", "teaches": ["common", "elvish", "dwarvish"]},
            "menzoberranzan": {"npc": "Drow Matron", "teaches": ["drow", "undercommon"]}
        }

    async def init(self, driver_instance):
        self.driver = driver_instance
        for player in self.driver.players.values():
            race = player.attrs.get("race", "human")
            for lang, data in self.languages.items():
                if race in data.get("native_to", []):
                    data["spoken"] = 100
                    data["written"] = 100
                    break

    async def set_language(self, player: Player, lang: str) -> bool:
        if lang in self.languages or lang == "grunt":
            player.attrs["current_lang"] = lang
            await player.send(f"You set your language to {lang}.")
            return True
        await player.send("Unknown language!")
        return False

    async def speak(self, player: Player, msg: str) -> str:
        current_lang = player.attrs.get("current_lang", "common")
        if current_lang == "grunt":
            return await self.garble_text(msg, "grunt_garble", player)
        lang_data = self.languages.get(current_lang, {"spoken": 0})
        if lang_data["spoken"] < 60:
            await player.send("Your speech is unintelligible to others!")
            return ""
        garbled = await self.garble_text(msg, current_lang, player)
        for oid in player.location.attrs.get("contents", []):
            if oid in self.driver.objects and oid != player.oid:
                await self.driver.call_other(oid, "receive_message", player, garbled)
        return f"You say in {current_lang}: {msg}"

    async def write(self, player: Player, msg: str) -> str:
        current_lang = player.attrs.get("current_lang", "common")
        lang_data = self.languages.get(current_lang, {"written": 0})
        if lang_data["written"] == 0:
            await player.send("You cannot write this language!")
            return ""
        garbled = await self.garble_text(msg, current_lang, player)
        return f"You write in {current_lang}: {garbled}"

    async def garble_text(self, text: str, lang: str, player: Player) -> str:
        if lang not in self.garble_tables:
            return text
        garble_table = self.garble_tables.get(lang, {})
        words = text.split()
        garbled_words = []
        for word in words:
            if random.random() < max(0.2, 1 - (player.attrs.get("skills", {}).get(f"{lang}_spoken", 0) / 100)):
                if callable(garble_table.get("")):
                    garbled_words.append(garble_table[""](word))
                else:
                    garbled = "".join(garble_table.get(c, c) for c in word)
                    garbled_words.append(garbled)
            else:
                garbled_words.append(word)
        return " ".join(garbled_words)

    async def learn_language(self, player: Player, lang: str, mode: str) -> bool:
        if lang not in self.languages:
            await player.send("Unknown language!")
            return False
        teacher = self.find_teacher(player.location.oid)
        if not teacher or lang not in teacher["teaches"]:
            await player.send("No teacher available for this language here!")
            return False
        current_spoken = self.languages[lang]["spoken"]
        current_written = self.languages[lang]["written"]
        if mode == "spoken" and current_spoken < 90:
            self.languages[lang]["spoken"] = min(90, current_spoken + 10)
            await player.send(f"You gain 10 spoken {lang} levels (now {self.languages[lang]['spoken']}).")
        elif mode == "written" and current_written < 90:
            self.languages[lang]["written"] = min(90, current_written + 10)
            await player.send(f"You gain 10 written {lang} levels (now {self.languages[lang]['written']}).")
        return True

    def find_teacher(self, room_oid: str) -> Optional[dict]:
        for zone, teacher in self.teachers.items():
            if zone in room_oid.lower():
                return teacher
        return None

# Initialize language handler
language_handler = LanguageHandler()

async def init(driver_instance):
    await language_handler.init(driver_instance)
