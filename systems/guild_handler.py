# /mnt/home2/mud/systems/guild_handler.py
# Imported to: room.py, living.py, taskmaster.py, guild_list.py
# Imports from: driver.py, taskmaster.py

from typing import Dict, List, Optional, Union
from ..driver import driver, MudObject, Player
import asyncio
import os
import math

# Constants from guild.c, guild_base.c, and skills.h
COST_DIV = 10
STD_COST = 100
LEVEL_DIV = 50
DEFAULT_COST = 50
NROFF_SOURCE = "/doc/help/"

class TeachSkill:
    def __init__(self, skill: str, teach: int, learn: int):
        self.skill = skill
        self.teach = teach
        self.learn = learn
        
#To add??
#class GuildHandler:
#    async def init(self, obj: MudObject):
#        """Initializes guild commands, now supporting outdoor rooms."""
#        is_outdoor = hasattr(obj, "query_zone") and obj.query_property("location") == "outside"
#        obj.add_command("advance", "<string>", lambda p, a: self.do_advance(p, a[0], is_outdoor))
        # ... (other commands updated similarly with is_outdoor param)

#    async def do_advance(self, player: Player, skill: str, is_outdoor: bool = False) -> bool:
#        if player.query_guild() != self.guild_name:
#            await player.send("Seek your guild’s hall—or garden—for advancement.\n")
#            return False
        # ... (rest unchanged)

#    async def do_join(self, player: Player, is_outdoor: bool = False) -> bool:
#        welcome = "You join the {self.guild_name} guild under Mystra’s aegis" + \
#                  (" amidst the open sky." if is_outdoor else ".")
        # ... (rest updated with welcome)

