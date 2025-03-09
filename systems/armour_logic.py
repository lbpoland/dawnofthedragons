# /mnt/home2/mud/systems/armour_logic.py
from typing import Dict, Optional, List
from ..driver import driver, Player, MudObject
import asyncio
import random
import math

class Armour:
    def __init__(self, oid: str, name: str, ac: Dict[str, int], coverage: Dict[str, float], weight: int, condition: int = 100):
        self.oid = oid
        self.name = name
        self.attrs: Dict = {
            "ac": ac,  # Armor class by damage type (slashing, piercing, etc.)
            "coverage": coverage,  # Percentage coverage per zone (0.0-1.0)
            "weight": weight,  # In pounds, affects burden
            "condition": condition,  # 0-100, degrades with damage
            "is_armour": True,
            "is_shield": False,
            "enchantment": 0  # Bonus AC from magic (Forgotten Realms)
        }

    def query_ac(self, damage_type: str, zone: str) -> int:
        base_ac = self.attrs["ac"].get(damage_type, 0)
        enchantment_bonus = self.attrs["enchantment"]
        condition_factor = max(0, min(1, self.attrs["condition"] / 100))
        coverage = self.attrs["coverage"].get(zone, 0.0)
        return int((base_ac + enchantment_bonus) * condition_factor * coverage)

    def query_weight(self) -> int:
        return self.attrs["weight"]

    def query_condition(self) -> int:
        return self.attrs["condition"]

    def adjust_condition(self, damage_taken: int) -> bool:
        if self.attrs["condition"] <= 0:
            return False
        degradation = random.randint(1, max(1, damage_taken // 5))
        self.attrs["condition"] = max(0, self.attrs["condition"] - degradation)
        self.driver.save_object(self)
        return self.attrs["condition"] > 0

    def apply_enchantment(self, bonus: int) -> bool:
        if bonus < 0 or self.attrs["condition"] <= 0:
            return False
        self.attrs["enchantment"] = max(0, self.attrs["enchantment"] + bonus)
        self.driver.save_object(self)
        return True

class ArmourLogic:
    def __init__(self):
        self.armour: Dict[str, Armour] = {}

    async def init(self, driver_instance):
        self.driver = driver_instance
        for obj in self.driver.objects.values():
            if hasattr(obj, "attrs") and obj.attrs.get("is_armour", False):
                self.armour[obj.oid] = Armour(obj.oid, obj.name, obj.attrs.get("ac", {}),
                                             obj.attrs.get("coverage", {}), obj.attrs.get("weight", 5),
                                             obj.attrs.get("condition", 100))
                obj.add_action("judge", self.judge_armour)

    async def judge_armour(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player) or caller.oid != obj.oid:
            return "You can only judge your own armour."
        if obj.oid not in self.armour:
            return "This is not valid armour."
        armour = self.armour[obj.oid]
        ac_summary = ", ".join(f"{dt}: {ac}" for dt, ac_dict in armour.attrs["ac"].items() for zone, ac in ac_dict.items())
        return (f"You judge {obj.name} as providing AC {ac_summary}, weighing {armour.query_weight()} lbs, "
                f"with condition {armour.query_condition()}%.")

    def query_armour(self, obj: MudObject) -> Optional[Armour]:
        return self.armour.get(obj.oid)

    def register_armour(self, obj: MudObject, name: str, ac: Dict[str, int], coverage: Dict[str, float],
                       weight: int, condition: int = 100) -> Armour:
        if obj.oid not in self.armour:
            armour = Armour(obj.oid, name, ac, coverage, weight, condition)
            self.armour[obj.oid] = armour
            obj.attrs.update(armour.attrs)
            self.driver.save_object(obj)
        return self.armour[obj.oid]

    def calculate_protection(self, armour: Armour, damage_type: str, damage: int, zone: str) -> int:
        stopped = armour.query_ac(damage_type, zone)
        effective_stopped = min(damage, stopped)
        if effective_stopped > 0:
            armour.adjust_condition(effective_stopped)
        return effective_stopped

# Initialize armour logic handler
armour_logic = ArmourLogic()

async def init(driver_instance):
    await armour_logic.init(driver_instance)
