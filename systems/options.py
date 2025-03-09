# /mnt/home2/mud/systems/options.py
from typing import Dict, Optional, List, Callable, Tuple, ClassVar
from ..driver import driver, Player, MudObject
from .tactics import TacticsHandler
import asyncio
import re

class option:
    def __init__(self, type_: mixed, restriction: int, set_func: Callable, query_func: Callable, suboptions: Dict, help: str):
        self.type = type_
        self.restriction = restriction
        self.set = set_func
        self.query = query_func
        self.suboptions = suboptions
        self.help = help

class player_options_control:
    def __init__(self):
        self.follow_everyone = 0
        self.follow_groups = 0
        self.follow_friends = 0
        self.lead_behind = 0
        self.mxp_disable = 0

# Option type constants (from /include/options.h)
OPTIONS_TYPE_BRIEF = 1
OPTIONS_TYPE_BOOLEAN = 2
OPTIONS_TYPE_INTEGER = 3
OPTIONS_TYPE_STRING = 4
OPTIONS_TYPE_PERCENTAGE = 5
OPTIONS_TYPE_COLOUR = 6
OPTIONS_TYPE_TERMINAL = 7
OPTIONS_TYPE_DYNAMIC_GROUP = 8
OPTIONS_TYPE_GROUP = 9
OPTIONS_TYPE_ALL = 0
OPTIONS_TYPE_CRE_ONLY = 1
OPTIONS_TYPE_LORD_ONLY = 2
OPTIONS_TYPE_PLAYTESTER_ONLY = 3
MONITOR_OPTIONS = ["off", "on", "slow"]