class GuildHandler:
    def __init__(self):
        self.guild_name: Optional[str] = None
        self.start_pos: Optional[str] = None
        self.cost_div: int = COST_DIV
        self.cost_mult: int = 100
        self.spells: Dict[str, List] = {}  # {skill_path: [name, level]}
        self.commands: Dict[str, List] = {}  # {skill_path: [name, level]}
        self.teaching_person: Optional[MudObject] = None
        self.nroff_file: Optional[str] = None  # From guild_base.c
        self.teach_skills: List[TeachSkill] = []  # Teaching requirements
        self.teach_guild: Optional[str] = None  # Guild restriction

    async def init(self, obj: MudObject):
        """Initializes guild commands for a room or object."""
        obj.add_command("advance", "<string>", lambda p, a: self.do_advance(p, a[0]))
        obj.add_command("advance", "<string> to <number>", lambda p, a: self.do_advance_to(p, a[0], a[1]))
        obj.add_command("advance", "<string> by <number>", lambda p, a: self.do_advance_by(p, a[0], a[1]))
        obj.add_command("join", "", lambda p, _: self.do_join(p))
        obj.add_command("cost", "primaries", lambda p, _: self.do_cost_primaries(p))
        obj.add_command("cost", "all", lambda p, _: self.do_cost_all(p, brief=False))
        obj.add_command("cost", "all brief", lambda p, _: self.do_cost_all(p, brief=True))
        obj.add_command("cost", "<string>", lambda p, a: self.do_cost(p, a[0]))
        obj.add_command("cost", "<string> to <number>", lambda p, a: self.do_cost_to(p, a[0], a[1]))
        obj.add_command("cost", "<string> by <number>", lambda p, a: self.do_cost_by(p, a[0], a[1]))
        obj.add_command("info", "", lambda p, _: self.do_info(p))
        if isinstance(obj, Player) and obj.query_guild() == self.guild_name and self.start_pos:
            obj.add_start(obj.environment().oid if obj.environment() else "default", self.start_pos)

    def set_guild(self, guild_name: str, start_pos: Optional[str] = None):
        self.guild_name = guild_name
        self.start_pos = start_pos

    def set_cost_div(self, div: int):
        self.cost_div = div
        self.cost_mult = 1000 if not div else 10 + (990 * div) // (10 * COST_DIV + div)

    def set_nroff_file(self, fname: str):
        """Sets the help file (guild_base.c)."""
        self.nroff_file = fname if fname.startswith("/") else f"{NROFF_SOURCE}{fname}"

    async def help(self, player: Player) -> str:
        """Returns help text from nroff file (2025 async)."""
        if not self.nroff_file or not os.path.exists(self.nroff_file):
            return "No lore is inscribed for this guild.\n"
        with open(self.nroff_file, "r") as f:
            return f"Scrolls of {self.guild_name}:\n{f.read()}\nSeek Mystra’s wisdom.\n"

    def add_teach_skill(self, skill: str, teach: int, learn: int):
        """Adds teaching requirements (guild_base.c)."""
        self.teach_skills.append(TeachSkill(skill, teach, learn))

    def set_teach_guild(self, guild: str):
        """Restricts teaching to a guild (guild_base.c)."""
        self.teach_guild = guild

    async def can_teach_command(self, teacher: Player, student: Player, command: str) -> int:
        """Checks if a command can be taught (guild_base.c)."""
        if not self.teach_skills or not command:
            return 0
        for ts in self.teach_skills:
            if teacher.query_skill(ts.skill) < ts.teach:
                return -1  # Teacher too low
            if student.query_skill(ts.skill) < ts.learn:
                return -2  # Student too low
        if self.teach_guild and student.query_guild() != self.teach_guild:
            return -3  # Wrong guild
        return 1

    async def teach_command(self, teacher: Player, student: Player, command: str) -> bool:
        """Teaches a command (guild_base.c)."""
        ret = await self.can_teach_command(teacher, student, command)
        if ret == 1:
            student.add_known_command(command)
            await student.send(f"{teacher.name} imparts the secret of '{command}' to you.\n")
            await teacher.send(f"You teach {student.name} the art of '{command}'.\n")
            return True
        return False

    def query_skill_cost(self, player: Player, skill: str, offset: int) -> int:
        total = DEFAULT_COST if not player.query_guild() else STD_COST
        total *= self.cost_mult // 500
        total *= (player.query_skill(skill) + offset) // LEVEL_DIV + 1
        total = int(total * math.exp((player.query_skill(skill) + offset) / 150.0))
        if "faith" in skill and player.attrs.get("mystra_blessing", 0) > 0:
            total = int(total * 0.9)
        return total

    async def do_advance_internal(self, player: Player, skill: str, to: int = 0, by: int = 0) -> bool:
        if player.query_guild() != self.guild_name:
            await player.send("Seek your own guild hall for advancement.\n")
            return False
        skill_name = skill  # Placeholder until skills.py
        lvl = player.query_skill(skill_name)
        by = to - lvl if to else by
        if by <= 0:
            await player.send(f"You are at level {lvl} in {skill_name}.\n" if by == 0 else "You cannot unlearn your skills!\n")
            return False
        total_xp = 0
        for i in range(by):
            cost = self.query_skill_cost(player, skill_name, i)
            if player.query_xp() < total_xp + cost:
                if not i:
                    await player.send(f"Your experience is too faint to advance {skill_name}.\n")
                    return False
                await player.send(f"Experience fades—you reach level {lvl + i} in {skill_name}.\n")
                break
            total_xp += cost
        player.adjust_xp(-total_xp)
        player.add_skill_level(skill_name, i, total_xp)
        await player.send(f"You ascend in {skill_name} from {lvl} to {lvl + i} for {total_xp} XP.\n")
        await player.environment().tell_room(f"{player.one_short()} rises in skill under Mystra’s gaze.\n")
        return True

    async def do_advance(self, player: Player, skill: str) -> bool:
        return await self.do_advance_internal(player, skill, by=1)

    async def do_advance_to(self, player: Player, skill: str, num: int) -> bool:
        return await self.do_advance_internal(player, skill, to=num)

    async def do_advance_by(self, player: Player, skill: str, num: int) -> bool:
        return await self.do_advance_internal(player, skill, by=num)

    async def do_join(self, player: Player) -> bool:
        if player.query_guild() == self.guild_name:
            await player.send("You are already sworn to this guild.\n")
            return False
        if player.query_guild():
            await player.send("You must forsake your current guild first.\n")
            return False
        await player.send("This oath binds you to Faerûn’s fate. Are you sure? (yes/no): ")
        response = await player.input("join_confirm")
        if response.lower() != "yes":
            await player.send(f"You turn from the {self.guild_name} guild’s path.\n")
            return False
        player.set_guild(self.guild_name)
        await player.send(f"You join the {self.guild_name} guild, blessed by Mystra.\n")
        await player.environment().tell_room(f"{player.one_short()} binds their fate to the {self.guild_name} guild.\n")
        return True

    async def do_info(self, player: Player) -> bool:
        """Displays guild info (guild_base.c integration)."""
        if player.query_guild() != self.guild_name:
            await player.send("This lore is not for outsiders.\n")
            return False
        info = f"The {self.guild_name} guild welcomes you:\n"
        info += await self.help(player)
        await player.send(info)
        return True

    # Placeholder for do_cost_* methods—awaiting skills.py for full primaries support

async def init(driver_instance):
    driver = driver_instance
    driver.guild_handler = GuildHandler()