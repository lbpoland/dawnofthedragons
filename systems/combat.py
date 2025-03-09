# /mnt/home2/mud/systems/combat.py
from typing import Dict, Optional, List, Tuple, Callable
from ..driver import driver, Player, MudObject
from .tactics import Tactics  # Import Tactics from tactics.py
import asyncio
import random
import math
import json

class CombatSpecial:
    def __init__(self, special_id: int, type_: int, events: int, callback: Callable, data: dict):
        self.id = special_id
        self.type_ = type_  # T_OFFENSIVE, T_DEFENSIVE, T_CONTINUOUS
        self.events = events  # E_OPPONENT_SELECTION, etc.
        self.callback = callback
        self.data = data

class Attack:
    def __init__(self, attacker: Player, opponent: Optional[MudObject] = None):
        self.attacker = attacker
        self.opponent = opponent
        self.defender = opponent
        self.person_hit = opponent
        self.attacker_tactics = attacker.attrs.get("tactics", Tactics())
        self.attacker_specials: List[CombatSpecial] = attacker.attrs.get("specials", [])
        self.attacker_concentrating = attacker.attrs.get("concentrating", None)
        self.attacker_defecit = attacker.attrs.get("action_defecit", 0)
        self.attacker_last_opponent = attacker.attrs.get("last_opponent", None)
        self.attacker_last_weapon = attacker.attrs.get("last_weapon", None)
        self.attacker_last_action = attacker.attrs.get("last_action", "none")
        self.attacker_last_result = attacker.attrs.get("last_result", 0)
        self.defender_tactics = Tactics()
        self.defender_specials: List[CombatSpecial] = []
        self.defender_concentrating = None
        self.defender_defecit = 0
        self.defender_last_opponent = None
        self.defender_last_action = "none"
        self.defender_last_result = 0
        self.attack_weapon = None
        self.attack_data = None
        self.attack_skill = "fighting.combat.melee"
        self.attack_modifier = 0
        self.attack_cost = 0
        self.defense_action = "none"
        self.defense_weapon = None
        self.defense_skill = "fighting.combat.dodge"
        self.defense_modifier = 0
        self.defense_cost = 0
        self.distance = 0
        self.target_zone = "chest"
        self.result = 0  # OFFWIN, OFFAWARD, DEFWIN, DEFAWARD
        self.degree = 0  # TASKER_CRITICAL, TASKER_EXCEPTIONAL, TASKER_MARGINAL
        self.damage = 0
        self.armour_stopped = 0
        self.stopped_by = None
        self.attack_messages = ["", "", "", "", ""]
        self.defense_messages = ["", "", "", "", ""]
        self.repeat = False

