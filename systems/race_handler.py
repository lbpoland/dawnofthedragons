from typing import Dict, List, Optional
from ..driver import driver, MudObject
from . import effects

class RaceHandler:
    def __init__(self):
        # Playable races from your list
        self.races: Dict[str, Dict] = {
            "human": {"stats": {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1}, "traits": ["versatile"], "languages": ["Common"], "playable": True, "desc": "Adaptable folk of Faerûn."},
            "elf": {"stats": {"dex": 2, "con": -2}, "traits": ["darkvision_60", "keen_senses"], "languages": ["Elvish", "Common"], "playable": True, "desc": "Graceful kin of Corellon."},
            "high elf": {"stats": {"int": 2, "con": -2}, "traits": ["darkvision_60", "arcane_aptitude"], "languages": ["Elvish", "Common"], "playable": True, "desc": "Masters of arcane lore."},
            "wild elf": {"stats": {"dex": 2, "cha": -2}, "traits": ["darkvision_60", "feral_instinct"], "languages": ["Elvish"], "playable": True, "desc": "Primal forest dwellers."},
            "wood elf": {"stats": {"dex": 2, "wis": 1, "int": -2}, "traits": ["darkvision_60", "woodland_stride"], "languages": ["Elvish", "Common"], "playable": True, "desc": "Guardians of the wilds."},
            "drow": {"stats": {"dex": 2, "cha": 1, "con": -2}, "traits": ["darkvision_120", "spell_resistance_5"], "languages": ["Elvish", "Drow Sign", "Undercommon"], "playable": True, "desc": "Dark kin of Lolth."},
            "duergar": {"stats": {"con": 2, "cha": -4}, "traits": ["darkvision_120", "stonecunning"], "languages": ["Dwarvish", "Undercommon"], "playable": True, "desc": "Gray dwarves of the deep."},
            "dwarf": {"stats": {"con": 2, "cha": -2}, "traits": ["stonecunning", "stability"], "languages": ["Dwarvish", "Common"], "playable": True, "desc": "Sons of Moradin."},
            "gnome": {"stats": {"int": 2, "str": -2}, "traits": ["tinker", "small_size"], "languages": ["Gnomish", "Common"], "playable": True, "desc": "Clever folk of Garl."},
            "halfling": {"stats": {"dex": 2, "str": -2}, "traits": ["lucky", "small_size"], "languages": ["Halfling", "Common"], "playable": True, "desc": "Nimble wanderers."},
            "orc": {"stats": {"str": 4, "int": -2, "cha": -2}, "traits": ["ferocity"], "languages": ["Orcish"], "playable": True, "desc": "Fierce spawn of Gruumsh."},
            "goblin": {"stats": {"dex": 2, "str": -2}, "traits": ["sneaky", "small_size"], "languages": ["Goblin"], "playable": True, "desc": "Cunning scavengers."},
            "dragonborn": {"stats": {"str": 2, "cha": 1}, "traits": ["breath_weapon"], "languages": ["Draconic", "Common"], "playable": True, "desc": "Draconic heirs of Bahamut."},
            "tiefling": {"stats": {"cha": 2, "wis": -2}, "traits": ["fiendish_resistance"], "languages": ["Infernal", "Common"], "playable": True, "desc": "Fiend-touched outcasts."},
        }
        # Additional FR races (NPCs or future playable) from https://forgottenrealms.fandom.com/wiki/Category:Races
        additional_races = {
            "aasimar": {"stats": {"wis": 2, "str": -2}, "traits": ["celestial_light"], "languages": ["Celestial", "Common"], "playable": False, "desc": "Blessed by the heavens."},
            "genasi_air": {"stats": {"dex": 2, "wis": -2}, "traits": ["levitate"], "languages": ["Auran", "Common"], "playable": False, "desc": "Children of the winds."},
            "kobold": {"stats": {"dex": 2, "str": -4}, "traits": ["trapmaking"], "languages": ["Draconic"], "playable": False, "desc": "Cunning dragon-kin."},
            "illithid": {"stats": {"int": 4, "con": -2}, "traits": ["mind_blast"], "languages": ["Undercommon"], "playable": False, "desc": "Mind flayers of the deep."},
            # Add 100+ more from wiki (e.g., beholder, centaur, yuan-ti) - truncated for brevity, fully sourced in design
        }
        self.races.update(additional_races)

    def add_race(self, name: str, stats_mod: Dict[str, int], traits: List[str], languages: List[str], playable: bool, desc: str):
        self.races[name] = {"stats": stats_mod, "traits": traits, "languages": languages, "playable": playable, "desc": desc}

    def query_race(self, name: str) -> Optional[Dict]:
        return self.races.get(name)

    def apply_race_effects(self, player: MudObject):
        race = self.races.get(player.race)
        if not race:
            return
        # Apply stat modifiers
        for stat, mod in race["stats"].items():
            player.stats[stat] = player.stats.get(stat, 13) + mod
        # Apply traits as effects
        for trait in race["traits"]:
            if trait == "darkvision_60":
                player.add_effect(effects.Effect("darkvision", duration=-1, strength=60))
            elif trait == "darkvision_120":
                player.add_effect(effects.Effect("darkvision", duration=-1, strength=120))
            elif trait == "stonecunning":
                player.skills["crafting.stone"] = player.skills.get("crafting.stone", 0) + 10
            # Add all traits from FR wiki (e.g., spell_resistance_5, breath_weapon)
        # Set languages
        player.languages = race["languages"]

race_handler = RaceHandler()