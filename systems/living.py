# /mnt/home2/mud/systems/living.py
from typing import Dict, List, Optional, Tuple, Union, Callable, ClassVar
from ..driver import driver, Player, MudObject
from .classes import class_handler, ClassHandler
from .quest import quest_handler, QuestHandler
from .library import library, Library
import asyncio
import random
import math

class living_data:
    def __init__(self):
        self.handicap = 0
        self.burden = 0
        self.followers = []
        self.it_them = None
        self.to_drop = []
        self.burden_call = None

class messages:
    def __init__(self):
        self.msgin = "$N arrive$s from $F."
        self.msgout = "$N leave$s $T."
        self.mmsgin = "$N appear$s out of the ground."
        self.mmsgout = "$N disappear$s in a puff of smoke."

# Constants from /include/living.h
MAX_AL = 10000
MAX_FAVOUR = 100
VERBOSE_TYPES = ["combat", "look", "score", "names", "htell", "finger", "errors", "quit"]
STANDING = "standing"
POSITION_ARRAY_SIZE = 3
POS_ON_OBJECT = 0
POS_MULTIPLE = 1
POS_TYPE = 2
POSITION_TYPE_INDEX = 0
POSITION_ME_MESS_INDEX = 1
POSITION_REST_MESS = 2
POSITION_ONLY_TYPE_SIZE = 1
POSITION_MESS_SIZE = 3
MAX_CREATOR_INVEN = 100
MAX_INVEN = 50
WILL_POWER = 1000
REL_DIRS = ["forward", "right forward", "right", "right backward", "backward", "left backward", "left", "left forward"]
ABS_FACING = {
    "north": 0, "northeast": 1, "east": 2, "southeast": 3,
    "south": 4, "southwest": 5, "west": 6, "northwest": 7
}
LENGTHEN = {"n": "north", "ne": "northeast", "e": "east", "se": "southeast",
            "s": "south", "sw": "southwest", "w": "west", "nw": "northwest"}

