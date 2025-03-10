# /mnt/home2/mud/systems/room.py
# Imported to: rooftop.py, terrain_handler.py, living.py, player.py, object.py
# Imports from: driver.py, desc.py, extra_look.py, light.py, property.py, export_inventory.py, help_files.py, effects.py, weather_handler.py, situation_changer.py, door.py, terrain_track_handler.py, magic_handler.py

from typing import Dict, List, Optional, Tuple, Union, Callable
from ..driver import driver, Player, MudObject
import asyncio
import math
import time
import random
from . import desc, extra_look, light, property, export_inventory, help_files, effects
from .weather_handler import WeatherHandler
from .situation_changer import SituationChanger
from .door import Door  # Assuming door.py exists
from .terrain_track_handler import TerrainTrackHandler  # Stubbed if not done
from .magic_handler import MagicHandler  # Stubbed if not done

# Constants (from includes like room.h, situations.h)
ENCHANT_HALF = 3600
ROOM_DEST, ROOM_EXIT, ROOM_MESS, ROOM_OBV, ROOM_REL, ROOM_FUNC, ROOM_SIZE, ROOM_GRADE, ROOM_DELTA, ROOM_LOOK, ROOM_LOOK_FUNC, ROOM_LINK_MESS = range(12)
ROOM_DEFAULT_INDEX, ROOM_DAY_INDEX, ROOM_NIGHT_INDEX = 0, 1, 2
ROOM_VOID = "/room/void"
SHORTEN = {"north": "n", "northeast": "ne", "east": "e", "southeast": "se", "south": "s", "southwest": "sw", "west": "w", "northwest": "nw", "up": "u", "down": "d"}
STD_ORDERS = ["north", [0, 1, 0], "northeast", [1, 1, 0], "east", [1, 0, 0], "southeast", [1, -1, 0], "south", [0, -1, 0], "southwest", [-1, -1, 0], "west", [-1, 0, 0], "northwest", [-1, 1, 0], "up", [0, 0, 1], "down", [0, 0, -1]]
WHEN_ANY_TIME = 0xFFFFFF

