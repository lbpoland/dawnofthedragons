# Imported to: combat.py, options.py, taskmaster.py
# Imports from: driver.py
# /mnt/home2/mud/systems/tactics.py
from typing import Dict, Optional
from ..driver import driver, Player, MudObject
import asyncio

class Tactics:
    def __init__(self):
        self.attitude: str = "neutral"
        self.response: str = "neutral"
        self.parry: str = "both"
        self.attack: str = "both"
        self.parry_unarmed: bool = False
        self.mercy: str = "ask"
        self.focus_zone: str = "none"
        self.ideal_distance: str = "medium"  # 2025: string options over int
        self.mystra_favor: int = 0  # Forgotten Realms: bonus to tactics

class TacticsHandler:
    ATTITUDE_OPTIONS = ["insane", "offensive", "neutral", "defensive", "wimp"]
    RESPONSE_OPTIONS = ["parry", "dodge", "both", "neutral"]
    PARRY_OPTIONS = ["left", "right", "both"]
    ATTACK_OPTIONS = ["left", "right", "both"]
    MERCY_OPTIONS = ["always", "never", "ask"]
    FOCUS_OPTIONS = ["none", "head", "chest", "arms", "legs"]  # Simplified for 2025
    DISTANCE_OPTIONS = ["close", "medium", "long", "none"]  # 2025 update
    
    def __init__(self):
        self.tactics: Dict[str, Tactics] = {}

    async def init(self, driver_instance):
        self.driver = driver_instance
        for obj in self.driver.objects.values():
            if isinstance(obj, (Player, MudObject)) and hasattr(obj, "attrs"):
                self.init_tactics(obj)
                obj.add_action("tactics", self.tactics_command)

    def init_tactics(self, obj: MudObject):
        if "tactics" not in obj.attrs or not isinstance(obj.attrs["tactics"], Tactics):
            obj.attrs["tactics"] = Tactics()
            self.tactics[obj.oid] = obj.attrs["tactics"]
            self.driver.save_object(obj)

    async def tactics_command(self, obj: MudObject, caller: Player, arg: str) -> str:
    if not isinstance(caller, Player) or caller.oid != obj.oid:
        return "Only players can adjust their own tactics."
    tactics = obj.attrs["tactics"]
    if not arg:
        return (f"Your current tactics under Mystra’s watch:\n"
                f"Attitude: {tactics.attitude}\n"
                f"Response: {tactics.response}\n"
                f"Parry: {tactics.parry}\n"
                f"Attack: {tactics.attack}\n"
                f"Parry Unarmed: {tactics.parry_unarmed}\n"
                f"Mercy: {tactics.mercy}\n"
                f"Focus Zone: {tactics.focus_zone}\n"
                f"Ideal Distance: {tactics.ideal_distance}\n"
                f"Mystra’s Favor: {tactics.mystra_favor}")
    args = arg.lower().split()
    if len(args) != 2:
        return ("Syntax: tactics <setting> <value>\n"
                "Settings: attitude, response, parry, attack, parry_unarmed, mercy, focus, distance\n"
                "See 'tactics help' for details.")
    setting, value = args
    if setting == "distance":
        if value not in self.DISTANCE_OPTIONS:
            return f"Invalid distance. Options: {', '.join(self.DISTANCE_OPTIONS)}"
        tactics.ideal_distance = value
   

      elif setting == "help":
        return ("Tactics settings:\n"
                f"distance [{', '.join(self.DISTANCE_OPTIONS)}]: Preferred combat range.\n"
                    f"attitude [{', '.join(self.ATTITUDE_OPTIONS)}]: How aggressively you fight.\n"
                    f"response [{', '.join(self.RESPONSE_OPTIONS)}]: How you defend.\n"
                    f"parry [{', '.join(self.PARRY_OPTIONS)}]: Which hand to parry with.\n"
                    f"attack [{', '.join(self.ATTACK_OPTIONS)}]: Which hand to attack with.\n"
                    "parry_unarmed [yes|no]: Whether to parry unarmed if no weapon.\n"
                    f"mercy [{', '.join(self.MERCY_OPTIONS)}]: How you handle surrender.\n"
                    f"focus [{'|'.join(self.FOCUS_OPTIONS)}]: Where to aim attacks.\n"
                    "distance [number]: Ideal combat distance (0 for none).")

        if setting == "attitude":
            if value not in self.ATTITUDE_OPTIONS:
                return f"Invalid attitude. Options: {', '.join(self.ATTITUDE_OPTIONS)}"
            tactics.attitude = value
        elif setting == "response":
            if value not in self.RESPONSE_OPTIONS:
                return f"Invalid response. Options: {', '.join(self.RESPONSE_OPTIONS)}"
            tactics.response = value
        elif setting == "parry":
            if value not in self.PARRY_OPTIONS:
                return f"Invalid parry. Options: {', '.join(self.PARRY_OPTIONS)}"
            tactics.parry = value
        elif setting == "attack":
            if value not in self.ATTACK_OPTIONS:
                return f"Invalid attack. Options: {', '.join(self.ATTACK_OPTIONS)}"
            tactics.attack = value
        elif setting == "parry_unarmed":
            if value not in ["yes", "no"]:
                return "Invalid parry_unarmed. Options: yes, no"
            tactics.parry_unarmed = (value == "yes")
        elif setting == "mercy":
            if value not in self.MERCY_OPTIONS:
                return f"Invalid mercy. Options: {', '.join(self.MERCY_OPTIONS)}"
            tactics.mercy = value
        elif setting == "focus":
            if value not in self.FOCUS_OPTIONS:
                return f"Invalid focus. Options: {'|'.join(self.FOCUS_OPTIONS)}"
            tactics.focus_zone = value
        elif setting == "distance":
            try:
                distance = int(value)
                if distance < 0:
                    return "Distance must be a non-negative number."
                tactics.ideal_distance = distance
            except ValueError:
                return "Distance must be a number."
        else:
            return "Unknown setting. Use 'tactics help' for options."

        self.tactics[obj.oid] = tactics
    self.driver.save_object(obj)
    return f"Tactics updated: {setting} set to {value}."

    def query_tactics(self, obj: MudObject) -> Tactics:
        self.init_tactics(obj)
        return self.tactics[obj.oid]

    def set_tactics(self, obj: MudObject, tactics: Tactics):
        self.tactics[obj.oid] = tactics
        obj.attrs["tactics"] = tactics
        self.driver.save_object(obj)

    def query_combat_distance(self, obj: MudObject) -> str:
    return self.query_tactics(obj).ideal_distance