class CombatHandler:
    # Constants from combat.h
    T_OFFENSIVE = 1
    T_DEFENSIVE = 2
    T_CONTINUOUS = 4
    E_OPPONENT_SELECTION = 1
    E_DEFENDER_SELECTION = 2
    E_ATTACK_SELECTION = 4
    E_DEFENSE_SELECTION = 8
    E_ATTACK_MODIFIER = 16
    E_DEFENSE_MODIFIER = 32
    E_DAMAGE_CALCULATION = 64
    E_ARMOUR_CALCULATION = 128
    E_WEAPON_DAMAGE = 256
    E_WRITE_MESSAGES = 512
    E_AFTER_ATTACK = 1024
    R_CONTINUE = 0
    R_DONE = 1
    R_ABORT = 2
    R_REMOVE_ME = 4
    OFFAWARD = 1
    OFFWIN = 2
    DEFAWARD = 3
    DEFWIN = 4
    TASKER_CRITICAL = 1
    TASKER_EXCEPTIONAL = 2
    TASKER_MARGINAL = 3
    COMBAT_SPEED = 1
    INITIAL_DISTANCE = 2
    REACH = 5
    ATTACK_COST = 10
    DEFENSE_COST = 8
    MAX_ACTION_DEFECIT = 100
    MIN_ACTION_DEFECIT = -100
    HUNTING_TIME = 300
    BALANCE_MOD = 0
    OFFENSIVE_DEFECITS = {"insane": 50, "offensive": 25, "neutral": 0, "defensive": -25, "wimp": -50}
    DEFENSIVE_DEFECITS = {"insane": -50, "offensive": -25, "neutral": 0, "defensive": 25, "wimp": 50}
    DEFENSE_GP = {"insane": 5, "offensive": 3, "neutral": 2, "defensive": 1, "wimp": 0}
    USE_DISTANCE = True

    def __init__(self):
        self.combatants: Dict[str, str] = {}  # {player_oid: target_oid}
        self.hunting: Dict[str, int] = {}  # {player_oid: timestamp}
        self.surrender_to: Dict[str, List[str]] = {}  # {player_oid: [surrenderers]}
        self.surrender_from: Dict[str, List[str]] = {}  # {player_oid: [attackers]}
        self.special_id_counter = 0
        self.damage_types = ["slashing", "piercing", "bludgeoning", "magic", "blunt"]

    async def init(self, driver_instance):
        self.driver = driver_instance
        for obj in self.driver.objects.values():
            if hasattr(obj, "add_action"):
                obj.add_action("attack", self.attack)
                obj.add_action("flee", self.flee)
                obj.add_action("surrender", self.surrender)

    async def attack(self, attacker: MudObject, player: Player, target_name: str) -> str:
        if not isinstance(player, Player) or not player.location:
            return "You cannot fight from nowhere!"
        if not self.can_attack(player):
            return "You are unable to attack right now!"

        target = self.find_target(player, target_name)
        if not target:
            return f"No {target_name} here to attack!"

        if not self.attack_by(player, target):
            return "You cannot attack this target!"

        att = Attack(attacker=player, opponent=target)
        await self.do_attack(att)
        return f"You attack {target.name}!"

    async def flee(self, fleeing: MudObject, player: Player, arg: str) -> str:
        if not isinstance(player, Player) or player.oid not in self.combatants:
            return "You are not in combat!"
        target_oid = self.combatants.get(player.oid)
        if target_oid:
            self.stop_fight(player, self.driver.objects[target_oid])
            await player.send("You flee from combat!")
            return await player.location.call("move", player, "random")
        return "No combat to flee from!"

    async def surrender(self, surrendering: MudObject, player: Player, target_name: str) -> str:
        if not isinstance(player, Player) or player.oid not in self.combatants:
            return "You are not in combat!"
        target = self.find_target(player, target_name)
        if not target:
            return f"No {target_name} to surrender to!"
        await self.event_surrender(player, target)
        return f"You surrender to {target.name}."

    def find_target(self, player: Player, target_name: str) -> Optional[MudObject]:
        for oid in player.location.attrs.get("contents", []):
            if oid in self.driver.objects and self.driver.objects[oid].name.lower() == target_name.lower():
                return self.driver.objects[oid]
        return None

    def can_attack(self, obj: MudObject) -> bool:
        if (obj.attrs.get("passed_out", False) or
            obj.attrs.get("dead", False) or
            obj.attrs.get("hp", 100) < 0 or
            obj.attrs.get("casting_spell", False) or
            (isinstance(obj, Player) and not obj.connected) or
            obj.attrs.get("cannot_attack", False)):
            return False
        return True

    def can_defend(self, obj: MudObject) -> bool:
        if (obj.attrs.get("passed_out", False) or
            obj.attrs.get("dead", False) or
            obj.attrs.get("hp", 100) < 0 or
            obj.attrs.get("casting_spell", False) or
            (isinstance(obj, Player) and not obj.connected) or
            obj.attrs.get("cannot_defend", False)):
            return False
        return True

    def query_attackable(self, obj: MudObject) -> bool:
        if (obj.attrs.get("passed_out", False) or
            obj.attrs.get("dead", False) or
            obj.attrs.get("hp", 100) < 0 or
            (isinstance(obj, Player) and not obj.connected)):
            return False
        return True

    def attack_by(self, attacker: MudObject, opponent: MudObject) -> bool:
        if (not opponent or attacker.oid == opponent.oid or
            not self.query_attackable(opponent) or
            self.pk_check(attacker, opponent)):
            return False

        attacker.attrs["protectors"] = [p for p in attacker.attrs.get("protectors", []) if p != opponent.oid]
        attacker.attrs["defenders"] = [d for d in attacker.attrs.get("defenders", []) if d != opponent.oid]

        if not self.is_fighting(attacker, opponent, actively=True):
            if self.USE_DISTANCE:
                self.combatants[opponent.oid] = self.INITIAL_DISTANCE
            else:
                self.combatants[opponent.oid] = 1
            attacker.attrs["action_defecit"] = (self.MAX_ACTION_DEFECIT - self.MIN_ACTION_DEFECIT) // 3

        self.combatants[attacker.oid] = opponent.oid
        return True

    def pk_check(self, attacker: MudObject, opponent: MudObject) -> bool:
        # Simplified PK check - to be expanded based on rules
        return False

    async def do_attack(self, att: Attack):
        # Initialize combat state
        att.attacker.attrs["in_combat"] = True

        # Choose opponent
        att = self.choose_opponent(att)
        if not att.opponent or not self.attack_by(att.attacker, att.opponent):
            return

        # Main combat loop
        while True:
            # Choose defender
            att = self.choose_defender(att)

            # Choose attack
            att = self.choose_attack(att)
            if not att.attack_weapon or not att.attack_data:
                return

            # Choose defense
            att = self.choose_defense(att)

            # Calculate modifiers
            att = self.calc_attack_modifier(att)
            if att.defense_action == "none":
                att.defense_modifier -= 1000
            else:
                att = self.calc_defense_modifier(att)

            # Compare skills
            modifier = att.attack_modifier - att.defense_modifier + self.BALANCE_MOD
            if modifier > 25:
                modifier = int(math.sqrt(modifier * 25))
            elif modifier < -25:
                modifier = -int(math.sqrt(-modifier * 25))

            result = self.compare_skills(att.attacker, att.attack_skill, att.defender, att.defense_skill, modifier)
            att.result = result[0]
            att.degree = result[1]

            # Handle defender failure
            if (att.result in [self.OFFWIN, self.OFFAWARD] and att.defender != att.opponent and not att.repeat):
                att.defender.attrs["action_defecit"] = att.defender.attrs.get("action_defecit", 0) + att.defense_cost
                att.defender.attrs["gp"] = att.defender.attrs.get("gp", 100) - self.DEFENSE_GP.get(att.defender_tactics.attitude, 0)
                att.defender = att.opponent
                att.repeat = True
            else:
                att.repeat = False
                break

        # Calculate damage
        att = self.calc_damage(att)

        # Calculate armor protection
        att = self.calc_armour_protection(att)

        # Prepare messages
        att = self.prepare_messages(att)

        # Write messages
        await self.write_messages(att)

        # Apply damage
        if att.damage - att.armour_stopped > 0:
            att.person_hit.attrs["hp"] = att.person_hit.attrs.get("hp", 100) - (att.damage - att.armour_stopped)
            self.driver.save_object(att.person_hit)
            if att.person_hit.attrs["hp"] <= 0:
                await self.die(att.person_hit, att.attacker)

        # Damage weapons
        att = self.damage_weapon(att)

        # Post-attack cleanup
        await self.after_attack(att)

        # Update action defecit
        att.attacker.attrs["action_defecit"] = att.attacker.attrs.get("action_defecit", 0) + att.attack_cost
        att.defender.attrs["action_defecit"] = att.defender.attrs.get("action_defecit", 0) + att.defense_cost

    def choose_opponent(self, att: Attack) -> Attack:
        opponents = [self.driver.objects[oid] for oid in self.combatants if oid != att.attacker.oid and self.driver.objects[oid].location == att.attacker.location]
        opponents = [opp for opp in opponents if self.query_attackable(opp)]

        if not opponents:
            return att

        if att.attacker_concentrating in opponents:
            att.opponent = att.attacker_concentrating
        else:
            # Simple NPC algorithm: pick random or weakest
            choice = random.randint(0, 2)
            if choice == 0:
                att.opponent = random.choice(opponents)
            elif choice == 1:
                att.opponent = min(opponents, key=lambda opp: opp.attrs.get("hp", 100))
            else:
                att.opponent = max(opponents, key=lambda opp: opp.attrs.get("hp", 100))

        if self.USE_DISTANCE:
            att.distance = self.combatants.get(att.opponent.oid, self.INITIAL_DISTANCE)

        if len(opponents) == 1:
            att.attacker.attrs["concentrating"] = att.opponent

        return att

    def choose_defender(self, att: Attack) -> Attack:
        protectors = [self.driver.objects[p] for p in att.opponent.attrs.get("protectors", []) if p in self.driver.objects and self.driver.objects[p].location == att.attacker.location]
        protectors = [p for p in protectors if self.query_protect(p) and not self.pk_check(p, att.attacker)]

        if protectors:
            for p in protectors:
                self.attack_by(p, att.attacker)
            att.person_hit = random.choice(protectors)

        defenders = [self.driver.objects[d] for d in att.opponent.attrs.get("defenders", []) if d in self.driver.objects and self.driver.objects[d].location == att.attacker.location]
        defenders = [d for d in defenders if self.query_defend(d) and not self.pk_check(d, att.attacker)]

        if defenders:
            for d in defenders:
                self.attack_by(d, att.attacker)
            att.defender = random.choice(defenders)

        if not att.person_hit:
            att.person_hit = att.opponent
        if not att.defender:
            att.defender = att.opponent

        return att

    def query_protect(self, obj: MudObject) -> bool:
        if not self.query_attackable(obj) or obj.attrs.get("casting_spell", False) or obj.attrs.get("gp", 100) < 1:
            return False
        return obj.attrs.get("action_defecit", 0) < (self.COMBAT_ACTION_TIME * 4)

    def query_defend(self, obj: MudObject) -> bool:
        if not self.query_attackable(obj) or obj.attrs.get("casting_spell", False) or obj.attrs.get("gp", 100) < 1:
            return False
        tactics = obj.attrs.get("tactics", Tactics())
        return (tactics.response in ["parry", "both"]) and obj.attrs.get("action_defecit", 0) < (self.COMBAT_ACTION_TIME * 4)

    def choose_attack(self, att: Attack) -> Attack:
        if not self.can_attack(att.attacker):
            return att

        if att.attacker_defecit > self.OFFENSIVE_DEFECITS.get(att.attacker_tactics.attitude, 0):
            return att

        weapons = att.attacker.attrs.get("holding", [])
        limbs = att.attacker.attrs.get("limbs", ["left hand", "right hand"])
        hand = att.attacker_tactics.attack

        if hand != "both":
            idx = next((i for i, limb in enumerate(limbs) if limb.startswith(hand)), -1)
            if idx != -1:
                if not weapons[idx]:
                    weapons = []
                elif weapons[idx].attrs.get("is_weapon", False):
                    weapons = [weapons[idx]]

        if len(weapons) > 1:
            weapons = list(set(w for w in weapons if w and w.attrs.get("is_weapon", False)))

        if not weapons:
            att.attack_weapon = att.attacker
        elif len(weapons) == 1:
            att.attack_weapon = weapons[0]
        else:
            if self.USE_DISTANCE:
                att.attack_weapon = min(weapons, key=lambda w: abs(self.REACH + w.attrs.get("length", 5) - att.distance))
            else:
                att.attack_weapon = random.choice(weapons)

        perc = 75 + att.attacker.attrs.get("str", 10) + att.attacker.attrs.get("dex", 10)
        if att.attack_weapon != att.attacker:
            perc -= att.attack_weapon.attrs.get("weight", 5) // 2
        perc = max(25, perc)

        attacks = self.weapon_attacks(att.attack_weapon, perc, att.defender)
        if not attacks:
            return att

        which_attack = random.randint(0, len(attacks) // 5 - 1)
        att.attack_data = attacks[which_attack * 5:(which_attack + 1) * 5]

        if att.attack_data[0] == "hands" and not att.attacker.attrs.get("free_limbs", 0):
            att.attack_data = None
            return att

        att.attack_skill = att.attack_data[1] if att.attack_data[1] else "fighting.combat.melee"

        # Choose target zone
        zones = att.opponent.attrs.get("target_zones", ["head", "chest", "arms", "legs"])
        if att.attacker_tactics.focus_zone == "upper body":
            zone = random.choice(zones[:len(zones)//2])
        elif att.attacker_tactics.focus_zone == "lower body":
            zone = random.choice(zones[len(zones)//2:])
        elif att.attacker_tactics.focus_zone and att.attacker_tactics.focus_zone != "none":
            zone = att.attacker_tactics.focus_zone
        else:
            sz = att.attacker.attrs.get("height", 6) / att.opponent.attrs.get("height", 6)
            if att.attack_data[0] == "hands":
                sz *= 2
            elif att.attack_data[0] == "feet":
                sz /= 2
            if sz > 1.5:
                zone = zones[random.randint(0, random.randint(0, len(zones)-1))]
            elif sz < 0.75:
                idx = random.randint(0, len(zones) + 9)
                zone = zones[min(idx, len(zones)-1)]
            else:
                zone = random.choice(zones)
        att.target_zone = zone

        actions = self.ATTACK_COST
        if att.attack_weapon != att.attacker:
            limbs_count = sum(1 for w in att.attacker.attrs.get("holding", []) if w == att.attack_weapon)
            actions += int(math.sqrt(att.attack_weapon.attrs.get("weight", 5)) * 3) // (limbs_count + 1)
        if len(att.attacker.attrs.get("weapons", [])) > 1:
            actions -= self.ATTACK_COST // 4
        actions -= (att.attacker.attrs.get("skills", {}).get(att.attack_skill, 10) + att.attacker.attrs.get("skills", {}).get("fighting.combat.tactics", 10)) // 50
        att.attack_cost = max(self.ATTACK_COST // 5, min(self.ATTACK_COST * 2, actions))

        return att

    def weapon_attacks(self, weapon: MudObject, perc: int, defender: MudObject) -> List:
        if weapon == defender:
            return [["hands", "fighting.combat.unarmed", 10, "blunt", perc]]
        return [["slash", "fighting.combat.melee", weapon.attrs.get("damage", 15), weapon.attrs.get("damage_type", "slashing"), perc]]

    def choose_defense(self, att: Attack) -> Attack:
        if att.defender != att.opponent and att.defender_defecit > self.DEFENSIVE_DEFECITS.get(att.defender_tactics.attitude, 0):
            att.defense_action = "none"
            return att

        response = att.defender_tactics.response
        if att.defender != att.opponent:
            if response == "dodge":
                att.defense_action = "none"
                return att
            response = "parry"
        elif not response or response == "neutral":
            response = random.choice(["parry", "dodge"])

        if response == "parry":
            weapons = att.defender.attrs.get("holding", [])
            hand = att.defender_tactics.parry
            limbs = att.defender.attrs.get("limbs", ["left hand", "right hand"])
            which = next((i for i, limb in enumerate(limbs) if limb.startswith(hand)), -1)

            if which != -1:
                if weapons[which]:
                    att.defense_action = "parry"
                    att.defense_skill = "fighting.combat.parry"
                    att.defense_weapon = weapons[which]
                elif att.defender_tactics.parry_unarmed:
                    att.defense_action = "parry"
                    att.defense_skill = "fighting.combat.unarmed"
                    att.defense_weapon = att.defender
                    att.defense_limb = limbs[which]
            else:
                weapons = [w for w in weapons if w]
                if not weapons and att.defender_tactics.parry_unarmed:
                    att.defense_action = "parry"
                    att.defense_skill = "fighting.combat.unarmed"
                    att.defense_weapon = att.defender
                elif weapons:
                    att.defense_action = "parry"
                    att.defense_skill = "fighting.combat.parry"
                    att.defense_weapon = random.choice(weapons)
        else:
            att.defense_action = "dodge"
            att.defense_skill = "fighting.combat.dodge"
            att.defense_weapon = None

        actions = self.DEFENSE_COST
        actions -= (att.defender.attrs.get("skills", {}).get(att.defense_skill, 10) + att.defender.attrs.get("skills", {}).get("fighting.combat.tactics", 10)) // 50
        if att.defense_weapon and att.defense_weapon != att.defender:
            if att.defense_weapon.attrs.get("is_shield", False):
                actions += int(math.sqrt(att.defense_weapon.attrs.get("weight", 5) / 4))
            else:
                limbs_count = sum(1 for w in att.defender.attrs.get("holding", []) if w == att.defense_weapon)
                actions += int(math.sqrt(att.defense_weapon.attrs.get("weight", 5) * 2) // (limbs_count + 1))
            if len(att.defender.attrs.get("weapons", [])) > 1:
                actions -= self.DEFENSE_COST // 4
        elif att.defense_action == "dodge":
            actions += int(math.sqrt(att.defender.attrs.get("burden", 0)))
        att.defense_cost = max(self.DEFENSE_COST // 5, min(self.DEFENSE_COST * 2, actions))

        return att

    def calc_attack_modifier(self, att: Attack) -> Attack:
        mod = wep = hld = lght = mntd = hlth = brdn = dist = tact = targ = oth = num = 0
        dex = att.attacker.attrs.get("dex", 10)
        attack_weapon = att.attack_weapon

        if attack_weapon != att.attacker:
            holding = att.attacker.attrs.get("holding", [])
            limbs = sum(1 for w in holding if w == attack_weapon)
            tmp2 = sum(w.attrs.get("weight", 5) if not w.attrs.get("is_shield", False) else w.attrs.get("weight", 5) // 5 for w in holding if w and w != attack_weapon)

            if att.attacker_tactics.response == "both":
                tmp2 = (tmp2 * 3) // 2
            elif att.attacker_tactics.response == "dodge" and tmp2 < dex:
                tmp2 //= 2

            wep = attack_weapon.attrs.get("weight", 5) + (tmp2 // 2)
            wep //= (limbs + 1)
            wep -= att.attacker.attrs.get("str", 10)
            if wep > 0:
                wep = -int(math.pow(wep, 1.4))

            if dex < 14 and holding and holding[0] != attack_weapon:
                hld = dex - 14
        else:
            wep = (dex * 2) - att.attacker.attrs.get("burden", 0)

        light_level = att.attacker.location.attrs.get("light", 0)
        if light_level in [-2, 2]:
            lght = -50
        elif light_level in [-1, 1]:
            lght = -25

        mntd = 0  # Placeholder for mounted combat

        hlth -= (50 - (att.attacker.attrs.get("hp", 100) * 50) // att.attacker.attrs.get("max_hp", 100))
        tmp = att.attacker.attrs.get("gp", 100)
        if tmp < -50:
            hlth += -25
        elif tmp < 0:
            hlth += tmp // 2

        brdn -= att.attacker.attrs.get("burden", 0) // 3

        if self.USE_DISTANCE:
            if att.attack_weapon == att.attacker:
                dist = -3 * abs(self.REACH - att.distance)
            else:
                dist = -3 * abs(self.REACH + att.attack_weapon.attrs.get("length", 5) - att.distance)

        tact = {"insane": 25, "offensive": 15, "defensive": -25, "wimp": -50}.get(att.attacker_tactics.attitude, 0)

        if att.attacker_tactics.focus_zone in ["upper body", "lower body"]:
            targ -= 25
        elif att.attacker_tactics.focus_zone and att.attacker_tactics.focus_zone != "none":
            zones = att.opponent.attrs.get("target_zones", ["head", "chest", "arms", "legs"])
            tmp = sum(1 for zone in zones if zone == att.target_zone)
            num_zones = len(zones)
            targ -= ((num_zones - tmp) * 25 // num_zones)

        attackers = [self.driver.objects[oid] for oid in self.combatants if self.driver.objects[oid].location == att.attacker.location]
        idx = attackers.index(att.attacker) if att.attacker in attackers else -1
        if idx > 1:
            num += -25 * idx

        if att.attacker_tactics.attack == "both":
            oth += 5

        att.attack_modifier += wep + hld + lght + mntd + hlth + brdn + dist + tact + targ + oth + num
        return att

    def calc_defense_modifier(self, att: Attack) -> Attack:
        mod = wep = wght = dist = brdn = hnd = lght = hlth = tact = prot = oth = 0
        dex = att.defender.attrs.get("dex", 10)

        if att.defense_action == "parry" and att.defense_weapon:
            holding = att.defender.attrs.get("holding", [])
            limbs = sum(1 for w in holding if w == att.defense_weapon)
            if att.defense_weapon.attrs.get("is_shield", False):
                wep = att.defense_weapon.attrs.get("weight", 5) // 5
            else:
                wep = att.defense_weapon.attrs.get("weight", 5) * 2
            wep //= (limbs + 2)
            if wep > att.defender.attrs.get("str", 10):
                wep = -int(math.pow(wep - att.defender.attrs.get("str", 10), 1.3))

            if att.attack_weapon != att.attacker:
                wght = 2 * (att.defense_weapon.attrs.get("weight", 5) - att.attack_weapon.attrs.get("weight", 5))
            else:
                wght = att.defense_weapon.attrs.get("weight", 5) // 2
            wght = min(5, wght)

            if self.USE_DISTANCE:
                dist = -abs(self.REACH + att.defense_weapon.attrs.get("length", 5) - att.distance)

            brdn = -(att.defender.attrs.get("burden", 0) // 3)

            if holding:
                if dex < 14 and holding[0] != att.defense_weapon:
                    hnd = dex - 14
                holding = list(set(w for w in holding if w))
                if dex < 16 and len(holding) == 1:
                    hnd += dex - 16
        elif att.defense_action == "dodge":
            brdn = -(att.defender.attrs.get("burden", 0) // 3)
            if dex < (att.defender.attrs.get("burden", 0) // 2):
                brdn -= dex - (att.defender.attrs.get("burden", 0) // 2)
            if att.attack_weapon != att.attacker:
                wght = att.attack_weapon.attrs.get("weight", 5) // 10

        light_level = att.defender.location.attrs.get("light", 0)
        if not att.attacker.attrs.get("visible", True):
            lght = -100
        elif light_level in [-2, 2]:
            lght = -50
        elif light_level in [-1, 1]:
            lght = -25

        hlth = -(25 - (att.defender.attrs.get("hp", 100) * 25) // att.defender.attrs.get("max_hp", 100))
        tmp = att.defender.attrs.get("gp", 100)
        if tmp < -50:
            hlth += -25
        elif tmp < 0:
            hlth += tmp // 2

        tact = {"insane": -50, "offensive": -25, "defensive": 15, "wimp": 25}.get(att.defender_tactics.attitude, 0)

        if att.defender != att.opponent:
            if att.defender != att.person_hit:
                if att.defense_weapon and att.defense_weapon.attrs.get("is_shield", False):
                    prot -= 15
                prot -= 15
            prot -= 15

        if att.defender_tactics.response == "both":
            oth += 5
        if att.defender.attrs.get("casting_spell", False):
            oth -= 25

        att.defense_modifier += wep + wght + dist + brdn + hnd + lght + hlth + tact + prot + oth
        return att

    def compare_skills(self, attacker: MudObject, attack_skill: str, defender: MudObject, defense_skill: str, modifier: int) -> Tuple[int, int]:
        atk_skill = attacker.attrs.get("skills", {}).get(attack_skill, 10)
        def_skill = defender.attrs.get("skills", {}).get(defense_skill, 10)
        chance = 50 + (atk_skill - def_skill) + modifier
        chance = max(5, min(95, chance))
        roll = random.random() * 100
        if roll < chance:
            degree = self.TASKER_CRITICAL if roll < chance * 0.1 else self.TASKER_EXCEPTIONAL if roll < chance * 0.3 else self.TASKER_MARGINAL
            return (self.OFFWIN, degree)
        else:
            degree = self.TASKER_CRITICAL if roll > chance * 1.9 else self.TASKER_EXCEPTIONAL if roll > chance * 1.7 else self.TASKER_MARGINAL
            return (self.DEFWIN, degree)

    def calc_damage(self, att: Attack) -> Attack:
        damage = att.attack_data[3] if att.attack_data else 10
        weapon_damage = damage
        if att.attack_weapon != att.attacker:
            damage = int(math.sqrt(damage * att.attacker.attrs.get("skills", {}).get(att.attack_skill, 10)))
        damage = min(3 * weapon_damage, damage)
        damage *= self.COMBAT_SPEED
        att.damage = damage

        if att.result in [self.OFFAWARD, self.OFFWIN]:
            if att.degree == self.TASKER_CRITICAL:
                att.damage *= 2
            elif att.degree == self.TASKER_EXCEPTIONAL:
                att.damage = (att.damage * 3) // 2
            elif att.degree == self.TASKER_MARGINAL:
                att.damage //= 2
        else:
            if att.degree == self.TASKER_CRITICAL:
                att.defense_cost = 0
            elif att.degree == self.TASKER_EXCEPTIONAL:
                att.defense_cost //= 2
            elif att.degree == self.TASKER_MARGINAL:
                att.defense_cost *= 2
            att.damage = 0

        return att

    def calc_armour_protection(self, att: Attack) -> Attack:
        if not att.damage or att.result not in [self.OFFWIN, self.OFFAWARD]:
            return att

        armour_zone = att.person_hit.attrs.get("armour_zones", {}).get(att.target_zone, "chest")
        damage_type = att.attack_data[2] if att.attack_data else "blunt"
        if damage_type == "unarmed":
            damage_type = "blunt"

        ac = att.person_hit.attrs.get("ac", {}).get(damage_type, {}).get(armour_zone, 0)
        att.armour_stopped = min(att.damage, ac)
        att.stopped_by = att.person_hit.attrs.get("armour", {}).get(armour_zone, "leather armor")

        return att

    def damage_weapon(self, att: Attack) -> Attack:
        off_damage = def_damage = 0
        if att.result in [self.OFFAWARD, self.OFFWIN]:
            if att.armour_stopped and att.degree:
                off_damage = att.armour_stopped // att.degree
        elif att.result in [self.DEFWIN, self.DEFAWARD] and att.defense_action == "parry" and att.damage and att.degree:
            off_damage = att.damage * (att.degree - 1)
            def_damage = att.damage // att.degree

        if off_damage:
            if att.attack_weapon == att.attacker:
                if att.attack_weapon.attrs.get("hp", 100) > (off_damage // 10):
                    att.attack_weapon.attrs["hp"] -= off_damage // 10
            else:
                att.attack_weapon.attrs["hp"] = att.attack_weapon.attrs.get("hp", 100) - off_damage

        if def_damage:
            if att.defense_weapon == att.defender:
                att.defense_weapon.attrs["hp"] = att.defense_weapon.attrs.get("hp", 100) - def_damage
            else:
                att.defense_weapon.attrs["hp"] = att.defense_weapon.attrs.get("hp", 100) - def_damage

        return att

    def prepare_messages(self, att: Attack) -> Attack:
        if att.result in [self.OFFAWARD, self.OFFWIN]:
            if att.person_hit == att.opponent:
                att.attack_messages = [
                    f"You hit {att.opponent.name} in the {att.target_zone}!",
                    f"{att.attacker.name} hits you in the {att.target_zone}!",
                    f"{att.attacker.name} hits {att.opponent.name} in the {att.target_zone}!",
                    f"{att.attacker.name} hits {att.opponent.name} in the {att.target_zone}!",
                    f"{att.attacker.name} hits you in the {att.target_zone}!"
                ]
            else:
                att.attack_messages = [
                    f"You almost hit {att.opponent.name} but {att.person_hit.name} protects them!",
                    f"{att.attacker.name} almost hits you but {att.person_hit.name} protects you!",
                    f"{att.attacker.name} almost hits {att.opponent.name} but {att.person_hit.name} protects them!",
                    f"{att.attacker.name} almost hits {att.opponent.name} but {att.person_hit.name} protects them!",
                    f"You leap in and protect {att.opponent.name} from {att.attacker.name}!"
                ]
        else:
            att.attack_messages = [
                f"You try to hit {att.opponent.name} in the {att.target_zone}!",
                f"{att.attacker.name} tries to hit you in the {att.target_zone}!",
                f"{att.attacker.name} tries to hit {att.opponent.name} in the {att.target_zone}!",
                f"{att.attacker.name} tries to hit {att.opponent.name} in the {att.target_zone}!",
                f"{att.attacker.name} tries to hit {att.opponent.name} in the {att.target_zone}!"
            ]

        if att.result in [self.OFFAWARD, self.OFFWIN] and att.armour_stopped and att.armour_stopped > att.damage // 3:
            msg = f" but {att.stopped_by} absorbs "
            msg += "all of" if att.armour_stopped >= att.damage else "most of" if att.armour_stopped > (att.damage * 2 // 3) else "some of"
            msg += " the blow"
            att.defense_messages = [msg] * 5

        return att

    async def write_messages(self, att: Attack):
        await att.attacker.send(att.attack_messages[0] + att.defense_messages[0])
        await att.opponent.send(att.attack_messages[1] + att.defense_messages[1])
        for oid in att.attacker.location.attrs.get("contents", []):
            if oid not in [att.attacker.oid, att.opponent.oid, att.defender.oid, att.person_hit.oid]:
                await self.driver.call_other(oid, "receive_message", att.attacker, att.attack_messages[2] + att.defense_messages[2])
        if att.defender != att.opponent:
            await att.defender.send(att.attack_messages[3] + att.defense_messages[3])
        if att.person_hit != att.opponent:
            await att.person_hit.send(att.attack_messages[4] + att.defense_messages[4])

    async def die(self, target: MudObject, attacker: Player):
        await target.send("You have been defeated!")
        if isinstance(target, Player):
            target.attrs["hp"] = 100
            target.location = self.driver.objects["ethereal_veil_start"]
            self.driver.save_object(target)
            await target.send("You awaken in the Ethereal Veil...")
        else:
            del self.driver.objects[target.oid]
        self.stop_fight(target, attacker)

    async def after_attack(self, att: Attack):
        # Placeholder for post-attack cleanup
        pass

    def stop_fight(self, obj: MudObject, opponent: MudObject):
        if obj.oid in self.combatants:
            del self.combatants[obj.oid]
        if opponent.oid in self.combatants:
            del self.combatants[opponent.oid]
        if obj.oid in self.hunting:
            del self.hunting[obj.oid]
        if opponent.oid in self.hunting:
            del self.hunting[opponent.oid]
        self.surrender_to[obj.oid] = [s for s in self.surrender_to.get(obj.oid, []) if s != opponent.oid]
        self.surrender_from[obj.oid] = [s for s in self.surrender_from.get(obj.oid, []) if s != opponent.oid]

    async def event_surrender(self, victim: Player, attacker: MudObject):
        mercy = attacker.attrs.get("tactics", Tactics()).mercy
        self.surrender_to[victim.oid] = self.surrender_to.get(victim.oid, []) + [attacker.oid]

        if mercy == "ask":
            if isinstance(attacker, Player):
                self.surrender_from[attacker.oid] = self.surrender_from.get(attacker.oid, []) + [victim.oid]
                await attacker.send(f"{victim.name} has surrendered to you. Use 'accept {victim.name}' or 'reject {victim.name}'.")
            else:
                # NPC logic - accept for now
                await self.accepted_surrender(victim, attacker)
        elif mercy == "always":
            await self.accepted_surrender(victim, attacker)
        else:
            await self.refused_surrender(victim, attacker)

    async def accepted_surrender(self, victim: Player, attacker: MudObject):
        self.surrender_to[victim.oid] = [s for s in self.surrender_to.get(victim.oid, []) if s != attacker.oid]
        await victim.send(f"{attacker.name} accepts your surrender.")
        self.stop_fight(victim, attacker)

    async def refused_surrender(self, victim: Player, attacker: MudObject):
        self.surrender_to[victim.oid] = [s for s in self.surrender_to.get(victim.oid, []) if s != attacker.oid]
        await victim.send(f"{attacker.name} refuses your surrender.")

    def is_fighting(self, obj: MudObject, opponent: MudObject, actively: bool = False) -> bool:
        if actively:
            return obj.oid in self.combatants and self.combatants[obj.oid] == opponent.oid
        return obj.oid in self.combatants or obj.oid in self.hunting

# Initialize combat handler
combat_handler = CombatHandler()

async def init(driver_instance):
    await combat_handler.init(driver_instance)