class Room(MudObject, desc.Desc, extra_look.ExtraLook, light.Light, property.Property, export_inventory.ExportInventory, help_files.HelpFiles, effects.Effects):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.do_setup: bool = False
        self.co_ord: Optional[List[int]] = None
        self.co_ord_calculated: bool = False
        self.long_exit: Optional[str] = None
        self.long_exit_mxp: Optional[str] = None
        self.short_exit: Optional[str] = None
        self.theft_handler: Optional[str] = "/obj/handlers/theft_handler"
        self.aliases: List[str] = []
        self._exits: List[str] = []
        self.item: Optional[MudObject] = None
        self.chatter: Optional[MudObject] = None
        self.sitchanger: Optional[SituationChanger] = None
        self.linker: Optional[MudObject] = None
        self.terrain: Optional[MudObject] = None
        self.wall: Optional[MudObject] = None
        self.rooftop: Optional[MudObject] = None
        self.hidden_objects: List[MudObject] = []
        self._use_internal_objects: List[MudObject] = []
        self.door_control: Dict[str, Union[str, Door]] = {}
        self.dest_other: List[Union[str, List]] = []
        self.enchant_time: int = time.time()
        self.background_enchant: int = 0
        self.dynamic_enchant: float = 0.0
        self.last_visited: int = 0
        self.variablelongs: Optional[List[str]] = None
        self.variablechats: Optional[List[Union[List, None]]] = None
        self.variableitems: Optional[List[List]] = None
        self.is_day: int = -1
        self.not_replaceable: bool = False
        self.weather_handler = WeatherHandler() if not hasattr(driver, "weather_handler") else driver.weather_handler
        self.tent_owner: Optional[str] = None
        self.tent_decay: int = 0
        self.magic_aura: int = 0  # New: Ambient magic level
        self.track_handler = TerrainTrackHandler()  # Stubbed
        self.magic_handler = MagicHandler()  # Stubbed
        self.attrs["location"] = "inside"
        self.attrs["here"] = "on the ground"
        self.attrs["arcane_resonance"] = 0  # FR-specific enchantment
        if not self.do_setup:
            self.setup()
            self.reset()
        asyncio.create_task(self.room_loop())

    async def room_loop(self):
        """Continuous room update loop."""
        while True:
            await asyncio.sleep(60)
            await self.update_weather()
            await self.check_tent()
            self.check_magic_aura()
            if self.sitchanger:
                self.sitchanger.check_situations()

    async def update_weather(self):
        """Updates weather effects with temperature and afflictions."""
        if self.attrs["location"] == "outside":
            temp = self.weather_handler.query_temperature(self.oid)
            if temp > 90:
                await self.tell_room("The air shimmers with oppressive heat.\n")
                self.add_effect("heatstroke", 300)
            elif temp < 32:
                await self.tell_room("A biting chill seeps into the air.\n")
                self.add_effect("hypothermia", 300)

    def check_magic_aura(self):
        """Updates ambient magic aura."""
        self.magic_aura = min(self.magic_aura + random.randint(-5, 5), 100)
        if self.magic_aura > 75:
            self.add_extra_look("A wild surge of Netherese energy crackles faintly.\n")

    def query_is_room(self) -> bool:
        return True

    def query_enchant(self) -> int:
        enchant_level = int(0.5 + self.dynamic_enchant * math.exp(-0.693 * (time.time() - self.enchant_time) / ENCHANT_HALF) + self.background_enchant + self.attrs["arcane_resonance"])
        return min(enchant_level, 5000)

    def set_enchant(self, number: int) -> int:
        number = max(0, number)
        if driver.previous_object() == self:
            self.background_enchant = number
            self.dynamic_enchant = 0.0
        else:
            self.dynamic_enchant = number - self.background_enchant
        self.enchant_time = time.time()
        return number

    def add_enchant(self, number: int) -> int:
        self.dynamic_enchant = self.dynamic_enchant * math.exp(-0.693 * (time.time() - self.enchant_time) / ENCHANT_HALF) + number
        self.enchant_time = time.time()
        return int(0.5 + self.dynamic_enchant) + self.background_enchant

    def set_background_enchant(self, number: int):
        self.background_enchant = number

    def set_dynamic_enchant(self, number: float):
        self.dynamic_enchant = number
        self.enchant_time = time.time()

    def query_background_enchant(self) -> int:
        return self.background_enchant

    def query_dynamic_enchant(self) -> float:
        self.dynamic_enchant = self.dynamic_enchant * math.exp(-0.693 * (time.time() - self.enchant_time) / ENCHANT_HALF)
        self.enchant_time = time.time()
        return self.dynamic_enchant

    def query_co_ord(self) -> Optional[List[int]]:
        return self.co_ord.copy() if self.co_ord else None

    def set_co_ord(self, new_co_ord: List[int]):
        if not isinstance(new_co_ord, list) or len(new_co_ord) != 3:
            print("Warning: Co-ordinate must be a 3-element array.")
            return
        self.co_ord = new_co_ord
        self.co_ord_calculated = driver.previous_object() != self
        self.track_handler.update_position(self.oid, new_co_ord)

    def flush_co_ord(self):
        self.co_ord = None
        self.co_ord_calculated = False

    def query_co_ord_calculated(self) -> bool:
        return self.co_ord_calculated

    def query_long_exit(self) -> Optional[str]:
        return self.long_exit

    def query_long_exit_mxp(self) -> Optional[str]:
        return self.long_exit_mxp

    def calc_long_exit(self):
        words = []
        for i in range(0, len(self.dest_other), 2):
            tmp = self.dest_other[i + 1][ROOM_OBV]
            if not tmp:
                continue
            add = False
            if isinstance(tmp, int) and tmp:
                add = True
            elif isinstance(tmp, str):
                add = getattr(self, tmp)(self.dest_other[i])
            elif isinstance(tmp, list):
                add = getattr(tmp[0], tmp[1])(self.dest_other[i])
            if add:
                words.append(f"$R$-{self.dest_other[i]}$R$" if self.dest_other[i + 1][ROOM_REL] else self.dest_other[i])
        if not words:
            self.long_exit = "There are no obvious exits."
            self.long_exit_mxp = "There are no obvious exits."
        elif len(words) == 1:
            self.long_exit = f"There is one obvious exit: {words[0]}."
            self.long_exit_mxp = f"There is one obvious exit: {words[0]}."
        else:
            self.long_exit = f"There are {self.query_num(len(words), 0)} obvious exits: {self.query_multiple_short(words)}."
            self.long_exit_mxp = f"There are {self.query_num(len(words), 0)} obvious exits: {self.query_multiple_short(words)}."

    def query_theft_handler(self) -> Optional[str]:
        return self.theft_handler

    def set_theft_handler(self, word: str):
        self.theft_handler = word

    def query_aliases(self) -> List[str]:
        return self.aliases.copy()

    def add_alias(self, names: Union[str, List[str]], word: str):
        if not self.aliases:
            self.aliases = []
        if isinstance(names, list):
            for name in names:
                self.add_alias(name, word)
            return
        self.aliases.extend([word, names])
        driver.call_out(self.calc_exits, 1)

    def remove_alias(self, names: Union[str, List[str]], word: str):
        if not self.aliases:
            return
        if isinstance(names, list):
            for name in names:
                self.remove_alias(name, word)
            return
        i = len(self.aliases) - 2
        while i >= -1:
            if self.aliases[i] == word and self.aliases[i + 1] == names:
                self.aliases = self.aliases[:i] + self.aliases[i + 2:]
            i -= 2
        driver.call_out(self.calc_exits, 1)

    def query_exits(self) -> List[str]:
        return self._exits.copy()

    def reset_exits(self):
        self._exits = []

    def query_item(self) -> Optional[MudObject]:
        return self.item

    def query_chatter(self) -> Optional[MudObject]:
        return self.chatter

    def query_situation_changer(self) -> Optional[SituationChanger]:
        return self.sitchanger

    def query_linker(self) -> Optional[MudObject]:
        return self.linker

    def query_terrain(self) -> Optional[MudObject]:
        return self.terrain

    def query_wall(self) -> Optional[MudObject]:
        return self.wall

    def query_hidden_objects(self) -> List[MudObject]:
        return self.hidden_objects.copy()

    def add_hidden_object(self, thing: MudObject) -> bool:
        if thing in self.hidden_objects:
            return False
        self.hidden_objects.append(thing)
        return True

    def remove_hidden_object(self, thing: MudObject) -> bool:
        if thing not in self.hidden_objects:
            return False
        self.hidden_objects.remove(thing)
        return True

    def add_use_internal_object(self, thing: MudObject):
        if thing not in self._use_internal_objects:
            self._use_internal_objects.append(thing)

    def remove_use_internal_object(self, thing: MudObject):
        if thing in self._use_internal_objects:
            self._use_internal_objects.remove(thing)

    def query_use_internal_objects(self) -> List[MudObject]:
        return self._use_internal_objects.copy()

    def query_door_control(self, direc: str = None, name: str = None) -> Union[Dict, Optional[Union[str, Door]]]:
        if not direc:
            return self.door_control.copy()
        key = f"{direc} {name}" if name else direc
        return self.door_control.get(key)

    def query_dest_other(self, direc: str = None) -> Union[List, Optional[List]]:
        if not direc:
            return self.dest_other.copy()
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        return self.dest_other[i + 1].copy() if i != -1 else None

    def query_dest_dir(self, thing: MudObject = None) -> List[str]:
        ret = []
        for i in range(0, len(self.dest_other), 2):
            direc = self.dest_other[i]
            if not self.dest_other[i + 1][ROOM_REL] or not thing:
                ret.extend([direc, self.dest_other[i + 1][ROOM_DEST]])
            else:
                ret.extend([thing.find_rel(direc), self.dest_other[i + 1][ROOM_DEST]])
        return ret

    def query_direc(self, thing: MudObject = None) -> List[str]:
        ret = []
        for i in range(0, len(self.dest_other), 2):
            direc = self.dest_other[i]
            if not self.dest_other[i + 1][ROOM_REL] or not thing:
                ret.append(direc)
            else:
                ret.append(thing.find_rel(direc))
        return ret

    def query_destination(self, exit: str) -> str:
        i = self.dest_other.index(exit) if exit in self.dest_other else -1
        if i == -1 and driver.this_player():
            i = self.dest_other.index(driver.this_player().reorient_rel(exit)) if driver.this_player().reorient_rel(exit) in self.dest_other else -1
        return self.dest_other[i + 1][ROOM_DEST] if i != -1 else ROOM_VOID

    def test_add(self, thing: MudObject, flag: int) -> bool:
        return True

    def test_remove(self, thing: MudObject, flag: int, dest: Union[str, MudObject]) -> bool:
        return True

    def add_weight(self, number: int) -> bool:
        return True

    def query_no_writing(self) -> bool:
        return True

    def query_decay(self) -> int:
        return 10

    def query_day(self) -> int:
        return self.is_day

    def attack_speed(self) -> int:
        return 15

    def query_dark_mess(self) -> str:
        return self.attrs.get("dark mess", "Darkness cloaks this place in shadow.\n")

    def set_dark_mess(self, word: str):
        self.attrs["dark mess"] = word

    def query_bright_mess(self) -> str:
        return self.attrs.get("bright mess", "Blinding light obscures all detail!\n")

    def set_bright_mess(self, word: str):
        self.attrs["bright mess"] = word

    def query_room_size(self) -> Union[int, List[int]]:
        return self.attrs.get("room size", 10)

    def query_room_size_array(self) -> List[int]:
        room_size = self.query_room_size()
        return room_size if isinstance(room_size, list) else [room_size] * 3

    def set_room_size(self, number: Union[int, List[int]]):
        if isinstance(number, int):
            self.attrs["room size"] = number
        elif isinstance(number, list) and len(number) == 3:
            self.attrs["room size"] = number
        else:
            print("Room size must be an integer or an array of three integers.")

    def id(self, word: str) -> bool:
        return False

    def expand_alias(self, word: str) -> str:
        if not self.aliases or not len(self.aliases):
            return word
        i = self.aliases.index(word) if word in self.aliases else -1
        if i == -1:
            return word
        return self.aliases[i - 1] if i % 2 else word

    def calc_short_exit_string(self) -> str:
        words = []
        for i in range(0, len(self.dest_other), 2):
            tmp = self.dest_other[i + 1][ROOM_OBV]
            if not tmp:
                continue
            add = False
            if isinstance(tmp, int) and tmp:
                add = True
            elif isinstance(tmp, str):
                add = getattr(self, tmp)(self.dest_other[i])
            elif isinstance(tmp, list):
                add = getattr(tmp[0], tmp[1])(self.dest_other[i])
            if add:
                short_form = SHORTEN.get(self.dest_other[i])
                if short_form:
                    words.append(f"$r$-{short_form}$r$" if self.dest_other[i + 1][ROOM_REL] else short_form)
                else:
                    if self.dest_other[i + 1][ROOM_REL]:
                        words.append(f"$r$-{self.dest_other[i]}$r$")
                    else:
                        pos = self.dest_other[i].find(" ")
                        if pos != -1:
                            tmp_dir = self.dest_other[i][pos + 1:]
                            tmp = SHORTEN.get(tmp_dir, tmp_dir)
                            words.append(f"{self.dest_other[i][:pos]}{tmp}")
                        else:
                            words.append(self.dest_other[i])
        return " [none]" if not words else f" [{', '.join(words)}]"

    def query_short_exit_string(self) -> str:
        if self.short_exit:
            return f"\033[32m{self.short_exit}\033[0m"
        tmp = self.calc_short_exit_string()
        if not self.attrs.get("no exit cache"):
            self.short_exit = tmp
        return f"\033[32m{tmp}\033[0m"

    def enchant_string(self) -> str:
        words = self.attrs.get("octarine_mess")
        if words:
            return words + "\n"
        enchant = self.query_enchant()
        if 0 <= enchant <= 49:
            return ""
        elif 50 <= enchant <= 149:
            return "A subtle hum of the Ethereal Veil brushes this place.\n"
        elif 150 <= enchant <= 299:
            return "Faint tendrils of Netherese sorcery coil through the air.\n"
        elif 300 <= enchant <= 499:
            return "The Ethereal Veil pulses, alive with arcane whispers.\n"
        elif 500 <= enchant <= 749:
            return "A surge of ancient power crackles, echoing lost Netheril.\n"
        elif 750 <= enchant <= 1000:
            return "The Veil bends, shimmering with forbidden magic.\n"
        elif 1001 <= enchant <= 1500:
            return "Ethereal runes flare, hinting at secrets of the Mythal.\n"
        else:
            return "Raw arcane torrents roar, threatening to tear reality asunder!\n"

    async def long(self, word: str = "", dark: int = 0) -> str:
        if not self.long_exit:
            self.calc_long_exit()
        ret = ""
        if dark:
            if dark < 0:
                ret = f"{self.query_dark_mess()}\n"
            else:
                ret = f"{self.query_bright_mess()}\n"
            if self.attrs.get("location") == "outside":
                ret += f"{self.weather_handler.query_weather(self.oid)}\n"
            if dark in [1, -1]:
                ret = f"$C${self.a_short()}.  {ret}\033[32m{self.long_exit}\033[0m\n"
                if self.query_contents("") != "":
                    ret += "Shadows conceal objects in the gloom.\n"
        else:
            ret = "$long$" if self.attrs.get("location") == "outside" else self.query_long()
            if not ret:
                ret = "Ancient arcane currents have faded here—report this to a sage of Candlekeep.\n"
            extra = self.calc_extra_look()
            if extra:
                ret += extra
            if driver.this_player() and driver.this_player().attrs.get("see_ether", False):  # Updated from see_octarine
                ret += self.enchant_string()
            if self.attrs.get("location") == "outside":
                ret += f"{self.weather_handler.query_weather(self.oid)}\n"
                if driver.this_player() and driver.this_player().attrs.get("terrain_map_in_look", 0):
                    ret += f"\n{driver.map_handler.query_player_map_template(self.co_ord[0], self.co_ord[1], self.co_ord[2], self.query_light(), 5)}\n"
            ret += f"\033[32m{self.long_exit}\033[0m\n{self.query_contents('')}"
            if self.rooftop:
                ret += "A jagged rooftop pierces the sky, whispering of Netherese ambition.\n"
            if self.tent_owner:
                ret += f"A tent of woven shadowsilk, pitched by {self.tent_owner}, stands resilient for {self.tent_decay} days.\n"
        if self.attrs.get("no exit cache"):
            self.long_exit = None
        return ret

    def pretty_short(self, thing: MudObject = None) -> str:
        dark = thing.check_dark(self.query_light()) if thing else 0
        return self.short(dark)

    def query_visibility(self) -> int:
        return 100

    def can_use_for_co_ords(self, other: str) -> bool:
        return True

    def calc_co_ord(self):
        if self.co_ord:
            return
        std_orders = STD_ORDERS
        for i in range(0, len(self.dest_other), 2):
            other = self.dest_other[i + 1][ROOM_DEST]
            if not driver.find_object(other):
                continue
            other_obj = driver.objects.get(other)
            if not other_obj or other_obj.attrs.get("do_not_use_coords", False):
                continue
            if other.startswith("/w/"):
                continue
            other_co_ord = other_obj.query_co_ord()
            if not other_co_ord or (other_co_ord[0] == 0 and other_co_ord[1] == 0 and other_co_ord[2] == 0):
                continue
            if not self.can_use_for_co_ords(other):
                continue
            j = -1
            delta = self.dest_other[i + 1][ROOM_DELTA]
            if delta:
                self.co_ord = other_co_ord.copy()
                if isinstance(delta, list):
                    for k in range(3):
                        self.co_ord[k] -= delta[k]
                    continue
                else:
                    j = std_orders.index(delta)
            if j == -1:
                j = std_orders.index(self.dest_other[i]) if self.dest_other[i] in std_orders else -1
                if j == -1:
                    continue
            self.co_ord = other_co_ord.copy()
            delta = self.query_room_size_array() + other_obj.query_room_size_array()
            for k in range(3):
                self.co_ord[k] += std_orders[j + 1][k] * (delta[k] + delta[k + 3])
            if j < 16 and self.dest_other[i + 1][ROOM_GRADE]:
                shift = (delta[0] + delta[3]) if j in [0, 1] else (delta[1] + delta[4]) if j in [2, 3] else (delta[0] + delta[1] + delta[3] + delta[4])
                self.co_ord[2] -= (self.dest_other[i + 1][ROOM_GRADE] * shift) // 100
            self.co_ord_calculated = True

    def calc_exits(self):
        self._exits = []
        for i in range(0, len(self.dest_other), 2):
            exit = self.dest_other[i]
            if exit not in self._exits:
                self._exits.append(exit)
                word = SHORTEN.get(exit)
                if word:
                    self._exits.append(word)
            tmp_al = self.aliases.copy()
            j = tmp_al.index(exit) if exit in tmp_al else -1
            while j != -1:
                if j % 2:
                    j -= 1
                else:
                    word = tmp_al[j + 1]
                    if word not in self._exits:
                        self._exits.append(word)
                tmp_al = tmp_al[:j] + tmp_al[j + 2:]
                j = tmp_al.index(exit) if exit in tmp_al else -1

    async def init(self):
        player = driver.this_player()
        if player and player.attrs.get("interactive", False):
            if (not self.last_visited and driver.uptime() > 1800 + random.randint(0, 3600)) or (self.last_visited and (time.time() - self.last_visited > random.randint(0, 900) + 900)):
                xp = random.randint(0, random.randint(0, 50)) if self.attrs.get("clone", False) else random.randint(0, random.randint(0, 500))
                player.adjust_xp(xp, 0)
            self.last_visited = time.time()

        if self.is_day != -1:
            new_day = self.weather_handler.query_day() > 0
            if new_day != self.is_day:
                self.is_day = new_day
                if self.variablelongs and self.variablelongs[self.is_day]:
                    self.set_long(self.variablelongs[self.is_day])
                if self.variableitems:
                    for i in range(0, len(self.variableitems[1 - self.is_day]), 2):
                        self.remove_item(self.variableitems[1 - self.is_day][i])
                    for i in range(0, len(self.variableitems[self.is_day]), 2):
                        self.add_item(self.variableitems[self.is_day][i], self.variableitems[self.is_day][i + 1])
                self.setup_room_chat()

        if self.chatter:
            self.chatter.check_chat()

        if self.sitchanger:
            self.sitchanger.check_situations()

        if not self._exits:
            self.calc_exits()

        if not self.co_ord:
            self.calc_co_ord()

        self.hidden_objects = [ob for ob in self.hidden_objects if ob]
        for ob in self.hidden_objects:
            ob.init()

        if player and player.attrs.get("player", False):
            for ob in self._use_internal_objects:
                if ob:
                    for inv in ob.find_inv_match("all", player):
                        inv.init()

        if self.item:
            self.item.init()

        if self.tent_owner and time.time() - self.last_visited > 86400:
            self.tent_decay -= 1
            if self.tent_decay <= 0:
                self.tent_owner = None
                self.set_keep_room_loaded(0)
                await self.tell_room(f"The shadowsilk tent collapses into ethereal dust.\n")

    async def tell_room(self, message: str):
        """Broadcasts message to all players in the room."""
        for obj in self.inventory:
            if obj.attrs.get("player", False):
                await obj.send(message)

    def query_zones(self) -> List[str]:
        zones = self.attrs.get("room zone", [])
        return zones if zones else ["nowhere"]

    def add_zone(self, zone: str):
        zones = self.attrs.get("room zone", [])
        zones.append(zone)
        self.attrs["room zone"] = zones

    def remove_zone(self, zone: str):
        zones = self.attrs.get("room zone", [])
        if zone in zones:
            zones.remove(zone)
        self.attrs["room zone"] = zones

    def set_zone(self, zone: str):
        self.add_zone(zone)

    def query_exit(self, direc: str) -> bool:
        return direc in self.dest_other

    def add_exit(self, direc: str, dest: Union[str, MudObject], type: str) -> bool:
        if direc in self.dest_other:
            return False
        if isinstance(dest, MudObject):
            dest = dest.oid
        if not dest.startswith("/"):
            dest = f"/{dest}"
        stuff = [dest] + driver.room_handler.query_exit_type(type, direc) if hasattr(driver, "room_handler") else [dest, None, None, 1, False, None, 0, 0, None, None, None, None]
        self.dest_other.extend([direc, stuff])
        door_stuff = driver.room_handler.query_door_type(type, direc, dest) if hasattr(driver, "room_handler") else None
        if door_stuff:
            door = Door(f"door_{direc}", "door")
            door.setup_door(direc, self, dest, door_stuff, type)
            self.door_control[direc] = door
            self.hidden_objects.append(door)
            key = f"{dest} {door.attrs.get('door_name', '')}" if door.attrs.get("door_name") else dest
            self.door_control[key] = direc
        driver.call_out(self.calc_exits, 1)
        self.long_exit = None
        self.short_exit = None
        return True

    def modify_exit(self, direc: Union[str, List[str]], data: List):
        if isinstance(direc, list):
            for d in direc:
                self.modify_exit(d, data)
            return 0
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        if i == -1:
            return 0
        for j in range(0, len(data), 2):
            key = data[j].lower()
            if key in ["message", "exit mess", "exit_mess"]:
                self.dest_other[i + 1][ROOM_EXIT] = data[j + 1]
            elif key == "move mess":
                self.dest_other[i + 1][ROOM_MESS] = data[j + 1]
            elif key == "linker mess":
                self.dest_other[i + 1][ROOM_LINK_MESS] = data[j + 1]
            elif key == "obvious":
                self.dest_other[i + 1][ROOM_OBV] = data[j + 1]
                if not isinstance(data[j + 1], int):
                    self.attrs["no exit cache"] = 1
                self.long_exit = None
                self.short_exit = None
            elif key == "function":
                self.dest_other[i + 1][ROOM_FUNC] = data[j + 1]
            elif key == "size":
                self.dest_other[i + 1][ROOM_SIZE] = data[j + 1]
            elif key == "upgrade":
                self.dest_other[i + 1][ROOM_GRADE] = data[j + 1]
        return 1

    def query_door_open(self, direc: str) -> int:
        door = self.door_control.get(direc)
        if not isinstance(door, Door):
            return -1
        return door.query_open()

    def query_relative(self, direc: str) -> bool:
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        return self.dest_other[i + 1][ROOM_REL] if i != -1 else False

    def query_look(self, direc: str) -> Optional[str]:
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        if i == -1 or not self.dest_other[i + 1]:
            return None
        return self.dest_other[i + 1][ROOM_LOOK]

    def query_look_func(self, direc: str) -> Optional[List]:
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        if i == -1 or not self.dest_other[i + 1]:
            return None
        return self.dest_other[i + 1][ROOM_LOOK_FUNC]

    def query_size(self, direc: str) -> int:
        i = self.dest_other.index(direc) if direc in self.dest_other else -1
        if i == -1:
            return 0
        size = self.dest_other[i + 1][ROOM_SIZE]
        if isinstance(size, str):
            return getattr(self, size)()
        elif isinstance(size, list):
            return getattr(size[0], size[1])()
        return size

    def event_magic(self, channel: MudObject, amount: int, caster: MudObject):
        self.add_enchant(amount // 5)
        self.magic_aura += amount // 10

    def event_theft(self, command_ob: MudObject, thief: MudObject, victim: MudObject, stolen: List[MudObject]):
        if thief.attrs.get("caster"):
            thief = driver.find_player(thief.attrs["caster"])
        elif thief.attrs.get("owner"):
            thief = thief.attrs["owner"]
        stolen_shorts = [s.short() for s in stolen]
        driver.log_file("THEFT", f"{time.ctime()[4:19]}: {thief.short()} stole {', '.join(stolen_shorts)} from {victim.short()} in {self.oid}\n")
        handler = self.theft_handler if self.theft_handler and self.theft_handler != "none" else "/obj/handlers/theft_handler"
        driver.call_handler(handler, "handle_theft", self, command_ob, thief, victim, stolen)

    def query_last_visited(self) -> int:
        return self.last_visited

    def add_item(self, shorts: Union[str, List[str]], desc: Union[str, List, Callable], no_plural: bool = False) -> bool:
        if not desc:
            print(f"Error! In {self.oid} add_item({shorts}, 0), not added.")
            return False
        if not self.item:
            self.item = MudObject(f"item_{self.oid}", "item")
        self.item.setup_item(shorts, desc, no_plural)
        return True

    def remove_item(self, word: str) -> bool:
        if not self.item:
            return True
        return self.item.remove_item(word)

    def modify_item(self, word: str, new_desc: Union[str, List]) -> bool:
        if not self.item:
            return False
        return self.item.modify_item(word, new_desc)

    def set_linker(self, rooms: List[str], d_prep: str = "into", s_prep: str = "in", r_name: str = "") -> bool:
        if self.linker:
            return False
        self.linker = MudObject(f"linker_{self.oid}", "linker")
        self.linker.setup_shadow(self, rooms, d_prep, s_prep, r_name)
        return True

    def set_terrain(self, terrain_name: str) -> bool:
        if self.terrain:
            return False
        self.terrain = MudObject(f"terrain_{self.oid}", "terrain")
        self.terrain.setup_shadow(self, terrain_name)
        self.set_not_replaceable(True)
        return True

    def set_wall(self, args: List):
        if not self.wall:
            self.wall = MudObject(f"wall_{self.oid}", "wall")
            self.wall.setup_shadow(self)
        self.wall.set_wall(args)

    def set_rooftop(self):
        if not self.rooftop:
            self.rooftop = driver.clone_object("/systems/rooftop")
            self.rooftop.setup_shadow(self)

    def add_tent(self, owner: str, duration: int = 7) -> bool:
        if self.tent_owner:
            return False
        self.tent_owner = owner
        self.tent_decay = duration
        self.set_keep_room_loaded(1)
        self.add_item("tent", f"A shadowsilk tent pitched by {owner}, woven with protective runes.", True)
        driver.call_out(self.check_tent, 86400)
        return True

    async def check_tent(self):
        if self.tent_owner and time.time() - self.last_visited > 86400:
            self.tent_decay -= 1
            if self.tent_decay <= 0:
                self.tent_owner = None
                self.set_keep_room_loaded(0)
                self.remove_item("tent")
                await self.tell_room(f"The shadowsilk tent collapses into ethereal dust.\n")

    def set_default_position(self, stuff: Union[str, List, Callable]):
        self.attrs["default_position"] = stuff

    def query_default_position(self) -> Union[str, List, Callable, None]:
        return self.attrs.get("default_position")

    def is_allowed_position(self, poss: str) -> bool:
        return poss in ["sitting", "standing", "kneeling", "lying", "meditating", "crouching"]

    def dest_me(self):
        if self.oid != ROOM_VOID:
            for thing in self.inventory:
                if thing.attrs.get("player", False):
                    thing.move_with_look(ROOM_VOID, "$N fall$s into the void.")
                else:
                    thing.dest_me()
        if self.chatter:
            self.chatter.dest_me()
        if self.sitchanger:
            self.sitchanger.dest_me()
        if self.linker:
            self.linker.destruct_shadow()
        if self.terrain:
            self.terrain.destruct_shadow()
        if self.wall:
            self.wall.destruct_shadow()
        if self.item:
            self.item.dest_me()
        for thing in self.door_control.values():
            if isinstance(thing, MudObject):
                thing.dest_me()
        for thing in self.hidden_objects:
            if thing and thing.multiple_hidden() == 0:
                thing.dest_me()
        self.destruct()

    def set_keep_room_loaded(self, flag: int):
        self.attrs["room_keep"] = flag

    def query_keep_room_loaded(self) -> bool:
        return self.attrs.get("room_keep", False)

    def clean_up(self, parent: int) -> bool:
        if parent:
            return False
        if self.query_keep_room_loaded():
            return False
        driver.call_out(self.real_clean, 30 + random.randint(0, 120))
        return True

    def real_clean(self) -> bool:
        for thing in self.inventory:
            if thing.attrs.get("transient", False):
                hospital = thing.attrs.get("hospital")
                thing.move(hospital if hospital else "/room/rubbish", "$N wander$s in.", "$N wander$s out.")
            if (thing.attrs.get("player", False) or
                (thing.attrs.get("unique", False) and self.last_visited > time.time() - 3600) or
                thing.attrs.get("slave", False) or
                thing.name == "corpse"):
                return False
        self.dest_me()
        return True

    def filter_inventory(self, item: MudObject, looker: MudObject) -> bool:
        return item and item.short(0) and (not looker or item.query_visible(looker))

    def find_inv_match(self, words: str, looker: MudObject) -> List[MudObject]:
        things = self.inventory.copy()
        if self.hidden_objects:
            things.extend(self.hidden_objects)
        if looker and looker.attrs.get("player", False):
            things = [t for t in things if self.filter_inventory(t, looker)]
        if self.item:
            things.append(self.item)
        return things

    def add_sign(self, sign_long: str, sign_read_mess: Union[str, List] = None, sign_short: str = None,
                 sign_name: Union[str, List[str]] = None, sign_language: str = "common") -> MudObject:
        sign = MudObject(f"sign_{self.oid}", "sign")
        sign_name = sign_name or "sign"
        if isinstance(sign_name, list):
            bits = sign_name[0].split()
            sign.set_name(bits[-1])
            sign.add_adjective(bits[:-1])
            sign.add_alias([s.split()[-1] for s in sign_name[1:]])
            sign.add_plural([self.pluralize(s.split()[-1]) for s in sign_name[1:]])
            sign.add_adjective([s.split()[:-1] for s in sign_name[1:]])
        else:
            bits = sign_name.split()
            sign.set_name(bits[-1])
            sign.add_adjective(bits[:-1])
        sign.set_long(sign_long)
        sign.set_read_mess(sign_read_mess, sign_language)
        sign.reset_get()
        if sign_short and sign_short != "":
            sign.set_short(sign_short)
            sign.set_main_plural(self.pluralize(sign_short))
            sign.move(self)
            sign.attrs["there"] = "here"
        else:
            self.hidden_objects.append(sign)
            adj = sign.query_adjectives()
            sign.set_short(f"{' '.join(adj)} {sign.name}" if adj else sign.name)
        return sign

    def tell_door(self, direc: str, message: str, thing: MudObject):
        door = self.door_control.get(direc)
        if isinstance(door, Door):
            door.tell_door(message, thing)

    def call_door(self, direc: str, func: str, *args) -> Optional[Union[int, str]]:
        door = self.door_control.get(direc)
        if isinstance(door, Door):
            return getattr(door, func)(*args)
        return None

    def query_door(self, dest: Union[str, MudObject], name: str = None) -> Optional[str]:
        if isinstance(dest, MudObject):
            dest = dest.oid
        if not isinstance(dest, str):
            return None
        key = f"{dest} {name}" if name else dest
        bing = self.door_control.get(key)
        direc = bing if isinstance(bing, str) else None
        if not direc:
            return None
        door = self.door_control.get(direc)
        if isinstance(door, Door):
            return direc
        door = Door(f"door_{direc}", "door")
        i = self.dest_other.index(direc)
        door.setup_door(direc, self, dest, self.dest_other[i + 1])
        self.hidden_objects.append(door)
        self.door_control[direc] = door
        return direc

    def stop_room_chats(self):
        if self.chatter:
            self.chatter.dest_me()

    def set_chat_min_max(self, min: int, max: int):
        if self.chatter:
            self.chatter.set_chat_min_max(min, max)

    def add_room_chats(self, new_chats: List[str]):
        if self.chatter:
            self.chatter.add_room_chats(new_chats)

    def remove_room_chats(self, dead_chats: List[str]):
        if self.chatter:
            self.chatter.remove_room_chats(dead_chats)

    def query_room_chats(self) -> Optional[List]:
        return self.chatter.query_room_chats() if self.chatter else None

    def setup_room_chat(self):
        if not self.chatter:
            self.chatter = MudObject(f"chatter_{self.oid}", "chatter")
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        chats = (self.variablechats[self.is_day] if self.is_day else self.variablechats[ROOM_NIGHT_INDEX]) if self.variablechats else None
        if not chats:
            chats = self.variablechats[ROOM_DEFAULT_INDEX] if self.variablechats else None
        elif self.variablechats and self.variablechats[ROOM_DEFAULT_INDEX]:
            chats[2].extend(self.variablechats[ROOM_DEFAULT_INDEX][2])
        if chats and driver.this_player() and driver.this_player().attrs.get("chat_output", True):
            self.chatter.setup_chatter(self, chats)

    def room_chat(self, args: List, chatobj: MudObject = None):
        if not args or not isinstance(args[2], list):
            print("Error: second argument of room_chat args is not an array.")
            return
        if not self.chatter and chatobj:
            self.chatter = chatobj
        if not self.variablechats:
            self.variablechats = [None] * 3
        self.variablechats[ROOM_DEFAULT_INDEX] = args
        self.setup_room_chat()

    def set_situation_changer(self, changer: Union[str, SituationChanger] = None) -> SituationChanger:
        if isinstance(changer, str):
            self.sitchanger = SituationChanger(f"sitchanger_{self.oid}", changer)
        elif isinstance(changer, SituationChanger):
            self.sitchanger = changer
        else:
            self.sitchanger = SituationChanger(f"sitchanger_{self.oid}", "situation_changer")
        return self.sitchanger.set_room(self)

    def add_situation(self, label: Union[str, int], sit: dict):
        if not self.sitchanger:
            self.sitchanger = SituationChanger(f"sitchanger_{self.oid}", "situation_changer")
            self.sitchanger.set_room(self)
        self.sitchanger.add_situation(label, sit)

    def make_situation_seed(self, xval: int, yval: int):
        if self.sitchanger:
            self.sitchanger.set_seed(xval, yval)

    def start_situation(self, label: int, do_start_mess: int):
        if self.sitchanger:
            asyncio.create_task(self.sitchanger.start_situation(label, do_start_mess))

    def end_situation(self, label: Union[str, int]):
        if self.sitchanger:
            self.sitchanger.end_situation(label)

    def change_situation(self, label: Union[str, int, List], duration: Union[int, List], words: Union[int, List] = None) -> Optional[int]:
        if self.sitchanger:
            return self.sitchanger.change_situation(label, duration, words, 0)
        return 0

    def automate_situation(self, label: Union[str, int, List], duration: Union[int, List], when: int = WHEN_ANY_TIME,
                           chance: int = 1000, category: str = None):
        if self.sitchanger:
            self.sitchanger.automate_situation(label, duration, when, chance, category)

    def shutdown_all_situations(self):
        if self.sitchanger:
            self.sitchanger.shutdown_all_situations()

    def shutdown_situation(self, call: int, label: Union[str, int, List]):
        if self.sitchanger:
            self.sitchanger.shutdown_situation(call, label)

    def query_not_replaceable(self) -> bool:
        return self.attrs.get("not_replaceable", False)

    def set_not_replaceable(self, replace: bool):
        self.attrs["not_replaceable"] = replace

    def stats(self) -> List[Tuple[str, Union[int, str]]]:
        stuff = []
        for i in range(0, len(self.dest_other), 2):
            stuff.append((self.dest_other[i], self.dest_other[i + 1][ROOM_DEST]))
        if self.co_ord:
            stuff.extend([("co-ord x", self.co_ord[0]), ("co-ord y", self.co_ord[1]), ("co-ord z", self.co_ord[2])])
        return (light.Light.stats(self) + property.Property.stats(self) + effects.Effects.stats(self) + stuff +
                [("short", self.short(0)), ("enchantment", self.query_enchant()),
                 ("background enchantment", self.background_enchant),
                 ("dynamic enchantment", self.dynamic_enchant),
                 ("enchantment time", self.enchant_time),
                 ("theft handler", self.theft_handler),
                 ("magic aura", self.magic_aura)])

    def set_day_long(self, str: str):
        if not self.variablelongs:
            self.variablelongs = [""] * 2
        self.variablelongs[ROOM_DAY_INDEX] = str
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_DAY_INDEX:
            self.set_long(str)

    def query_day_long(self) -> str:
        if self.variablelongs and self.variablelongs[ROOM_DAY_INDEX]:
            return self.variablelongs[ROOM_DAY_INDEX]
        return self.query_long()

    def set_night_long(self, str: str):
        if not self.variablelongs:
            self.variablelongs = [""] * 2
        self.variablelongs[ROOM_NIGHT_INDEX] = str
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_NIGHT_INDEX:
            self.set_long(str)

    def query_night_long(self) -> str:
        if self.variablelongs and self.variablelongs[ROOM_NIGHT_INDEX]:
            return self.variablelongs[ROOM_NIGHT_INDEX]
        return self.query_long()

    def return_long(self, desc: Union[str, List]) -> str:
        if not isinstance(desc, list):
            return desc
        ma = desc.index("long") if "long" in desc else -1
        return desc[ma + 1] if ma >= 0 else "Error: No long found."

    def add_day_item(self, shorts: Union[str, List[str]], desc: Union[str, List], no_plural: bool = False) -> bool:
        the_item = shorts[0] if isinstance(shorts, list) else shorts
        if not self.variableitems:
            self.variableitems = [[], []]
        self.variableitems[ROOM_DAY_INDEX].extend([the_item, self.return_long(desc)])
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_DAY_INDEX:
            return self.add_item(shorts, desc, no_plural)
        return True

    def add_night_item(self, shorts: Union[str, List[str]], desc: Union[str, List], no_plural: bool = False) -> bool:
        the_item = shorts[0] if isinstance(shorts, list) else shorts
        if not self.variableitems:
            self.variableitems = [[], []]
        self.variableitems[ROOM_NIGHT_INDEX].extend([the_item, self.return_long(desc)])
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_NIGHT_INDEX:
            return self.add_item(shorts, desc, no_plural)
        return True

    def room_day_chat(self, args: List):
        if not self.variablechats:
            self.variablechats = [None] * 3
        self.variablechats[ROOM_DAY_INDEX] = args
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_DAY_INDEX:
            self.setup_room_chat()

    def room_night_chat(self, args: List):
        if not self.variablechats:
            self.variablechats = [None] * 3
        self.variablechats[ROOM_NIGHT_INDEX] = args
        if self.is_day == -1:
            self.is_day = self.weather_handler.query_day() > 0
        if self.is_day == ROOM_NIGHT_INDEX:
            self.setup_room_chat()

    def query_help_file_directory(self) -> str:
        return "/doc/room_help"

    def query_room_night_chats(self) -> List:
        return self.variablechats[ROOM_NIGHT_INDEX] if self.variablechats else []

    def query_room_day_chats(self) -> List:
        return self.variablechats[ROOM_DAY_INDEX] if self.variablechats else []

    def query_room_default_chats(self) -> List:
        return self.variablechats[ROOM_DEFAULT_INDEX] if self.variablechats else []

    def query_day_items(self) -> List:
        return self.variableitems[ROOM_DAY_INDEX] if self.variableitems else []

    def query_night_items(self) -> List:
        return self.variableitems[ROOM_NIGHT_INDEX] if self.variableitems else []

    async def move(self, dest: str | MudObject, messin: str = "", messout: str = "") -> int:
        if isinstance(dest, str):
            dest = driver.load_object(dest)
        if not dest:
            return -1  # MOVE_INVALID_DEST
        return await driver.move_object(self, dest, messin, messout)

async def init(driver_instance):
    global driver
    driver = driver_instance
    room = Room("room_void", "The Void")
    driver.add_object(room)