def set_combat_distance(self, obj: MudObject, distance: str):
    if distance not in self.DISTANCE_OPTIONS:
        return
    tactics = self.query_tactics(obj)
    tactics.ideal_distance = distance
    self.set_tactics(obj, tactics)

    def query_combat_response(self, obj: MudObject) -> str:
        return self.query_tactics(obj).response

    def set_combat_response(self, obj: MudObject, response: str):
        if response not in self.RESPONSE_OPTIONS:
            return
        tactics = self.query_tactics(obj)
        tactics.response = response
        self.set_tactics(obj, tactics)

    def query_combat_parry(self, obj: MudObject) -> str:
        return self.query_tactics(obj).parry

    def set_combat_parry(self, obj: MudObject, parry: str):
        if parry not in self.PARRY_OPTIONS:
            return
        tactics = self.query_tactics(obj)
        tactics.parry = parry
        self.set_tactics(obj, tactics)

    def query_combat_attack(self, obj: MudObject) -> str:
        return self.query_tactics(obj).attack

    def set_combat_attack(self, obj: MudObject, attack: str):
        if attack not in self.ATTACK_OPTIONS:
            return
        tactics = self.query_tactics(obj)
        tactics.attack = attack
        self.set_tactics(obj, tactics)

    def query_unarmed_parry(self, obj: MudObject) -> bool:
        return self.query_tactics(obj).parry_unarmed

    def set_unarmed_parry(self, obj: MudObject, parry_unarmed: bool):
        tactics = self.query_tactics(obj)
        tactics.parry_unarmed = parry_unarmed
        self.set_tactics(obj, tactics)

    def query_combat_mercy(self, obj: MudObject) -> str:
        return self.query_tactics(obj).mercy

    def set_combat_mercy(self, obj: MudObject, mercy: str):
        if mercy not in self.MERCY_OPTIONS:
            return
        tactics = self.query_tactics(obj)
        tactics.mercy = mercy
        self.set_tactics(obj, tactics)

    def query_combat_focus(self, obj: MudObject) -> str:
        return self.query_tactics(obj).focus_zone

    def set_combat_focus(self, obj: MudObject, focus: str):
        if focus not in self.FOCUS_OPTIONS:
            return
        tactics = self.query_tactics(obj)
        tactics.focus_zone = focus
        self.set_tactics(obj, tactics)

    def query_combat_distance(self, obj: MudObject) -> int:
        return self.query_tactics(obj).ideal_distance

    def set_combat_distance(self, obj: MudObject, distance: int):
        if distance < 0:
            return
        tactics = self.query_tactics(obj)
        tactics.ideal_distance = distance
        self.set_tactics(obj, tactics)

# Initialize tactics handler
tactics_handler = TacticsHandler()

async def init(driver_instance):
    await tactics_handler.init(driver_instance)