class OptionsHandler:
    _options: Dict[str, Dict] = {}
    _colours: List[str] = ["BOLD", "FLASH", "BLACK", "RED", "BLUE", "CYAN", "MAGENTA", "ORANGE", "YELLOW", "GREEN", "WHITE", "B_RED", "B_ORANGE", "B_YELLOW", "B_BLACK", "B_CYAN", "B_WHITE", "B_GREEN", "B_MAGENTA"]
    _cache_input: Dict[str, Dict] = {}
    tactics_handler = TacticsHandler()

    def __init__(self):
        pass  # Initialization handled in create()

    async def init(self, driver_instance):
        self.driver = driver_instance
        self.create()
        for obj in self.driver.objects.values():
            if isinstance(obj, Player) and hasattr(obj, "attrs"):
                self.init_options(obj)
                obj.add_action("options", self.options_command)

    def create(self):
        self._options = {}
        self._cache_input = {}

        # Output options
        self.add_option("output look", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_verbose(p, "look", v), lambda p: self.query_verbose(p, "look"),
                       "Display room descriptions briefly or in full")
        self.add_option("output combat", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_verbose(p, "combat", v), lambda p: self.query_verbose(p, "combat"),
                       "Display all combat messages or only those involving damage")
        self.add_option("output errors", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: self.set_verbose(p, "errors", v), lambda p: self.query_verbose(p, "errors"),
                       "Display errors in the error handler briefly")
        self.add_option("output score", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_verbose(p, "score", v), lambda p: self.query_verbose(p, "score"),
                       "Amount of detail to be displayed by the 'score' command")
        self.add_option("output accent", ["mangle", "unadulterated"], OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs["mangle_accent"] == (v == "mangle"), lambda p: p.attrs.get("mangle_accent", False) and "mangle" or "unadulterated",
                       "Show others speech with or without regional accents")
        self.add_option("output names", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_verbose(p, "names", v), lambda p: self.query_verbose(p, "names"),
                       "Display player names with or without title and surname")
        self.add_option("output htell", OPTIONS_TYPE_BRIEF, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_verbose(p, "htell", v), lambda p: self.query_verbose(p, "htell"),
                       "Cause the 'htell' command to display times for tells or not")
        self.add_option("output msgout", OPTIONS_TYPE_STRING, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: setattr(p.attrs, "msgout", v), lambda p: p.attrs.get("msgout", ""),
                       "The message that is displayed when you walk out of a room")
        self.add_option("output msgin", OPTIONS_TYPE_STRING, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: setattr(p.attrs, "msgin", v), lambda p: p.attrs.get("msgin", ""),
                       "The message that is displayed when you walk into a room")
        self.add_option("output mmsgout", OPTIONS_TYPE_STRING, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: setattr(p.attrs, "mmsgout", v), lambda p: p.attrs.get("mmsgout", ""),
                       "The message that is displayed when you trans out of a room")
        self.add_option("output mmsgin", OPTIONS_TYPE_STRING, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: setattr(p.attrs, "mmsgin", v), lambda p: p.attrs.get("mmsgin", ""),
                       "The message that is displayed when you trans into a room")
        self.add_option("output usercolour", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("allow_coloured_souls", v), lambda p: p.attrs.get("allow_coloured_souls", 0),
                       "Display user chosen colours in souls")
        self.add_option("output plainmaps", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("plain_maps", v), lambda p: p.attrs.get("plain_maps", 0),
                       "Display terrain maps without colour")
        self.add_option("output lookmap", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_PLAYTESTER_ONLY,
                       lambda p, v: p.attrs.setdefault("terrain_map_in_look", v), lambda p: p.attrs.get("terrain_map_in_look", 0),
                       "Display room a map in the terrain long or not")
        self.add_option("output tabstops", OPTIONS_TYPE_INTEGER, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: p.attrs.setdefault("tabstops", v), lambda p: p.attrs.get("tabstops", 0),
                       "Show tabstops as <TAB> or as spaces")
        self.add_option("output shorthand", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("shorthand_output", v), lambda p: p.attrs.get("shorthand_output", 0),
                       "Convert others shorthand text into long form")

        # Colour options
        for colour in ["tell", "say", "shout", "inform", "combat", "magic.spellcasting"]:  # Added magic.spellcasting
            self.add_option(f"colour {colour}", OPTIONS_TYPE_COLOUR, OPTIONS_TYPE_ALL,
                           lambda p, v, c=colour: self.set_my_colours(p, c, v), lambda p, c=colour: self.colour_event(p, c),
                           f"The colour for {colour} messages")
        self.add_option("colour inform", OPTIONS_TYPE_DYNAMIC_GROUP, OPTIONS_TYPE_ALL,
                       0, lambda p: self.get_inform_colours(p),
                       "The colours of various informational messages")
        self.add_option("colour club", OPTIONS_TYPE_DYNAMIC_GROUP, OPTIONS_TYPE_ALL,
                       0, lambda p: self.get_club_colours(p),
                       "The colour for club messages")

        # Terminal options
        self.add_option("terminal type", OPTIONS_TYPE_TERMINAL, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "term_type", v), lambda p: p.attrs.get("term_type", ""),
                       "The type of terminal you are using")
        self.add_option("terminal rows", OPTIONS_TYPE_INTEGER, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "rows", v), lambda p: p.attrs.get("rows", 0),
                       "The number of rows in your terminal")
        self.add_option("terminal cols", OPTIONS_TYPE_INTEGER, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "cols", v), lambda p: p.attrs.get("cols", 0),
                       "The number of columns in your terminal")

        # Combat options
        self.add_option("combat wimpy", OPTIONS_TYPE_INTEGER, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "wimpy", v), lambda p: p.attrs.get("wimpy", 20),
                       "The percentage of your hitpoints at which you will run away")
        self.add_option("combat monitor", MONITOR_OPTIONS, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "monitor", MONITOR_OPTIONS.index(v)), lambda p: MONITOR_OPTIONS[p.attrs.get("monitor", 1)],
                       "The frequency of display of your combat monitor")
        self.add_option("combat tactics attitude", ["insane", "offensive", "neutral", "defensive", "wimp"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_attitude(p, v), lambda p: self.tactics_handler.query_combat_attitude(p),
                       "Your combat attitude (see help tactics)")
        self.add_option("combat tactics response", ["dodge", "neutral", "parry"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_response(p, v), lambda p: self.tactics_handler.query_combat_response(p),
                       "Your combat response (see help tactics)")
        self.add_option("combat tactics parry", ["left", "right", "both"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_parry(p, v), lambda p: self.tactics_handler.query_combat_parry(p),
                       "Which hand you will parry with (see help tactics)")
        self.add_option("combat tactics unarmed_parry", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_unarmed_parry(p, v), lambda p: self.tactics_handler.query_unarmed_parry(p),
                       "Whether you will parry unarmed (see help tactics)")
        self.add_option("combat tactics attack", ["left", "right", "both"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_attack(p, v), lambda p: self.tactics_handler.query_combat_attack(p),
                       "Which hand you will attack with (see help tactics)")
        self.add_option("combat tactics mercy", ["always", "ask", "never"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_mercy(p, v), lambda p: self.tactics_handler.query_combat_mercy(p),
                       "Whether or not you will show mercy to opponents")
        self.add_option("combat tactics focus", ["upper body", "lower body", "head", "neck", "chest", "abdomen", "arms", "hands", "legs", "feet", "none"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_focus(p, v), lambda p: self.tactics_handler.query_combat_focus(p),
                       "Which body part you will focus on in combat (see help tactics)")
        self.add_option("combat tactics distance", ["long", "medium", "close", "hand-to-hand", "none"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.tactics_handler.set_combat_distance(p, v), lambda p: self.tactics_handler.query_combat_distance(p),
                       "Your ideal combat distance (see help tactics)")
        self.add_option("combat killer", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "player_killer", v), lambda p: p.attrs.get("player_killer", 0),
                       "Whether or not you are a registered player killer")

        # Input options
        self.add_option("input ambiguous", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.change_bool_property(p, "ambiguous", not v), lambda p: not p.attrs.get("ambiguous", 0),
                       "Should the parser notify you of ambiguities")
        self.add_option("input andascomma", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.change_bool_property(p, "andascomma", not v), lambda p: not p.attrs.get("andascomma", 0),
                       "Should 'and' be treated as a comma (an inclusive list)")
        self.add_option("input editor", ["menu", "magic", "command", "ed"], OPTIONS_TYPE_ALL,
                       lambda p, v: setattr(p.attrs, "editor", v), lambda p: p.attrs.get("editor", "menu"),
                       "Your preferred editor")
        self.add_option("input shorthand", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("shorthand", v), lambda p: p.attrs.get("shorthand", 0),
                       "Convert your shorthand typing into long form")

        # Earmuff options
        earmuff_events = ["shout", "newbie", "cryer", "remote-soul", "multiple-soul", "multiple-tell", "teach", "tell", "remote", "multiple-remote"]
        for event in earmuff_events:
            self.add_option(f"earmuff events {event}", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                           lambda p, v, e=event: self.change_earmuffs(p, e, v), lambda p, e=event: e in p.attrs.get("earmuffs", []),
                           f"Should you be informed of {event} messages")
        self.add_option("earmuff state", ["on", "off", "allowfriends"], OPTIONS_TYPE_ALL,
                       lambda p, v: self.setup_earmuffs(p, v), lambda p: "allowfriends" if p.attrs.get("earmuffs") == "allowfriends" else "on" if p.attrs.get("earmuffs") else "off",
                       "Enable or disable earmuffs always or just for friends")
        self.add_option("earmuff cut-through", ["off", "ask", "auto"], OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("cut_earmuffed_tells", ["off", "ask", "auto"].index(v)), lambda p: ["off", "ask", "auto"][p.attrs.get("cut_earmuffed_tells", 0)],
                       "Cut through a players tell earmuffs")

        # Creator options
        self.add_option("command ls use_nickname", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_CRE_ONLY,
                       lambda p, v: self.change_bool_property(p, "ls_nickname", v), lambda p: p.attrs.get("ls_nickname", 0),
                       "Should 'ls' check for nicknames")

        # Personal options
        self.add_option("personal description", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: len(v) <= 30 and setattr(p.attrs, "description", v if v != "none" else None) or 0, lambda p: p.attrs.get("description", "none"),
                       "Ain't you perdy")
        self.add_option("personal real_name", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: len(v) <= 30 and setattr(p.attrs, "real_name", v if v != "none" else None) or 0, lambda p: p.attrs.get("real_name", "none"),
                       "The real name displayed in your finger information")
        self.add_option("personal location", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: len(v) <= 30 and setattr(p.attrs, "location", v if v != "none" else None) or 0, lambda p: p.attrs.get("location", "none"),
                       "The location displayed in your finger information")
        self.add_option("personal home_page", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: len(v) <= 30 and setattr(p.attrs, "homepage", v if v != "none" else None) or 0, lambda p: p.attrs.get("homepage", "none"),
                       "The url displayed in your finger information")
        self.add_option("personal email", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: len(v) <= 30 and setattr(p.attrs, "email", v if v != "none" else None) or 0, lambda p: p.attrs.get("email", "none"),
                       "The email address displayed in your finger information")
        self.add_option("personal birthday", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: self.valid_birthday(v) and not p.attrs.get("birthday") and setattr(p.attrs, "birthday", self.convert_birthday(v) if v != "none" else None) or 0, lambda p: p.attrs.get("birthday", "none"),
                       "Your birthday")
        self.add_option("personal execinclude", OPTIONS_TYPE_STRING, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("execinclude", v if v != "none" else None), lambda p: p.attrs.get("execinclude", "none"),
                       "The path of files to be included in exec commands")
        self.add_option("personal auto teach", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("auto_teach", v), lambda p: p.attrs.get("auto_teach", 0),
                       "Are you available to auto-teach")
        self.add_option("personal travel", ["walk", "journey"], OPTIONS_TYPE_ALL,
                       lambda p, v: p.attrs.setdefault("travel", v == "journey"), lambda p: "journey" if p.attrs.get("travel", False) else "walk",
                       "By default should you walk or journey across terrains")

        # Playtester options
        self.add_option("playtester protection", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_PLAYTESTER_ONLY,
                       lambda p, v: p.attrs.setdefault("pt_protection", v), lambda p: p.attrs.get("pt_protection", 0),
                       "Enable or disable playtester protection")
        self.add_option("personal roleplaying", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_PLAYTESTER_ONLY,
                       lambda p, v: p.attrs.setdefault("roleplaying", v), lambda p: p.attrs.get("roleplaying", 0),
                       "Enable or disable roleplaying mode")

        # Player options from /std/player/options.c
        self.add_option("player follow groups", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_auto_follow_group(p, v), lambda p: self.query_auto_follow_group(p),
                       "Should the player auto follow in groups")
        self.add_option("player follow friends", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_auto_follow_friends(p, v), lambda p: self.query_auto_follow_friends(p),
                       "Should the player auto follow friends")
        self.add_option("player follow everyone", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_auto_follow_everyone(p, v), lambda p: self.query_auto_follow_everyone(p),
                       "Should the player auto follow everyone")
        self.add_option("player lead behind", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_lead_from_behind(p, v), lambda p: self.query_lead_from_behind(p),
                       "Should the player lead from behind")
        self.add_option("player mxp disable", OPTIONS_TYPE_BOOLEAN, OPTIONS_TYPE_ALL,
                       lambda p, v: self.set_mxp_disable(p, v), lambda p: self.query_mxp_disable(p),
                       "Disable MXP support")

    def init_options(self, obj: Player):
        if "options" not in obj.attrs:
            obj.attrs["options"] = {
                "output": {"look": 0, "combat": 0, "errors": 0, "score": 0, "names": 0, "htell": 0},
                "combat": {"wimpy": 20, "monitor": 1, "killer": 0},
                "tactics": {},
                "colour": {},
                "terminal": {"type": "", "rows": 0, "cols": 0},
                "input": {"ambiguous": 0, "andascomma": 0, "editor": "menu", "shorthand": 0},
                "earmuff": {"state": "off", "cut-through": 0},
                "personal": {"description": "none", "real_name": "none", "location": "none", "homepage": "none", "email": "none", "birthday": "none", "execinclude": "none", "auto_teach": 0, "travel": "walk"},
                "playtester": {"protection": 0, "roleplaying": 0},
                "player": {"follow_groups": 0, "follow_friends": 0, "follow_everyone": 0, "lead_behind": 0, "mxp_disable": 0}
            }
            obj.attrs.setdefault("mangle_accent", False)
            obj.attrs.setdefault("msgout", "")
            obj.attrs.setdefault("msgin", "")
            obj.attrs.setdefault("mmsgout", "")
            obj.attrs.setdefault("mmsgin", "")
            obj.attrs.setdefault("allow_coloured_souls", 0)
            obj.attrs.setdefault("plain_maps", 0)
            obj.attrs.setdefault("terrain_map_in_look", 0)
            obj.attrs.setdefault("tabstops", 0)
            obj.attrs.setdefault("shorthand_output", 0)
            obj.attrs.setdefault("ambiguous", 0)
            obj.attrs.setdefault("andascomma", 0)
            obj.attrs.setdefault("shorthand", 0)
            obj.attrs.setdefault("earmuffs", [])
            obj.attrs.setdefault("cut_earmuffed_tells", 0)
            obj.attrs.setdefault("ls_nickname", 0)
            obj.attrs.setdefault("wimpy", 20)
            obj.attrs.setdefault("monitor", 1)
            obj.attrs.setdefault("player_killer", 0)
            obj.attrs.setdefault("editor", "menu")
            obj.attrs.setdefault("term_type", "")
            obj.attrs.setdefault("rows", 0)
            obj.attrs.setdefault("cols", 0)
            obj.attrs.setdefault("pt_protection", 0)
            obj.attrs.setdefault("roleplaying", 0)
            self.driver.save_object(obj)

    async def options_command(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player):
            return "Only players can use the options command."
        if caller.oid != obj.oid:
            return "You can only modify your own options."

        if not arg:
            return self.display_options(caller)

        args = arg.lower().split(maxsplit=1)
        if len(args) < 1:
            return "Syntax: options [setting] [value] or options help"

        command = args[0]
        if command == "help":
            return self.help_text()
        elif len(args) == 1 and self.is_option_group(caller, command):
            return self.display_category(caller, command)
        elif len(args) == 2:
            setting, value = args
            if self.is_option(caller, setting):
                return await self.set_option(caller, setting, value)
            elif setting.endswith(" all") and self.is_option_group(caller, setting[:-4]):
                return await self.set_all(caller, setting[:-4], value)
            else:
                return f"Unknown setting '{setting}'. Use 'options help' for valid settings."
        return "Syntax: options [setting] [value] or options help"

    def display_options(self, caller: Player) -> str:
        options = caller.attrs["options"]
        output = "Your current options are:\n"
        for category, settings in options.items():
            output += f"{category.capitalize()}:\n"
            for setting, value in settings.items():
                if category == "combat" and setting == "monitor":
                    value = MONITOR_OPTIONS[value]
                output += f"  {setting}: {value}\n"
        return output

    def display_category(self, caller: Player, category: str) -> str:
        if not self.is_option_group(caller, category):
            return f"Unknown category '{category}'. Use 'options help' for valid categories."
        options = caller.attrs["options"].get(category, {})
        output = f"{category.capitalize()} options:\n"
        for setting, value in options.items():
            if category == "combat" and setting == "monitor":
                value = MONITOR_OPTIONS[value]
            output += f"  {setting}: {value}\n"
        return output

    async def set_option(self, caller: Player, option: str, value: str) -> str:
        if not self.is_option(caller, option):
            return f"There is no option {option}."
        old_value = self.query_option_value(caller, option)
        if self.set_option_value(caller, option, value):
            new_value = self.query_option_value(caller, option)
            return f"Set option {option} to {new_value} (was {old_value if old_value else 'unset'})."
        return f"Unable to set option {option} to {value}."

    async def set_all(self, caller: Player, option: str, value: str) -> str:
        if not self.is_option_group(caller, option):
            return f"The option must be an option group to use the 'all' keyword."
        sub_options = self.query_sub_options(caller, option)
        ok, bad = [], []
        for opt in sub_options:
            full_opt = f"{option} {opt}"
            if self.is_option(caller, full_opt):
                if self.set_option_value(caller, full_opt, value):
                    ok.append(full_opt)
                else:
                    bad.append(full_opt)
        if ok:
            return f"Set {self.query_multiple_short(ok)} to {value}."
        return f"Unable to set {self.query_multiple_short(bad)} to {value}."

    def edit_option(self, caller: Player, option: str) -> str:
        if not self.is_option(caller, option):
            return f"There is no option {option}."
        value = self.query_option_value(caller, option)
        caller.attrs["editing_option"] = option
        return f"Editing the option {option}.\nEnter new value (or 'abort' to cancel):"

    async def finish_edit(self, caller: Player, value: str) -> str:
        option = caller.attrs.pop("editing_option", None)
        if not option or not value or value.lower() == "abort":
            return "Aborting."
        if self.set_option_value(caller, option, value):
            return f"Set option {option} to {self.query_option_value(caller, option)}."
        return f"Unable to set the option {option}."

    def query_multiple_short(self, list_: List[str]) -> str:
        return ", ".join(list_[:-1]) + ("" if len(list_) <= 1 else " and " + list_[-1])

    def set_verbose(self, player: Player, var: str, value: int):
        player.attrs["options"]["output"][var] = value

    def query_verbose(self, player: Player, var: str) -> int:
        return player.attrs["options"]["output"].get(var, 0)

    def set_my_colours(self, player: Player, key: str, value: str):
        if key in player.attrs.get("colours", {}):
            player.attrs["colours"][key] = value

    def colour_event(self, player: Player, key: str) -> str:
        return player.attrs.get("colours", {}).get(key, "default")

    def get_inform_colours(self, player: Player) -> Dict:
        if "inform_colours" not in self._cache_input.get(player.oid, {}):
            self._cache_input[player.oid]["inform_colours"] = {
                "tell": OPTIONS_TYPE_COLOUR, "say": OPTIONS_TYPE_COLOUR
            }
        return self._cache_input[player.oid]["inform_colours"]

    def get_club_colours(self, player: Player) -> Dict:
        if "club_colours" not in self._cache_input.get(player.oid, {}):
            self._cache_input[player.oid]["club_colours"] = {
                "guild": OPTIONS_TYPE_COLOUR
            }
        return self._cache_input[player.oid]["club_colours"]

    def change_bool_property(self, player: Player, prop: str, value: int):
        player.attrs[prop] = value

    def setup_earmuffs(self, player: Player, value: str):
        if value == "on" and not player.attrs.get("earmuffs"):
            player.attrs["earmuffs"] = True
        elif value == "off" and player.attrs.get("earmuffs"):
            player.attrs.pop("earmuffs", None)
        elif value == "allowfriends":
            player.attrs["earmuffs"] = "allowfriends"

    def change_earmuffs(self, player: Player, ear: str, value: int):
        earmuffs = player.attrs.get("earmuffs", [])
        if value and ear not in earmuffs:
            earmuffs.append(ear)
        elif not value and ear in earmuffs:
            earmuffs.remove(ear)
        player.attrs["earmuffs"] = earmuffs

    def valid_birthday(self, str_: str) -> bool:
        if len(str_) != 4 or not str_.isdigit():
            return False
        tot = int(str_)
        month, day = tot % 100, tot // 100
        lengths = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return 1 <= month <= 12 and 1 <= day <= lengths[month]

    def convert_birthday(self, str_: str) -> str:
        tot = int(str_)
        day, month = tot // 100, tot % 100
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        suffix = "th"
        if day in [11, 12, 13]:
            suffix = "th"
        elif day % 10 == 1:
            suffix = "st"
        elif day % 10 == 2:
            suffix = "nd"
        elif day % 10 == 3:
            suffix = "rd"
        return f"{day}{suffix} of {months[month-1]}"

    def set_auto_follow_group(self, player: Player, flag: int):
        options = player.attrs.get("player_options", player_options_control())
        options.follow_groups = flag
        player.attrs["player_options"] = options

    def query_auto_follow_group(self, player: Player) -> int:
        options = player.attrs.get("player_options", player_options_control())
        return options.follow_groups

    def set_auto_follow_friends(self, player: Player, flag: int):
        options = player.attrs.get("player_options", player_options_control())
        options.follow_friends = flag
        player.attrs["player_options"] = options

    def query_auto_follow_friends(self, player: Player) -> int:
        options = player.attrs.get("player_options", player_options_control())
        return options.follow_friends

    def set_auto_follow_everyone(self, player: Player, flag: int):
        options = player.attrs.get("player_options", player_options_control())
        options.follow_everyone = flag
        player.attrs["player_options"] = options

    def query_auto_follow_everyone(self, player: Player) -> int:
        options = player.attrs.get("player_options", player_options_control())
        return options.follow_everyone

    def set_lead_from_behind(self, player: Player, flag: int):
        options = player.attrs.get("player_options", player_options_control())
        options.lead_behind = flag
        player.attrs["player_options"] = options

    def query_lead_from_behind(self, player: Player) -> int:
        options = player.attrs.get("player_options", player_options_control())
        return options.lead_behind

    def set_mxp_disable(self, player: Player, flag: int):
        options = player.attrs.get("player_options", player_options_control())
        options.mxp_disable = flag
        player.attrs["player_options"] = options

    def query_mxp_disable(self, player: Player) -> int:
        options = player.attrs.get("player_options", player_options_control())
        return options.mxp_disable

    def is_mxp_enabled(self, player: Player) -> bool:
        return not self.query_mxp_disable(player)  # Simplified, no has_mxp efun

    def add_option(self, name: str, type_: mixed, cre_only: int, set_func: Callable, query_func: Callable, help: str) -> int:
        path = name.split()
        stuff = self._options
        for option in path[:-1]:
            if option not in stuff or stuff[option].type != OPTIONS_TYPE_GROUP:
                stuff[option] = option({"type": OPTIONS_TYPE_GROUP, "restriction": cre_only, "suboptions": {}, "help": help})
            stuff = stuff[option].suboptions
        stuff[path[-1]] = option(type_, cre_only, set_func, query_func, {}, help)
        return 1

    def add_option_to_mapping(self, array: Dict, name: str, type_: mixed, cre_only: int, set_func: Callable, query_func: Callable, help: str):
        array[name] = option(type_, cre_only, set_func, query_func, {}, help)

    def query_sub_option(self, player: Player, name: str, tree: Dict) -> Optional[Dict]:
        if name in tree and isinstance(tree[name], dict):
            return tree[name]
        if name in tree and isinstance(tree[name], option):
            if tree[name].restriction == OPTIONS_TYPE_CRE_ONLY and not player.attrs.get("creator", False):
                return 0
            if tree[name].restriction == OPTIONS_TYPE_PLAYTESTER_ONLY and not player.attrs.get("playtester", False):
                return 0
            if tree[name].type == OPTIONS_TYPE_DYNAMIC_GROUP:
                return self.get_inform_colours(player) if name == "inform" else self.get_club_colours(player) if name == "club" else tree[name].suboptions
            if tree[name].type == OPTIONS_TYPE_GROUP:
                return tree[name].suboptions
            return tree[name]
        return 0

    def query_bottom_sub_option(self, player: Player, path: List[str]) -> Optional[Dict]:
        if not path:
            return self._options
        stuff = self._options
        for option in path[:-1]:
            stuff = self.query_sub_option(player, option, stuff) or {}
            if not isinstance(stuff, dict):
                return 0
        return self.query_sub_option(player, path[-1], stuff)

    def is_option(self, player: Player, name: str) -> bool:
        stuff = self.query_bottom_sub_option(player, name.split())
        return isinstance(stuff, option)

    def is_option_group(self, player: Player, name: str) -> bool:
        stuff = self.query_bottom_sub_option(player, name.split())
        return isinstance(stuff, dict) and stuff

    def query_sub_options(self, player: Player, name: str) -> List[str]:
        stuff = self.query_bottom_sub_option(player, name.split())
        if isinstance(stuff, dict):
            return [k for k in stuff.keys() if self.query_bottom_sub_option(player, (name + " " + k).split())]
        return []

    def query_option_values(self, player: Player, name: str) -> List[str]:
        stuff = self.query_bottom_sub_option(player, name.split())
        if isinstance(stuff, option):
            if isinstance(stuff.type, list):
                return stuff.type
            return {
                OPTIONS_TYPE_BRIEF: ["brief", "verbose"],
                OPTIONS_TYPE_BOOLEAN: ["on", "off"],
                OPTIONS_TYPE_INTEGER: ["integer"],
                OPTIONS_TYPE_STRING: ["string"],
                OPTIONS_TYPE_PERCENTAGE: ["0..100"],
                OPTIONS_TYPE_COLOUR: ["none", "default", "colour"]
            }.get(stuff.type, [])
        return []

    def query_option_value(self, player: Player, path: str) -> str:
        stuff = self.query_bottom_sub_option(player, path.split())
        if isinstance(stuff, option):
            value = stuff.query(player)
            if isinstance(stuff.type, int):
                if stuff.type == OPTIONS_TYPE_BRIEF:
                    return "verbose" if value else "brief"
                elif stuff.type == OPTIONS_TYPE_BOOLEAN:
                    return "on" if value else "off"
                elif stuff.type == OPTIONS_TYPE_COLOUR:
                    return "[none]" if value == "" else "[default]" if value == "default" else f"[{value}%^RESET%^]"
            return str(value)
        return ""

    def query_option_help(self, player: Player, path: str) -> str:
        stuff = self.query_bottom_sub_option(player, path.split())
        return stuff.help if isinstance(stuff, option) else ""

    def set_option_value(self, player: Player, path: str, value: str) -> bool:
        stuff = self.query_bottom_sub_option(player, path.split())
        if not isinstance(stuff, option):
            return False
        set_value = value
        if isinstance(stuff.type, list):
            if value not in stuff.type:
                return False
        elif isinstance(stuff.type, int):
            if stuff.type == OPTIONS_TYPE_BRIEF:
                set_value = 1 if value == "verbose" else 0 if value == "brief" else None
            elif stuff.type == OPTIONS_TYPE_BOOLEAN:
                set_value = 1 if value in ["on", "true"] else 0 if value in ["off", "false"] else None
            elif stuff.type == OPTIONS_TYPE_INTEGER or stuff.type == OPTIONS_TYPE_PERCENTAGE:
                if not re.match(r"^\d+$", value):
                    return False
                set_value = int(value)
                if stuff.type == OPTIONS_TYPE_PERCENTAGE and (set_value < 0 or set_value > 100):
                    return False
            elif stuff.type == OPTIONS_TYPE_COLOUR:
                if value in ["none", "default"]:
                    set_value = value
                else:
                    colours = [upper_case(c) for c in value.split()]
                    bad = [c for c in colours if c not in self._colours]
                    if bad:
                        return False
                    set_value = "%^" + "%^ %^".join(colours) + "%^"
        return stuff.set(player, set_value) if set_value is not None else False

    def help_text(self) -> str:
        output = "Options help:\n"
        for category in ["output", "combat", "colour", "terminal", "input", "earmuff", "command", "personal", "playtester", "player"]:
            output += f"{category.capitalize()} settings:\n"
            sub_options = self.query_sub_options(None, category)
            for opt in sub_options:
                full_opt = f"{category} {opt}"
                values = self.query_option_values(None, full_opt)
                help_text = self.query_option_help(None, full_opt)
                output += f"  {opt}: {', '.join(values) if values else 'variable'} - {help_text}\n"
        output += "Syntax: options [setting] [value] or options help\nExample: options combat monitor on"
        return output

# Initialize options handler
options_handler = OptionsHandler()

async def init(driver_instance):
    await options_handler.init(driver_instance)
