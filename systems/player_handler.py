# /mnt/home2/mud/systems/player_handler.py
# Imported to: quest.py, login_handler.py, living.py
# Imports from: driver.py

from typing import Dict, List, Optional, Union
from ..driver import driver, Player
import asyncio
import os
import time
import json

class PlayerHandler:
    SAVE_VERSION = "2025.03"  # Version for save file compatibility

    def __init__(self):
        self.players: Dict[str, Dict] = {}  # {player_name: {oid, last_login, attrs, static_load, dynamic_load}}
        self.banned: List[str] = []
        self.player_dir: str = "/save/players"

    async def init(self, driver_instance):
        """Initializes the player handler with Faerûn’s ethereal records."""
        self.driver = driver_instance
        if not os.path.exists(self.player_dir):
            os.makedirs(self.player_dir)
        for filename in os.listdir(self.player_dir):
            if filename.endswith(".o"):
                name = filename[:-2].lower()
                try:
                    data = driver.load_object(f"{self.player_dir}/{name}.o")
                    if data and data.get("version") == self.SAVE_VERSION:
                        self.players[name] = data
                    else:
                        driver.log_file("PLAYER_ERRORS", f"{time.ctime()} Corrupted/old save for {name}, skipping.\n")
                except Exception as e:
                    driver.log_file("PLAYER_ERRORS", f"{time.ctime()} Failed to load {name}: {str(e)}\n")
        driver.player_handler = self

    def add_player(self, player: Player) -> bool:
        """Adds a new soul to Faerûn’s annals."""
        name = player.name.lower()
        if name in self.players or name in self.banned:
            return False
        self.players[name] = {
            "oid": player.oid,
            "last_login": int(time.time()),
            "attrs": player.attrs.copy(),
            "static_load": player.query_static_auto_load(),
            "dynamic_load": player.query_dynamic_auto_load(),
            "race": player.race,
            "spells": player.spells.copy(),
            "faith": player.faith,
            "max_faith": player.max_faith,
            "rituals": player.rituals.copy(),
            "deity": player.deity,
            "favor": player.favor,
            "piety": player.piety,
            "version": self.SAVE_VERSION
        }
        self.save_player(player)
        return True

    def remove_player(self, name: str) -> bool:
        """Banishes a soul from Faerûn’s records."""
        name = name.lower()
        if name not in self.players:
            return False
        del self.players[name]
        save_path = f"{self.player_dir}/{name}.o"
        if os.path.exists(save_path):
            os.remove(save_path)
            driver.log_file("PLAYER_EVENTS", f"{time.ctime()} {name}’s record sundered from the Veil.\n")
        return True

    def query_player(self, name: str) -> Optional[Dict]:
        """Peers into the Veil for a soul’s record."""
        return self.players.get(name.lower())

    def save_player(self, player: Union[Player, str]):
        """Etches a soul’s essence into the Ethereal Veil."""
        if isinstance(player, str):
            name = player.lower()
        else:
            name = player.name.lower()
        if name in self.players:
            if isinstance(player, Player):
                self.players[name].update({
                    "attrs": player.attrs.copy(),
                    "static_load": player.query_static_auto_load(),
                    "dynamic_load": player.query_dynamic_auto_load(),
                    "race": player.race,
                    "spells": player.spells.copy(),
                    "faith": player.faith,
                    "max_faith": player.max_faith,
                    "rituals": player.rituals.copy(),
                    "deity": player.deity,
                    "favor": player.favor,
                    "piety": player.piety,
                    "last_login": int(time.time())
                })
            driver.save_object(f"{self.player_dir}/{name}.o", self.players[name])

    async def load_player(self, name: str) -> Optional[Player]:
        """Summons a soul back to Faerûn from the Veil (2025 update)."""
        name = name.lower()
        if name in self.banned:
            return None
        player_data = self.query_player(name)
        if not player_data or player_data.get("version") != self.SAVE_VERSION:
            return None

        player = driver.find_player(name)
        if not player:
            player = Player(player_data["oid"], name)
            player.attrs.update(player_data["attrs"])
            player.init_static_arg(player_data["static_load"])
            player.init_dynamic_arg(player_data["dynamic_load"])
            player.race = player_data["race"]
            race_handler.apply_race_effects(player)
            player.spells = player_data["spells"]
            player.faith = player_data["faith"]
            player.max_faith = player_data["max_faith"]
            player.rituals = player_data["rituals"]
            player.deity = player_data["deity"]
            player.favor = player_data["favor"]
            player.piety = player_data["piety"]
            await player.init(self.driver)
        self.players[name]["last_login"] = int(time.time())
        self.save_player(name)

        await player.send("Welcome back, traveler of Faerûn, under Mystra’s ethereal gaze.\n")
        return player

    def ban_player(self, name: str):
        """Casts a soul into the Fugue Plane’s exile."""
        name = name.lower()
        if name not in self.banned:
            self.banned.append(name)
            driver.log_file("BANS", f"{time.ctime()} {name} banished to the Fugue Plane.\n")

    def unban_player(self, name: str) -> bool:
        """Restores a soul from exile under Kelemvor’s judgment."""
        name = name.lower()
        if name in self.banned:
            self.banned.remove(name)
            driver.log_file("BANS", f"{time.ctime()} {name} redeemed from the Fugue Plane.\n")
            return True
        return False

    def query_banned(self) -> List[str]:
        """Lists souls barred from Faerûn’s weave."""
        return self.banned.copy()

    async def update_player(self, player: Player):
        """Refreshes a soul’s mark in the Veil’s tapestry."""
        name = player.name.lower()
        if name in self.players:
            self.players[name].update({
                "attrs": player.attrs.copy(),
                "static_load": player.query_static_auto_load(),
                "dynamic_load": player.query_dynamic_auto_load(),
                "race": player.race,
                "spells": player.spells.copy(),
                "faith": player.faith,
                "max_faith": player.max_faith,
                "rituals": player.rituals.copy(),
                "deity": player.deity,
                "favor": player.favor,
                "piety": player.piety,
                "last_login": int(time.time())
            })
            self.save_player(player)

player_handler = PlayerHandler()

async def init(driver_instance):
    await player_handler.init(driver_instance)