# Imported to: combat.py, living.py
# Imports from: driver.py
# /mnt/home2/mud/systems/weapon_logic.py
from typing import Dict, Optional, List
from ..driver import driver, Player, MudObject
import asyncio
import random
import math

class Weapon:
    def __init__(self, oid: str, name: str, damage: int, weight: int, length: int, damage_type: str, condition: int = 100):
        self.oid = oid
        self.name = name
        self.attrs: Dict = {
            "damage": damage,
            "weight": weight,
            "length": length,
            "damage_type": damage_type,
            "condition": condition,
            "enchantment": 0,
            "is_weapon": True,
            "is_shield": False,
            "category": self.determine_category(damage),
            "mystra_blessing": 0  # 2025 Forgotten Realms bonus
        }

    def determine_category(self, damage: int) -> str:
        categories = ["extremely low", "very low", "rather low", "low", "fair", "moderate", "high", "very high", "extremely high"]
        index = min(max(0, (damage - 1) // 25), len(categories) - 1)
        return categories[index]

    def query_damage(self) -> int:
    base_damage = self.attrs["damage"]
    enchantment_bonus = self.attrs["enchantment"] + self.attrs["mystra_blessing"]
    condition_factor = max(0, min(1, self.attrs["condition"] / 100))
    return int((base_damage + enchantment_bonus) * condition_factor)
    
    def query_weight(self) -> int:
        return self.attrs["weight"]

    def query_length(self) -> int:
        return self.attrs["length"]

    def query_damage_type(self) -> str:
        return self.attrs["damage_type"]

    def query_condition(self) -> int:
        return self.attrs["condition"]

    def adjust_condition(self, damage_dealt: int) -> bool:
        if self.attrs["condition"] <= 0:
            return False
        degradation = random.randint(1, max(1, damage_dealt // 10))
        self.attrs["condition"] = max(0, self.attrs["condition"] - degradation)
        self.driver.save_object(self)
        return self.attrs["condition"] > 0

    def apply_enchantment(self, bonus: int) -> bool:
        if bonus < 0 or self.attrs["condition"] <= 0:
            return False
        self.attrs["enchantment"] = max(0, self.attrs["enchantment"] + bonus)
        self.driver.save_object(self)
        return True

    def query_ap_cost(self, wielder: MudObject) -> int:
        weight = self.attrs["weight"]
        melee_bonus = wielder.attrs.get("skills", {}).get("fighting.combat.melee", 10) + \
                      wielder.attrs.get("skills", {}).get("fighting.combat.tactics", 10)
        base_ap = 4  # Base AP per round
        if weight > 17:  # Max weight for 4 AP per Pokey’s data
            return base_ap + int(math.sqrt(weight - 17))
        return base_ap - min(2, melee_bonus // 25)  # Reduction with skill

    def apply_focus_modifier(self, focus_zone: str) -> float:
        modifiers = {
            "none": 1.0,
            "upper body": 1.0,
            "lower body": 1.0,
            "head": 1.2,  # 20% extra per Pokey’s data
            "neck": 1.2,
            "chest": 1.1,
            "arms": 1.0,
            "legs": 1.0
        }
        return modifiers.get(focus_zone, 1.0)

class WeaponLogic:
    def __init__(self):
        self.weapons: Dict[str, Weapon] = {}

    async def init(self, driver_instance):
        self.driver = driver_instance
        for obj in self.driver.objects.values():
            if hasattr(obj, "attrs") and obj.attrs.get("is_weapon", False):
                self.weapons[obj.oid] = Weapon(obj.oid, obj.name, obj.attrs.get("damage", 10),
                                              obj.attrs.get("weight", 5), obj.attrs.get("length", 5),
                                              obj.attrs.get("damage_type", "blunt"), obj.attrs.get("condition", 100))
                obj.add_action("judge", self.judge_weapon)

    async def judge_weapon(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player) or caller.oid != obj.oid:
            return "You can only judge your own weapon."
        if obj.oid not in self.weapons:
            return "This is not a valid weapon."
        weapon = self.weapons[obj.oid]
        category = weapon.attrs["category"]
        damage = weapon.query_damage()
        return (f"You judge {obj.name} as dealing {category} damage ({damage} points), "
                f"weighing {weapon.query_weight()} lbs, with a length of {weapon.query_length()} units, "
                f"type {weapon.query_damage_type()}, and condition {weapon.query_condition()}%.")

    def query_weapon(self, obj: MudObject) -> Optional[Weapon]:
        return self.weapons.get(obj.oid)

    def register_weapon(self, obj: MudObject, name: str, damage: int, weight: int, length: int,
                       damage_type: str, condition: int = 100) -> Weapon:
        if obj.oid not in self.weapons:
            weapon = Weapon(obj.oid, name, damage, weight, length, damage_type, condition)
            self.weapons[obj.oid] = weapon
            obj.attrs.update(weapon.attrs)
            self.driver.save_object(obj)
        return self.weapons[obj.oid]

    def calculate_damage(self, weapon: Weapon, wielder: MudObject, focus_zone: str) -> int:
        base_damage = weapon.query_damage()
        focus_modifier = weapon.apply_focus_modifier(focus_zone)
        skill_bonus = wielder.attrs.get("skills", {}).get("fighting.combat.melee", 10) // 10
        return int(base_damage * focus_modifier * (1 + skill_bonus / 100))

    def degrade_weapon(self, weapon: Weapon, damage_dealt: int, armor_stopped: int) -> bool:
        effective_damage = max(0, damage_dealt - armor_stopped)
        return weapon.adjust_condition(effective_damage)

# Initialize weapon logic handler
weapon_logic = WeaponLogic()

async def init(driver_instance):
    await weapon_logic.init(driver_instance)