class Living(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.attrs: Dict = {}
        self._liv_data = living_data()
        self._messages = messages()
        self.alignment = 0
        self.facing = [0, ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"], ["up", "down"]]
        self.verbose = {t: 1 for t in VERBOSE_TYPES}
        self.deity = None
        self.deity_favour = {}
        self.position = STANDING
        self.default_position = None
        self.always_use_default_position = 0
        self.position_on = None
        self.max_items = 50
        self.attrs["adjectives"] = self.attrs.get("adjectives", []) + ["living"]
        self.attrs["skills"] = {}
        self.attrs["money"] = {}
        self.attrs["max_hp"] = 100
        self.attrs["hp"] = 100
        self.attrs["max_gp"] = 100
        self.attrs["gp"] = 100
        self.attrs["drink_info"] = {"alcohol": 0, "food": 0, "drink": 0}
        self.attrs["xp"] = 0
        self.attrs["guild"] = None
        self.attrs["guild_level"] = 0
        living_handler.set_living_name(name, self)

    async def heart_beat(self):
        pass  # Placeholder for stats and combat heartbeats

    def query_pronoun(self) -> str:
        gender = self.attrs.get("gender", 0)
        return {0: "it", 1: "he", 2: "she"}.get(gender, "it")

    def query_possessive(self) -> str:
        gender = self.attrs.get("gender", 0)
        return {0: "its", 1: "his", 2: "her"}.get(gender, "its")

    def query_objective(self) -> str:
        gender = self.attrs.get("gender", 0)
        return {0: "it", 1: "him", 2: "her"}.get(gender, "it")

    def query_weight(self, actual: bool = False) -> int:
        if not actual and self.attrs.get("dead", False):
            return 0
        return self.attrs.get("weight", 0)

    def query_burden(self) -> int:
        return self._liv_data.burden

    def query_handicap(self) -> int:
        return self._liv_data.handicap

    def calc_burden(self):
        self._liv_data.burden_call = None
        burden = sum(obj.query_complete_weight() for obj in self.inventory)
        for thing in self.attrs.get("wearing", []):
            burden -= thing.query_complete_weight() // 2
        hands = {}
        for thing in self.attrs.get("holding", []):
            hands[thing] = hands.get(thing, 0) + 1
        for thing, count in hands.items():
            burden += thing.query_complete_weight() // count
        max_weight = self.query_max_weight()
        self._liv_data.burden = 50 if not max_weight else (100 * burden) // max_weight
        new_handicap = max(0, (self._liv_data.burden // 25) - 1)
        if self._liv_data.handicap != new_handicap:
            self.adjust_bonus_dex(self._liv_data.handicap - new_handicap)
            self._liv_data.handicap = new_handicap

    def burden_string(self) -> str:
        handicap = self._liv_data.handicap
        if handicap == 0:
            return "unburdened"
        elif handicap == 1:
            return "burdened"
        elif handicap == 2:
            return "heavily burdened"
        elif handicap == 3:
            return "very heavily burdened"
        return "incredibly heavily burdened"

    def eat_this(self, food: MudObject):
        asyncio.create_task(self.command(f"eat {food.oid}"))

    def test_add(self, ob: MudObject, flag: int) -> bool:
        if len(self.inventory) > self.max_items:
            return False
        return not flag

    def test_remove(self, ob: MudObject, flag: int, dest: Union[str, MudObject]) -> bool:
        if flag:
            return False
        if not self.driver.this_player() or self.driver.this_player() == self:
            return not flag
        if isinstance(dest, str):
            thing = self.driver.objects.get(dest)
        elif isinstance(dest, MudObject):
            thing = dest
            dest = thing.oid
        else:
            thing = None
        if thing and (thing.attrs.get("corpse", False) or dest == "/room/rubbish"):
            return not flag
        if self.attrs.get("passed_out", False):
            return False
        self.driver.event(self.environment, "theft", self.driver.this_player(), self, ob)
        return not flag

    def query_al(self) -> int:
        return self.alignment

    def set_al(self, number: int):
        self.alignment = number

    def adjust_al(self, number: int) -> int:
        self.alignment += number
        self.alignment = max(-MAX_AL, min(MAX_AL, self.alignment))
        return self.alignment

    def adjust_alignment(self, number: int) -> int:
        change = -(number + self.alignment // 5) // 20
        return self.adjust_al(change)

    def align_string(self) -> str:
        al = self.alignment
        if al <= -5001:
            return "extremely good"
        elif al <= -2501:
            return "very good"
        elif al <= -1251:
            return "quite good"
        elif al <= -601:
            return "good"
        elif al <= -301:
            return "barely good"
        elif al <= 300:
            return "neutral"
        elif al <= 600:
            return "barely evil"
        elif al <= 1250:
            return "evil"
        elif al <= 2500:
            return "quite evil"
        elif al <= 5000:
            return "very evil"
        return "extremely evil"

    def query_deity(self) -> Optional[str]:
        return self.deity

    def set_deity(self, word: str):
        self.deity = word

    def query_msgin(self) -> str:
        return self._messages.msgin

    def query_msgout(self) -> str:
        return self._messages.msgout

    def set_msgin(self, str_: str) -> bool:
        if "$N" not in str_ or "$F" not in str_:
            return False
        self._messages.msgin = str_
        return True

    def set_msgout(self, str_: str) -> bool:
        if "$N" not in str_ or "$T" not in str_:
            return False
        self._messages.msgout = str_
        return True

    def query_mmsgin(self) -> str:
        return self._messages.mmsgin

    def query_mmsgout(self) -> str:
        return self._messages.mmsgout

    def set_mmsgin(self, str_: str) -> bool:
        if "$N" not in str_:
            return False
        self._messages.mmsgin = str_
        return True

    def set_mmsgout(self, str_: str) -> bool:
        if "$N" not in str_:
            return False
        self._messages.mmsgout = str_
        return True

    def query_facing(self) -> List:
        return self.facing.copy()

    def set_facing(self, args: List):
        self.facing = args

    def find_rel(self, word: str, from_: int) -> str:
        i = self.facing[1].index(word)
        if i != -1:
            i = (i + 8 - self.facing[0]) % 8
            return REL_DIRS[3 * i + from_]
        i = self.facing[2].index(word)
        if i != -1:
            return ["up", "down"][i]
        return word

    def find_abs(self, word: str) -> str:
        i = REL_DIRS.index(word)
        if i != -1:
            i = (i // 3 + self.facing[0]) % 8
            return self.facing[1][i]
        i = ["up", "down"].index(word)
        if i != -1:
            return self.facing[2][i]
        return word

    def reorient_rel(self, word: str) -> str:
        i = REL_DIRS.index(word)
        if i != -1:
            i = (i // 3 + self.facing[0]) % 8
            self.facing[0] = i
            return self.facing[1][i]
        i = ["up", "down"].index(word)
        if i != -1:
            return self.facing[2][i]
        return word

    def reorient_abs(self, verb: str):
        if verb in ABS_FACING:
            self.facing[0] = ABS_FACING[verb] % 8

    def set_dragging(self, thing: MudObject):
        self.attrs["dragging"] = thing

    def query_dragging(self) -> Optional[MudObject]:
        return self.attrs.get("dragging")

    def reset_dragging(self):
        self.attrs["dragging"] = None

    async def room_look(self) -> bool:
        if self.attrs.get("unknown_move", False) or not (self.attrs.get("interactive", False) or self.attrs.get("slave", False)):
            return False
        if self.verbose.get("look", 1):
            await self.command("look")
        else:
            await self.command("glance")
        return True

    def query_verbose(self, type_: str) -> int:
        return self.verbose.get(type_, 1)

    def set_verbose(self, type_: str, val: int):
        if type_ in VERBOSE_TYPES:
            self.verbose[type_] = val

    def query_verbose_types(self) -> List[str]:
        return VERBOSE_TYPES

    async def move_with_look(self, dest: Union[str, MudObject], messin: str = "", messout: str = "") -> bool:
        self.return_to_default_position(1)
        if not await self.move(dest, messin, messout):
            return False
        await self.room_look()
        self.return_to_default_position(1)
        return True

    async def exit_command(self, word: str, verb: Union[str, List] = None, thing: MudObject = None, redirection: bool = False) -> bool:
        if not self.environment:
            return False
        if not verb:
            verb = word
            bits = word.split()
            word = " ".join(bits[1:]) if len(bits) > 1 else ""
        else:
            if isinstance(verb, list):
                special_mess, verb = verb[1], verb[0]
            bits = verb.split()
            word = " ".join(bits[1:]) if len(bits) > 1 else ""
        verb = LENGTHEN.get(verb, verb)
        exits = self.environment.attrs.get("exits", [])
        if verb not in exits:
            verb = self.find_abs(verb)
            if verb not in exits:
                return False
        if verb in ABS_FACING:
            self.facing[0] = ABS_FACING[verb] % 8
        thing = thing or self
        # Placeholder for exit_move via room_handler
        return True

    def become_flummoxed(self):
        will = self.attrs.get("int", 10) * self.attrs.get("wis", 10)
        if will < random.randint(0, WILL_POWER):
            self.attrs["interrupt_ritual"] = True
        if will < random.randint(0, WILL_POWER):
            self.attrs["interrupt_spell"] = True
        if will < random.randint(0, WILL_POWER):
            self.attrs["stop_fight"] = True

    async def run_away(self) -> bool:
        direcs = self.environment.attrs.get("dest_dir", [])
        old_env = self.environment
        while direcs:
            i = random.randint(0, len(direcs) // 2 - 1) * 2
            if await self.exit_command(direcs[i]):
                self.driver.event(old_env, "run_away", direcs[i], direcs[i + 1])
                return True
            direcs = direcs[:i] + direcs[i+2:]
        return False

    def stats(self) -> List[Tuple[str, Union[int, str]]]:
        return [
            ("max_hp", self.attrs.get("max_hp", 0)),
            ("hp", self.attrs.get("hp", 0)),
            ("max_gp", self.attrs.get("max_gp", 0)),
            ("gp", self.attrs.get("gp", 0)),
            ("alcohol", self.attrs["drink_info"].get("alcohol", 0)),
            ("food", self.attrs["drink_info"].get("food", 0)),
            ("drink", self.attrs["drink_info"].get("drink", 0)),
            ("gender", self.attrs.get("gender", 0)),
            ("alignment", self.query_al()),
            ("deity", self.deity or "None"),
            ("total money", self.attrs.get("money", {}).get("value", 0)),
            ("xp", self.attrs.get("xp", 0))
        ]

    def query_it_them(self) -> Optional[List[MudObject]]:
        return self._liv_data.it_them

    def set_it_them(self, args: List[MudObject]):
        self._liv_data.it_them = args

    def add_follower(self, ob: MudObject) -> bool:
        if ob == self or ob in self._liv_data.followers:
            return False
        self._liv_data.followers.append(ob)
        return True

    def remove_follower(self, ob: MudObject) -> bool:
        if ob in self._liv_data.followers:
            self._liv_data.followers.remove(ob)
            return True
        return False

    def check_doing_follow(self, thing: MudObject, verb: str, special: str) -> bool:
        return True

    def query_current_room(self) -> Optional[MudObject]:
        return self.environment

    def query_followers(self) -> List[MudObject]:
        return [f for f in self._liv_data.followers if f]

    def do_burden_call(self):
        if self._liv_data.burden_call:
            self.driver.remove_call_out(self._liv_data.burden_call)
        self._liv_data.burden_call = self.driver.call_out(self.calc_burden, 1)

    def query_burden_limit(self) -> int:
        return MAX_CREATOR_INVEN if self.attrs.get("creator", False) else MAX_INVEN

    async def event_enter(self, thing: MudObject, mess: str, from_: MudObject):
        if thing.environment == self:
            self.do_burden_call()
            if len(self.inventory) > self.query_burden_limit():
                self._liv_data.to_drop.append(thing)
                self.driver.call_out(self.test_number_of_items, 5 + random.randint(0, 5))

    async def event_exit(self, thing: MudObject, mess: str, to: MudObject):
        if thing.environment == self:
            self.do_burden_call()

    async def test_number_of_items(self):
        things = [obj for obj in self.inventory if obj not in self.attrs.get("armours", []) and obj not in self.attrs.get("holding", [])]
        how_many = len(things) - self.query_burden_limit()
        if how_many < 1:
            return
        self._liv_data.to_drop = [t for t in self._liv_data.to_drop if t]
        dropped = []
        while how_many > 0 and things:
            thing = self._liv_data.to_drop[random.randint(0, len(self._liv_data.to_drop)-1)] if self._liv_data.to_drop else things[random.randint(0, len(things)-1)]
            things.remove(thing)
            if thing in self._liv_data.to_drop:
                self._liv_data.to_drop.remove(thing)
            if not thing or not thing.attrs.get("short") or thing.attrs.get("cannot_fumble") or thing.attrs.get("coin") or thing.environment != self:
                continue
            if await thing.move(self.environment):
                how_many -= 1
                dropped.append(thing)
        self._liv_data.to_drop = []
        if dropped:
            await self.send(f"Whoops! You tried to carry too many things and fumbled {self.query_multiple_short([d.name for d in dropped])}.\n")
            await self.driver.tell_room(self.environment, f"{self.name.capitalize()} juggles around {self.query_possessive()} stuff and fumbles {self.query_multiple_short([d.name for d in dropped])}.\n", self)

    def force_burden_recalculate(self):
        self.do_burden_call()
        self.driver.call_out(self.test_number_of_items, 5 + random.randint(0, 5))

    def query_position(self) -> str:
        return self.position

    def set_position(self, name: str):
        self.position = name

    def set_position_on(self, ob: Union[str, MudObject]):
        if not self.position_on:
            self.position_on = [None] * POSITION_ARRAY_SIZE
        self.position_on[POS_ON_OBJECT] = ob

    def set_position_multiple(self, mult: int):
        if not self.position_on:
            self.position_on = [None] * POSITION_ARRAY_SIZE
        self.position_on[POS_MULTIPLE] = mult

    def query_position_multiple(self) -> int:
        return self.position_on[POS_MULTIPLE] if self.position_on else 0

    def set_position_type(self, type_: str):
        if not self.position_on:
            self.position_on = [None] * POSITION_ARRAY_SIZE
        self.position_on[POS_TYPE] = type_

    def query_position_type(self) -> str:
        return self.position_on[POS_TYPE] if self.position_on and self.position_on[POS_TYPE] else "on"

    def query_position_on(self) -> Optional[Union[str, MudObject]]:
        return self.position_on[POS_ON_OBJECT] if self.position_on else None

    def query_position_on_short(self) -> str:
        if not self.position_on or not self.position_on[POS_ON_OBJECT]:
            return ""
        if isinstance(self.position_on[POS_ON_OBJECT], str):
            return self.position_on[POS_ON_OBJECT]
        return self.position_on[POS_ON_OBJECT].name

    def query_position_long(self) -> str:
        if self.position != STANDING or self.position_on:
            if self.position_on:
                return f"{self.query_pronoun()} is {self.query_position_type()} {self.query_position_on_short()}.\n"
            return f"{self.query_pronoun()} is {self.position} on the floor.\n"
        return ""

    def query_position_short(self) -> str:
        if not self.position_on or not self.position_on[POS_ON_OBJECT]:
            return self.position
        return f"{self.position} {self.query_position_type()} {self.query_position_on_short()}"

    def set_always_use_default_position(self, flag: int):
        self.always_use_default_position = flag

    def query_always_use_default_position(self) -> int:
        return self.always_use_default_position

    def query_default_position(self) -> Union[str, List, Callable]:
        pos = self.default_position
        if isinstance(pos, str) or (isinstance(pos, list) and len(pos) in [POSITION_ONLY_TYPE_SIZE, POSITION_MESS_SIZE]) or callable(pos):
            return pos
        return "standing"

    def set_default_position(self, str_: Union[str, List, Callable]):
        if isinstance(str_, str) and str_ != "standing":
            self.default_position = str_
        elif not str_ or str_ == "standing":
            self.default_position = None
        elif isinstance(str_, list) and len(str_) in [POSITION_ONLY_TYPE_SIZE, POSITION_MESS_SIZE]:
            self.default_position = str_
        elif callable(str_):
            self.default_position = str_

    async def return_to_default_position(self, leaving: bool):
        pos = self.query_default_position() if self.query_always_use_default_position() else (self.environment.attrs.get("default_position", None) if self.environment else None) or self.query_default_position()
        if callable(pos):
            if not pos(self, leaving):
                pos = self.environment.attrs.get("default_position", None) if self.environment else "standing"
        if isinstance(pos, str):
            if self.position != pos or (leaving and self.query_position_on()):
                self.position = pos
                self.set_position_on(None)
                self.set_position_type(None)
                self.set_position_multiple(0)
        elif isinstance(pos, list):
            if self.position != pos[POSITION_TYPE_INDEX]:
                if len(pos) > 1:
                    if pos[POSITION_ME_MESS_INDEX]:
                        await self.send(pos[POSITION_ME_MESS_INDEX])
                    if len(pos) > 2 and pos[POSITION_REST_MESS]:
                        await self.driver.tell_room(self.environment, pos[POSITION_REST_MESS], self)
                self.set_position(pos[POSITION_TYPE_INDEX])
                self.set_position_on(None)
                self.set_position_type(None)
                self.set_position_multiple(0)

    def query_deity_favour(self, god: str) -> int:
        return self.deity_favour.get(god, 0)

    def adjust_deity_favour(self, god: str, amount: int):
        if god not in self.deity_favour:
            self.deity_favour[god] = 0
        self.deity_favour[god] += amount
        self.deity_favour[god] = max(-MAX_FAVOUR, min(MAX_FAVOUR, self.deity_favour[god]))

    def query_all_deity_favour(self) -> Dict[str, int]:
        return self.deity_favour.copy()

    def query_quest_points(self) -> int:
        return library.query_quest_points(self.name)

    # Replace guild methods with class handler calls
    def join_guild(self, guild: str):
        return asyncio.run(class_handler.class_command(self, self, f"join {guild}"))

    def leave_guild(self):
        return asyncio.run(class_handler.class_command(self, self, "leave"))

    def query_guild(self) -> Optional[str]:
        return class_handler.query_class(self)

    def query_guild_level(self) -> int:
        return class_handler.query_class_level(self)

    def set_guild_level(self, level: int):
        class_handler.set_class_level(self, level)

    def advancement_restriction(self) -> bool:
        return class_handler.advancement_restriction(self)

    # Taskmaster Methods
    def add_skill_level(self, skill: str, level: int, prev_ob: MudObject) -> bool:
        if self.advancement_restriction():
            return False
        current = self.attrs["skills"].get(skill, 0)
        self.attrs["skills"][skill] = current + level
        return True

    def stat_modify(self, upper: int, skill: str) -> int:
        # Simplified stat-based modification
        stat_bonus = (self.attrs.get("str", 10) + self.attrs.get("dex", 10)) // 20
        return max(0, upper + stat_bonus)

    # Options Methods
    def query_inform_types(self) -> List[str]:
        return ["tell", "say"]

    def query_player_clubs(self) -> List[str]:
        return ["guild"]

    def adjust_bonus_dex(self, amount: int):
        self.attrs["dex_bonus"] = self.attrs.get("dex_bonus", 0) + amount

    def query_max_weight(self) -> int:
        return self.attrs.get("max_weight", 100)

class LivingHandler:
    def __init__(self):
        self._lnames: Dict[str, List[MudObject]] = {}
        self._players: Dict[str, MudObject] = {}

    def check_lnames(self, names: List[str]):
        for key in names:
            if key in self._lnames:
                bing = [x for x in self._lnames[key] if x]
                if bing:
                    self._lnames[key] = bing
                else:
                    del self._lnames[key]
            else:
                del self._lnames[key]

    def check_players(self, names: List[str]):
        for key in names:
            if key in self._players:
                bing = [x for x in self._players[key] if x]
                if bing:
                    self._players[key] = bing
                else:
                    del self._players[key]
            else:
                del self._players[key]

    def remove_garbage(self):
        names = list(self._lnames.keys())
        for i in range(0, len(names), 50):
            self.driver.call_out(lambda n=names[i:i+50]: self.check_lnames(n), i // 25)
        names = list(self._players.keys())
        for i in range(0, len(names), 50):
            self.driver.call_out(lambda n=names[i:i+50]: self.check_players(n), i // 25)

    def set_living_name(self, name: str, ob: MudObject):
        if not name or not isinstance(ob, MudObject):
            return
        if name not in self._lnames:
            self._lnames[name] = [ob]
        else:
            self._lnames[name].append(ob)

    def named_livings(self) -> List[MudObject]:
        ret = []
        for name in self._lnames:
            ret.extend([x for x in self._lnames[name] if x])
        return ret

    def find_living(self, name: str) -> Optional[MudObject]:
        if name in self._lnames:
            self._lnames[name] = [x for x in self._lnames[name] if x]
            if self._lnames[name]:
                return self._lnames[name][-1]
        return None

    def find_player(self, name: str) -> Optional[MudObject]:
        if name in self._players:
            return self._players[name]
        players = [p for p in driver.players if p.attrs.get("name") == name]
        if players:
            self._players[name] = players[0]
            return players[0]
        if name in self._lnames:
            tmp = [x for x in self._lnames[name] if x and x.attrs.get("player", False)]
            if tmp:
                return tmp[0]
        return None

living_handler = LivingHandler()
