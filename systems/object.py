# /mnt/home2/mud/systems/object.py
# Imported to: driver.py, player.py, room.py, living.py
# Imports from: driver.py, extra_look.py, property.py, effects.py, id.py, misc.py, auto_load.py, help_files.py, theft_callback.py

from typing import List, Optional, Dict, Tuple
from ..driver import driver, MudObject
import asyncio
import time
from .extra_look import ExtraLookMixin
from .property import PropertyMixin
from .effects import EffectsMixin
from .id import IdHandler
from .misc import MiscHandler
from .auto_load import AutoLoadHandler
from .help_files import HelpFilesHandler
from .theft_callback import TheftCallbackHandler

ENCHANT_DEGRADE_TIME = 8 * 7 * 24 * 60 * 60  # 8 weeks in seconds

class Object(MudObject, ExtraLookMixin, PropertyMixin, EffectsMixin):
    def __init__(self, oid: str = "object", name: str = "object"):
        super().__init__(oid, name)
        self.id_handler = IdHandler()
        self.misc_handler = MiscHandler()
        self.auto_load_handler = AutoLoadHandler()
        self.help_handler = HelpFilesHandler()
        self.theft_handler = TheftCallbackHandler()
        self.help_handler.set_object(self)
        self.theft_handler.obj = self  # Direct reference for event_theft
        self.cmr_handler = driver.cmr_handler  # Assumes driver has cmr_handler
        self.materials: List[str] = []
        self.colour = ""
        self.player = None
        self.short_d = name
        self.long_d = ""
        self.plural_d = ""
        self._enchanted = 0
        self._set_enchant_time = 0
        self._degrade_enchant = 0
        self._read_mess: List[Tuple[str, str, str, int]] = []
        self._max_size = 100
        self._cur_size = 0
        self.setup()

    def setup(self):
        if not self.do_setup:
            self.do_setup = True
            self.add_property("determinate", "")

    def set_name(self, name: str):
        if self.name != "object":
            super().set_name(name)
            return
        super().set_name(name)
        if not self.short_d:
            self.short_d = name
        self.add_plural(self.pluralize(name))

    def long(self, word: Optional[str] = None, dark: int = 0) -> str:
        base = self.long_d or f"This is {self.short(0)}."
        extra = self.calc_extra_look()
        details = self.query_long_details(word, dark)
        return self.replace_long_dollars(base + extra + details)

    def query_long_details(self, word: str, dark: int) -> str:
        stuff = ""
        player = driver.this_player()
        if player and player.attrs.get("see_ether", False):  # Updated from see_octarine
            stuff += self.enchant_string()
        if self._read_mess or self.query_property("paper"):
            stuff += "It appears to have something written on it.\n"
        return stuff

    def replace_long_dollars(self, text: str) -> str:
        player = driver.this_player()
        if self.colour:
            text = text.replace("$colour$", self.cmr_handler.identify_colour(self.colour, player))
        if self.materials:
            text = text.replace("$material$", self.cmr_handler.identify_material(self.materials[0], player, False))
        return text

    def set_colour(self, colour: str):
        self.colour = colour

    def query_colour(self) -> str:
        return self.colour

    def set_material(self, material: str | List[str]):
        if not isinstance(material, list):
            material = [material]
        if material:
            self.materials = material + self.materials
            self.add_adjective(material)

    def add_material(self, material: str | List[str]):
        if isinstance(material, list):
            self.materials.extend([m for m in material if m not in self.materials])
        elif isinstance(material, str) and material not in self.materials:
            self.materials.append(material)
        self.add_adjective(material)

    def query_material(self) -> Optional[str]:
        return self.materials[0] if self.materials else None

    def query_materials(self) -> List[str]:
        return [m for m in self.materials if isinstance(m, str)]

    def query_pronoun(self) -> str:
        return "it"

    def query_possessive(self) -> str:
        return "its"

    def query_objective(self) -> str:
        return "it"

    def query_cloned_by(self) -> str:
        return self.create_me

    def set_quality(self, quality: int):
        self.add_property("quality", quality)

    def query_quality(self) -> int:
        return self.query_property("quality") or 0

    # Enchantment Methods (Updated with FR Theming)
    def query_max_enchant(self) -> int:
        return 5 + self.query_weight() // 4

    def query_degrade_enchant(self) -> int:
        return self._degrade_enchant or self.query_max_enchant() // 2

    def set_degrade_enchant(self, enchant: int):
        self._degrade_enchant = min(enchant, self.query_max_enchant())

    def enchant_string(self) -> str:
        tal_msg = ""
        ench_msg = ""
        if self.query_property("talisman"):
            tal_msg = self.query_property("talisman_mess") or "It hums with the Ethereal Veil’s blessing.\n"
        if custom_msg := self.query_property("ether_mess"):  # Updated from octarine_mess
            ench_msg = custom_msg + "\n"
        else:
            percent = (self.query_enchant() * 100) // self.query_max_enchant()
            ench_msg = {
                range(1, 11): "A faint ripple of Netherese power stirs within.\n",
                range(11, 21): "It pulses with a subtle ethereal glow.\n",
                range(21, 31): "A soft hum of the Veil emanates steadily.\n",
                range(31, 41): "It glows with a steady ethereal light.\n",
                range(41, 51): "The Veil’s essence shimmers vibrantly.\n",
                range(51, 61): "It radiates an intense ethereal sheen.\n",
                range(61, 71): "A bright surge of Netherese magic flares.\n",
                range(71, 81): "It pulses brilliantly with Veil-born power.\n",
                range(81, 91): "Ethereal brilliance dances across its form.\n",
                range(91, 101): "It blazes with pure Netherese might!\n",
            }.get(next((r for r in [range(1, 11), range(11, 21), range(21, 31), range(31, 41), range(41, 51),
                               range(51, 61), range(61, 71), range(71, 81), range(81, 91), range(91, 101)]
                       if percent in r), range(0, 1)), "")
        return ench_msg + tal_msg

    def set_enchant(self, number: int):
        self._enchanted = min(number, self.query_max_enchant())
        self._set_enchant_time = int(time.time())

    def add_enchant(self, number: int) -> int:
        self.set_enchant(self.query_enchant() + number)
        return self._enchanted

    def query_enchant(self) -> int:
        max_ench = self.query_max_enchant()
        degrade = self.query_degrade_enchant()
        if self._enchanted > max_ench:
            self._enchanted = max_ench
        if self._enchanted > degrade:
            if not self._set_enchant_time:
                self._set_enchant_time = int(time.time())
            if time.time() - self._set_enchant_time >= ENCHANT_DEGRADE_TIME:
                self._enchanted = degrade
            else:
                tmp = (self._enchanted - degrade) * 100 + 99
                tmp *= 100 - ((int(time.time() - self._set_enchant_time) * 100) // ENCHANT_DEGRADE_TIME)
                return degrade + (tmp // 10000)
        return self._enchanted

    def query_real_enchant(self) -> int:
        return self._enchanted

    def query_enchant_set_time(self) -> int:
        return self._set_enchant_time

    def set_enchant_set_time(self, tim: int):
        self._set_enchant_time = tim

    # Readable Message Methods (Updated with NROFF)
    def set_max_size(self, siz: int):
        self._max_size = siz

    def query_max_size(self) -> int:
        return self._max_size

    def set_cur_size(self, siz: int):
        self._cur_size = siz

    def query_cur_size(self) -> int:
        return self._cur_size

    def set_read_mess(self, mess: List[Tuple[str, str, str, int]] | str, lang: Optional[str] = None, size: Optional[int] = None):
        if isinstance(mess, list):
            self._read_mess = mess
        elif lang:
            size = size or 1
            self._read_mess = [(mess, "", lang, size)] if mess else []

    def query_read_mess(self) -> List[Tuple[str, str, str, int]]:
        if self.query_property("paper") and self.query_property("file_name"):
            fname = self.query_property("file_name")
            nroff_fn = f"{fname}_nroff"
            str_ = driver.nroff_handler.cat_file(nroff_fn, True)
            if not str_:
                driver.nroff_handler.create_nroff(fname, nroff_fn)
                str_ = driver.nroff_handler.cat_file(nroff_fn, False)
            lang = self.query_property("language") or "common"
            return [(str_ or "Unable to render NROFF file.", "", lang, 0)] if str_ else self._read_mess
        return self._read_mess.copy()

    async def add_read_mess(self, str: str, type_: str = "", lang: str = "common", size: int = 1) -> str:
        if self._cur_size >= self._max_size:
            return ""
        de_size = size * len(str)
        if self._cur_size + de_size > self._max_size:
            str = str[:int((self._max_size - self._cur_size) / size)]
            if not str:
                return ""
            de_size = size * len(str)
        self._read_mess.append((str, type_, lang, size))
        self._cur_size += de_size
        return str

    def remove_read_mess(self, str_: str = "", type_: str = "", lang: str = "") -> bool:
        for i, (text, t, l, s) in enumerate(self._read_mess):
            if (not str_ or text == str_) and (not type_ or t == type_) and (not lang or l == lang):
                self._cur_size -= s * len(text)
                self._read_mess.pop(i)
                return True
        return False

    def query_readable_message(self, player: Optional["MudObject"] = None, ignore_labels: bool = False) -> str:
        if not self._read_mess and not self.query_property("paper"):
            return ""
        player = player or driver.this_player()
        message = ""
        for text, type_, lang, _ in self.query_read_mess():
            mess = text
            if lang != "common" or type_:
                mess = f"Written{' in ' + type_ if type_ else ''}{' in ' + lang.capitalize() if lang != 'common' else ''}: {mess}\n"
            else:
                mess += "\n"
            message += mess
        return message

    def query_read_short(self, player: Optional["MudObject"] = None, ignore_labels: bool = False) -> str:
        if not self._read_mess and not self.query_property("paper"):
            return ""
        return self.query_property("read id") or "$name$"

    # Help and Theft Methods
    def query_help_file_directory(self) -> str:
        return "/doc/object/"

    def add_help_file(self, help_file: str):
        self.help_handler.add_help_file(help_file)

    def remove_help_file(self, help_file: str):
        self.help_handler.remove_help_file(help_file)

    def query_help_files(self) -> List[str]:
        return self.help_handler.query_help_files()

    def help_string(self) -> Optional[str]:
        return self.help_handler.help_string()

    async def event_theft(self, command_ob: MudObject, thief: MudObject, victim: MudObject, stolen: List[MudObject]):
        await self.theft_handler.event_theft(command_ob, thief, victim, stolen)

    def add_theft_callback(self, func_name: str, path: str) -> int:
        return self.theft_handler.add_theft_callback(func_name, path)

    def remove_theft_callback(self, id_: int) -> int:
        return self.theft_handler.remove_theft_callback(id_)

    def query_theft_callbacks(self) -> str:
        return self.theft_handler.query_theft_callbacks()

    # Auto-load Methods
    def stats(self) -> List[Tuple[str, str | int]]:
        return [
            ("name", self.name),
            ("short", self.short(0)),
            ("plural", self.plural_d),
            ("weight", self.weight),
            ("enchantment", self.query_enchant()),
            ("colour", self.colour),
            ("material", ", ".join(self.materials) if self.materials else "none"),
            ("cloned by", self.create_me),
            ("length", self.length),
            ("width", self.width),
        ] + super().stats()

    def query_static_auto_load(self) -> Dict:
        if self.name == "object":
            return {}
        map_ = {
            "name": self.name,
            "short": self.short_d,
            "main plural": self.plural_d,
            "long": self.long_d,
            "alias": self.query_alias(),
            "adjective": self.query_adjectives(),
            "plural": self.query_plurals(),
            "value": self.value,
            "weight": self.weight,
            "colour": self.colour,
            "length": self.length,
            "width": self.width,
            "help files": self.query_help_files(),
        }
        return self.auto_load_handler.add_auto_load_value(map_, self.auto_load_handler.AUTO_LOAD_TAG, "materials", self.materials)

    def query_dynamic_auto_load(self) -> Dict:
        if self.name == "object":
            return {}
        map_ = {
            "read mess": self._read_mess,
            "degrade enchantment": self._degrade_enchant,
            "enchantment": self._enchanted,
            "enchantment time": self._set_enchant_time,
            "light": self.query_my_light(),
            "materials": self.materials,
            "cloned by": self.create_me,
            "theft callbacks": self.theft_handler.callbacks,
        }
        if self.map_prop:
            map_["properties"] = self.map_prop.copy()
        if self.timed_properties:
            map_["timed properties"] = self.timed_properties.copy()
        if self.query_effs():
            self.effect_freeze()
            self.effects_saving()
            map_["effects"] = (self.query_effs(), self.query_eeq())
            self.effect_unfreeze()
        return map_

    def init_static_arg(self, map_: Dict):
        if not map_:
            return
        self.set_name(map_.get("name", "object"))
        self.short_d = map_.get("short", self.short_d)
        self.plural_d = map_.get("main plural", self.plural_d)
        self.long_d = map_.get("long", self.long_d)
        if "alias" in map_:
            self.set_aliases(map_["alias"])
        if "adjective" in map_:
            self.set_adjectives(map_["adjective"])
        if "plural" in map_:
            self.set_plurals(map_["plural"])
        self.value = map_.get("value", 0)
        self.weight = map_.get("weight", 0)
        self.colour = self.auto_load_handler.query_auto_load_value(map_, self.auto_load_handler.AUTO_LOAD_TAG, "colour") or ""
        self.materials = self.auto_load_handler.query_auto_load_value(map_, self.auto_load_handler.AUTO_LOAD_TAG, "materials") or []
        help_files = self.auto_load_handler.query_auto_load_value(map_, self.auto_load_handler.AUTO_LOAD_TAG, "help files")
        if help_files:
            for hf in help_files:
                self.add_help_file(hf)

    def init_dynamic_arg(self, map_: Dict):
        if not map_:
            return
        if "properties" in map_:
            self.map_prop = map_["properties"]
        if "timed properties" in map_:
            self.timed_properties = map_["timed properties"]
        if "read mess" in map_:
            self.set_read_mess(map_["read mess"])
        self._enchanted = map_.get("enchantment", 0)
        self._degrade_enchant = map_.get("degrade enchantment", 0)
        self._set_enchant_time = map_.get("enchantment time", 0)
        self.create_me = map_.get("cloned by", "unknown")
        if "effects" in map_:
            self.set_effs(map_["effects"][0])
            self.set_eeq(map_["effects"][1])
        callbacks = self.auto_load_handler.query_auto_load_value(map_, self.auto_load_handler.AUTO_LOAD_TAG, "theft callbacks")
        if callbacks:
            for func, path in callbacks:
                self.add_theft_callback(func, path)

    def set_player(self, player: Optional["MudObject"]):
        self.player = player

    async def dest_me(self):
        self.effects_desting()
        await super().dest_me()

async def init(driver_instance):
    global driver
    driver = driver_instance
    driver.add_object(Object())