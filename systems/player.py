# /mnt/home2/mud/systems/player.py
# Imported to: driver.py, login_handler.py, living.py
# Imports from: driver.py, living.py, skills.py, guild_handler.py, inventory.py, race_handler.py, magic_handler.py, rituals_handler.py, deity_handler.py, combat.py, effects.py

from typing import Dict, Optional
from ..driver import driver, MudObject, Player
from .living import Living
from .skills import SkillsHandler
from .race_handler import race_handler
from .magic_handler import magic_handler
from .rituals_handler import rituals_handler
from .deity_handler import deity_handler
from .combat import combat_handler, CombatSpecial
from .effects import EffectsMixin
import asyncio
import time

class Player(Living, EffectsMixin):
    def __init__(self, oid: str = "player", name: str = "player"):
        super().__init__(oid, name)
        self.time_on = time.time()
        self.max_deaths = 7
        self.monitor = 0
        self.refresh_time = 0
        self.start_time = time.time()
        self.creator = False
        self.deaths = 0
        self.last_log_on = time.time()
        self.no_logins = 0
        self.activity_counter = 0
        self.flags = 0  # PLAYER_KILLER_FLAG = 1
        self.cap_name = name.capitalize()
        self.last_on_from = ""
        self.pinfo = {
            "hb_num": 0,
            "level": 0,
            "level_time": 0,
            "save_inhibit": 1,
            "update_tmps_call_out": None,
            "last_save": 0,
            "snoopee": None,
            "titles": {}
        }
        # Combat-related attributes
        self.attrs["gp"] = 100  # Guild points for spells/rituals
        self.attrs["max_gp"] = 100
        self.attrs["limbs"] = ["left hand", "right hand"]
        self.attrs["holding"] = [None, None]
        self.attrs["tactics"] = None  # Set in setup_player
        self.attrs["specials"] = []
        self.attrs["concentrating"] = None
        self.attrs["action_defecit"] = 0
        # New attributes for races, magic, rituals, deities
        self.race = "human"  # Default, updated via choose_race
        self.spells: list = []
        self.faith = 100
        self.max_faith = 100
        self.rituals: list = []
        self.deity = None
        self.favor = 0
        self.piety = 0
        self.skills_handler = SkillsHandler()
        self.setup_player()

    def setup_player(self):
        self.add_property("player", 1)
        self.set_max_hp(100)  # From Living
        self.set_hp(100)
        self.set_max_sp(50)
        self.set_sp(50)
        self.set_wimpy(20)
        self.attrs["Str"] = 13
        self.attrs["Dex"] = 13
        self.attrs["Int"] = 13
        self.attrs["Con"] = 13
        self.attrs["Wis"] = 13
        self.attrs["tactics"] = combat_handler.Tactics()  # Default tactics
        self.skills_handler.setup(self)
        race_handler.apply_race_effects(self)  # Apply default human traits
        self.attrs["effects"] = {}  # For EffectsMixin

    async def move_player_to_start(self, name: str, new_flag: bool, c_name: str, ident: str, go_invis: int):
        self.set_name(name)
        self.cap_name = c_name
        if not new_flag:
            await driver.player_handler.restore_player(self)
            if go_invis == 2 and self.query_lord():
                self.set_invis(2)
            elif go_invis == 1:
                self.set_invis(1)
        self.disallow_save()
        self.no_logins += 1
        self.last_on_from = f"{self.query_ip_name()} ({self.query_ip_number()})"
        self.time_on = time.time() if new_flag else 0 - time.time()
        if new_flag:
            self.add_property("new player", 1)
        await asyncio.sleep(0)
        await self.continue_start_player()

    async def continue_start_player(self):
        self.start_player()
        await self.move_to_start_pos()
        await driver.send(self, "Welcome to the shadowed lands of Faerûn!\n")

    def start_player(self):
        self.enable_commands()
        self.add_command("save", "", self.save)
        self.add_command("quit", "", lambda p, _: self.quit_alt(-1))
        self.add_command("wimpy", "<word'number'>", self.toggle_wimpy)
        self.add_command("cast", "<word'spell'> <word'target'>", self.cast_spell)
        self.add_command("perform", "<word'ritual'> <word'target'>", self.perform_ritual)
        self.add_command("worship", "<word'deity'>", self.worship_deity)
        self.set_heart_beat(1)

    async def save(self, player: Player, arg: str) -> bool:
        if self.pinfo["save_inhibit"]:
            await self.send("Cannot save yet—your essence is still forming.\n")
            return False
        if time.time() - self.time_on < 1800:
            await self.send("You’re too new to Faerûn to save yet.\n")
            return False
        await self.send("Saving your soul to the Ethereal Veil...\n")
        await self.save_me()
        return True

    async def save_me(self):
        if self.query_property("guest"):
            await self.send("Guests leave no mark on Faerûn.\n")
            return
        self.create_auto_load(self.query_carried())
        self.time_on -= time.time()
        await driver.player_handler.save_player(self)
        self.time_on += time.time()

    async def quit_alt(self, verbose: int) -> bool:
        if self.pinfo["save_inhibit"]:
            await self.send("Cannot quit yet—your inventory binds you.\n")
            return False
        if self.query_attacker_list():
            await self.send("You cannot flee Faerûn mid-battle. Use 'stop'.\n")
            return False
        self.update_activity(False)
        self.last_log_on = time.time()
        await self.send("A Netherese portal opens, pulling you from Faerûn.\n")
        await self.broadcast(f"{self.cap_name} departs under the Veil’s shroud.\n")
        await self.move("/room/departures")
        await self.save_me()
        await driver.remove_object(self)
        return True

    async def second_life(self):
        self.add_property("dead", time.time())
        self.deaths += 1
        corpse = self.make_corpse()
        if self.deaths > self.max_deaths or (self.deity and self.favor < -50):
            await self.send("Your soul fades into the Fugue Plane—your tale ends.\n")
            await driver.broadcast(f"{self.cap_name} meets their final doom.\n")
            await corpse.move("/room/morgue")
        else:
            await corpse.move(self.environment())
            if self.deity and self.favor > 0:
                await self.send(f"{self.deity} grants you a flicker of life.\n")
                self.favor -= 10  # Deity favor cost
                self.remove_ghost()
        await self.save_me()
        return corpse

    def remove_ghost(self):
        if self.deaths > self.max_deaths:
            return
        self.remove_property("dead")
        self.set_hp(max(1, self.query_hp()))
        await self.send(f"You return to flesh under {self.deity or 'the Veil'}’s grace.\n")
        await self.broadcast(f"{self.cap_name} rises anew in Faerûn!\n")

    def update_activity(self, logon: bool):
        if logon:
            self.activity_counter += 3
        else:
            self.activity_counter += 2 * ((time.time() - self.last_log_on) // 3600)
        self.activity_counter = min(0, max(-55, self.activity_counter))

    async def heart_beat(self):
        await super().heart_beat()
        if not self.is_interactive() and time.time() - self.last_command > 1800:
            await self.send("Idleness claims you—farewell from Faerûn!\n")
            await self.quit_alt(-1)
        # Regen gp and faith
        self.attrs["gp"] = min(self.attrs["max_gp"], self.attrs["gp"] + 1)
        self.faith = min(self.max_faith, self.faith + 1)

    def query_level(self) -> int:
        if time.time() - self.pinfo["level_time"] > 60:
            guild = driver.load_object(self.query_guild()) if self.query_guild() else None
            self.pinfo["level"] = guild.query_level(self) if guild else 0
            self.pinfo["level_time"] = time.time()
        return self.pinfo["level"]

    def set_name(self, name: str):
        super().set_name(name)
        self.cap_name = name.capitalize()

    def query_cap_name(self) -> str:
        return self.cap_name

    def toggle_wimpy(self, player: Player, arg: str) -> bool:
        if not arg.isdigit() or not 0 <= int(arg) <= 30:
            return False
        self.set_wimpy(int(arg))
        return True

    def disallow_save(self):
        self.pinfo["save_inhibit"] = 1

    def allow_save(self):
        self.pinfo["save_inhibit"] = 0

    # New Methods for Integration
    def query_skill(self, skill: str) -> int:
        return self.skills_handler.query_skill(self, skill)

    async def cast_spell(self, player: Player, args: str) -> bool:
        parts = args.split(" on ")
        spell_name = parts[0].strip()
        target_name = parts[1].strip() if len(parts) > 1 else None
        target = self.find_target(target_name) if target_name else None
        if spell_name not in self.spells:
            await self.send(f"You don’t know the spell '{spell_name}'.\n")
            return False
        success = await magic_handler.cast_spell(self, spell_name, target)
        return success

    async def perform_ritual(self, player: Player, args: str) -> bool:
        parts = args.split(" on ")
        ritual_name = parts[0].strip()
        target_name = parts[1].strip() if len(parts) > 1 else None
        target = self.find_target(target_name) if target_name else None
        if ritual_name not in self.rituals:
            await self.send(f"You haven’t learned the ritual '{ritual_name}'.\n")
            return False
        success = await rituals_handler.perform_ritual(self, ritual_name, target)
        if success and self.deity:
            self.piety += 1  # Increase piety per ritual
        return success

    async def worship_deity(self, player: Player, deity_name: str) -> bool:
        if deity_handler.worship(self, deity_name):
            self.deity = deity_name
            await self.send(f"You pledge yourself to {deity_name}, their power stirring within.\n")
            return True
        await self.send(f"{deity_name} does not heed your call.\n")
        return False

    def find_target(self, target_name: str) -> Optional[MudObject]:
        for oid in self.location.attrs.get("contents", []):
            if oid in self.driver.objects and self.driver.objects[oid].name.lower() == target_name.lower():
                return self.driver.objects[oid]
        return None

    def choose_race(self, race: str):
        if race in race_handler.races and race_handler.races[race]["playable"]:
            self.race = race
            race_handler.apply_race_effects(self)
            return True
        return False

async def init(driver_instance):
    global driver
    driver = driver_instance
    driver.add_object(Player())