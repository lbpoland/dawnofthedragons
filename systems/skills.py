# /mnt/home2/mud/systems/skills.py
# Imported to: living.py, guild_handler.py, taskmaster.py, skills_cmd.py
# Imports from: driver.py, taskmaster.py

from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject, Player
import asyncio
import math
import time
import random

# 2025 top-level skills from dwwiki.mooo.com/wiki/Skills
STD_SKILLS = ["adventuring", "covert", "crafts", "faith", "fighting", "magic", "people"]

# Stat bonuses from bonuses.irreducible.org/skillstat.php
STAT_BONUS = {
    "adventuring": "DDIIW", "adventuring.acrobatics": "CDDSS", "adventuring.acrobatics.balance": "CDDSS",
    "adventuring.acrobatics.tumbling": "CDDSS", "adventuring.acrobatics.vaulting": "CDDSS",
    "adventuring.direction": "DDIIW", "adventuring.evaluating.armour": "IIIIW",
    "adventuring.evaluating.weapons": "IIIIW", "adventuring.health": "CCCCS",
    "adventuring.movement": "CCDDS", "adventuring.movement.climbing": "DCDSS",
    "adventuring.movement.climbing.rope": "DCDSS", "adventuring.movement.climbing.rock": "DCDSS",
    "adventuring.movement.climbing.tree": "DCDSS", "adventuring.movement.riding": "CCDDS",
    "adventuring.movement.riding.camel": "CCDDS", "adventuring.movement.riding.horse": "CCDDS",
    "adventuring.movement.swimming": "CCDDS", "adventuring.perception": "IIWWW",
    "adventuring.points": "CDISW",
    "covert": "DDDII", "covert.casing": "DIIWW", "covert.casing.person": "DIIWW",
    "covert.casing.place": "DIIWW", "covert.hiding": "DDIIS", "covert.hiding.object": "DDIIS",
    "covert.hiding.person": "DDIIS", "covert.items": "DIIII", "covert.lockpick": "DDDDI",
    "covert.lockpick.doors": "DDDDI", "covert.lockpick.safes": "DDDDI", "covert.lockpick.traps": "DDDDI",
    "covert.manipulation": "DDISS", "covert.manipulation.palming": "DDISS",
    "covert.manipulation.passing": "DDISS", "covert.manipulation.sleight-of-hand": "DDISS",
    "covert.manipulation.stealing": "DDISS", "covert.points": "DDIIC", "covert.stealth": "DDDIS",
    "covert.stealth.inside": "DDDIS", "covert.stealth.outside": "DDDIS", "covert.stealth.underwater": "DDDIS",
    "crafts": "DDIIW", "crafts.arts": "DIIII", "crafts.arts.calligraphy": "DIIII",
    "crafts.arts.design": "DIIII", "crafts.arts.drawing": "DIIII", "crafts.arts.painting": "DIIII",
    "crafts.arts.printing": "DIIII", "crafts.arts.sculpture": "DIIII", "crafts.carpentry": "DDIIS",
    "crafts.carpentry.coopering": "DDIIS", "crafts.carpentry.furniture": "DDIIS",
    "crafts.carpentry.turning": "DDIIS", "crafts.carpentry.whittling": "DDIIS",
    "crafts.culinary": "DDIII", "crafts.culinary.baking": "DDIII", "crafts.culinary.brewing": "DDIII",
    "crafts.culinary.butchering": "DDIII", "crafts.culinary.cooking": "DDIII",
    "crafts.culinary.distilling": "DDIII", "crafts.culinary.preserving": "DDIII",
    "crafts.husbandry": "IIIWW", "crafts.husbandry.animal": "IIIWW",
    "crafts.husbandry.animal.breeding": "IIIWW", "crafts.husbandry.animal.grooming": "IIIWW",
    "crafts.husbandry.plant": "IIIWW", "crafts.husbandry.plant.edible": "IIIWW",
    "crafts.husbandry.plant.herbal": "IIIWW", "crafts.husbandry.plant.milling": "IIIWW",
    "crafts.husbandry.plant.tree": "IIIWW", "crafts.hunting": "DDIII",
    "crafts.hunting.fishing": "DDIII", "crafts.hunting.tracking": "DDIII",
    "crafts.hunting.trapping": "DDIII", "crafts.materials": "DDIIS",
    "crafts.materials.dyeing": "DDIIS", "crafts.materials.leatherwork": "DDIIS",
    "crafts.materials.needlework": "DDIIS", "crafts.materials.spinning": "DDIIS",
    "crafts.materials.weaving": "DDIIS", "crafts.mining": "DIISS", "crafts.mining.gem": "DIISS",
    "crafts.mining.mineral": "DIISS", "crafts.mining.ore.panning": "DIISS",
    "crafts.music": "DIIII", "crafts.music.instruments": "DIIII",
    "crafts.music.instruments.keyboard": "DIIII", "crafts.music.instruments.percussion": "DIIII",
    "crafts.music.instruments.stringed": "DIIII", "crafts.music.instruments.vocal": "DIIII",
    "crafts.music.instruments.wind": "DIIII", "crafts.music.performance": "DIIII",
    "crafts.music.special": "DIIII", "crafts.music.theory": "DIIII", "crafts.points": "DDIIW",
    "crafts.pottery": "DDDII", "crafts.pottery.firing": "DDDII", "crafts.pottery.forming": "DDDII",
    "crafts.pottery.forming.shaping": "DDDII", "crafts.pottery.forming.throwing": "DDDII",
    "crafts.pottery.glazing": "DDDII", "crafts.pottery.staining": "DDDII",
    "crafts.smithing": "DDIIS", "crafts.smithing.black": "DDIIS",
    "crafts.smithing.black.armour": "DDIIS", "crafts.smithing.black.tool": "DDIIS",
    "crafts.smithing.black.weapon": "DDIIS", "crafts.smithing.gem": "DDIIS",
    "crafts.smithing.gem.cutting": "DDIIS", "crafts.smithing.gem.polishing": "DDIIS",
    "crafts.smithing.gem.setting": "DDIIS", "crafts.smithing.gold": "DDIIS",
    "crafts.smithing.silver": "DDIIS",
    "faith": "ISWWW", "faith.items": "IIDWW", "faith.items.relic": "IIDWW",
    "faith.items.rod": "IIDWW", "faith.items.scroll": "IIDWW", "faith.points": "IICWW",
    "faith.rituals": "IIWWW", "faith.rituals.curing": "ICCWW", "faith.rituals.curing.self": "ICCWW",
    "faith.rituals.curing.target": "ICCWW", "faith.rituals.defensive": "IDDWW",
    "faith.rituals.defensive.area": "IDDWW", "faith.rituals.defensive.self": "IDDWW",
    "faith.rituals.defensive.target": "IDDWW", "faith.rituals.misc": "IIWWW",
    "faith.rituals.offensive": "ISSWW", "faith.rituals.offensive.area": "ISSWW",
    "faith.rituals.offensive.target": "ISSWW", "faith.rituals.special": "IIWWW",
    "fighting": "DDSSI", "fighting.defence": "DDSSW", "fighting.defence.dodging": "DDDSW",
    "fighting.defence.parrying": "DDSSW", "fighting.melee": "DSSSW", "fighting.melee.blunt": "DSSSS",
    "fighting.melee.pierce": "DDDSS", "fighting.melee.sharp": "DDSSS", "fighting.melee.unarmed": "DDDSW",
    "fighting.points": "DSSCC", "fighting.range": "DDDSS", "fighting.range.bow": "DDDSS",
    "fighting.range.fired": "DDDSS", "fighting.range.thrown": "DDDSS", "fighting.special": "SDIII",
    "fighting.special.tactics": "WWIII", "fighting.special.unarmed": "DDIII",
    "fighting.special.weapon": "SDIII",
    "magic": "IIIDW", "magic.items": "IIDWW", "magic.items.held": "IIDWW",
    "magic.items.held.staff": "IIDWW", "magic.items.held.wand": "IIDWW",
    "magic.items.scroll": "IIDWW", "magic.items.worn": "IIDWW", "magic.items.worn.amulet": "IIDWW",
    "magic.items.worn.ring": "IIDWW", "magic.methods": "IIWWW", "magic.methods.elemental": "IICCC",
    "magic.methods.elemental.air": "IICCC", "magic.methods.elemental.earth": "IICCC",
    "magic.methods.elemental.fire": "IICCC", "magic.methods.elemental.water": "IICCC",
    "magic.methods.mental": "IIIII", "magic.methods.mental.animating": "IIIII",
    "magic.methods.mental.channeling": "IIIII", "magic.methods.mental.convoking": "IIIII",
    "magic.methods.mental.cursing": "IIIII", "magic.methods.physical": "IIDDD",
    "magic.methods.physical.binding": "IIDDD", "magic.methods.physical.brewing": "IIDDD",
    "magic.methods.physical.chanting": "IIDDD", "magic.methods.physical.dancing": "IIDDD",
    "magic.methods.physical.enchanting": "IIDDD", "magic.methods.physical.evoking": "IIDDD",
    "magic.methods.physical.healing": "IIDDD", "magic.methods.physical.scrying": "IIDDD",
    "magic.methods.spiritual": "IIWWW", "magic.methods.spiritual.abjuring": "IIWWW",
    "magic.methods.spiritual.conjuring": "IIWWW", "magic.methods.spiritual.divining": "IIWWW",
    "magic.methods.spiritual.summoning": "IIWWW", "magic.points": "IISWW",
    "magic.spells": "IIDWW", "magic.spells.defensive": "WCCII", "magic.spells.misc": "WDDII",
    "magic.spells.offensive": "WSSII", "magic.spells.special": "WWWII",
    "people": "IIIWW", "people.culture": "IIIWW", "people.culture.ankh-morpork": "IIIWW",
    "people.culture.djelibeybi": "IIIWW", "people.culture.ephebe": "IIIWW",
    "people.culture.genua": "IIIWW", "people.culture.klatch": "IIIWW",
    "people.culture.lancrastian": "IIIWW", "people.culture.sto-plains": "IIIWW",
    "people.points": "IIIWW", "people.trading": "IIIIW", "people.trading.buying": "IIIIW",
    "people.trading.selling": "IIIIW", "people.trading.valueing": "IIIIW"
}

class SkillsHandler:
    def __init__(self):
        self.skills: Dict[str, int] = {}
        self.bonus_cache: Dict[str, int] = {}
        self.stat_cache: Dict[str, Tuple[float, str]] = {}
        self.teach_offer: Dict[MudObject, List] = {}
        self.last_info: Dict[str, List] = {"time": int(time.time())}
        self.skill_tree: Dict[str, List[str]] = {}
        self.immediate_children: Dict[str, List[str]] = {}
        self.only_leaf: Dict[str, bool] = {"people": True}
        self.not_allowed_to_teach: Dict[str, bool] = {}
        self.only_show_if_non_zero: Dict[str, bool] = {}
        self.no_bonus: Dict[str, bool] = {}
        self.ignore_bits: Dict[str, bool] = {"crafts": True}
        self._init_skill_tree()

    def _init_skill_tree(self):
        """Builds skill tree from STAT_BONUS."""
        for skill in STAT_BONUS.keys():
            self.skill_tree[skill] = self._create_skill_tree(skill)
            children = [s for s in STAT_BONUS.keys() if s.startswith(skill + ".")]
            self.immediate_children[skill] = [c[len(skill) + 1:] for c in children if c.count(".") == skill.count(".") + 1]

    def _create_skill_tree(self, skill: str) -> List[str]:
        bits = skill.split(".")
        if self.only_leaf.get(bits[0], False):
            return [skill]
        return [".".join(bits[:i + 1]) for i in range(len(bits))][::-1]

    def setup(self, obj: MudObject):
        obj.skills_handler = self
        obj.skills = self.skills.copy()
        obj.bonus_cache = self.bonus_cache.copy()
        obj.stat_cache = self.stat_cache.copy()
        obj.teach_offer = self.teach_offer.copy()
        obj.last_info = self.last_info.copy()

    def query_skill(self, skill: str) -> int:
        if not skill or skill.startswith("."):
            skill = skill[1:] if skill else ""
        return self.skills.get(skill, 0)

    async def query_skill_bonus(self, player: Player, skill: str, use_base_stats: bool = False) -> int:
        if not skill or skill.startswith("."):
            skill = skill[1:] if skill else ""
        if skill in self.bonus_cache and not use_base_stats:
            return await self.stat_modify(player, self.bonus_cache[skill], skill, use_base_stats)
        lvl = self.query_skill(skill)
        return await self.calc_bonus(player, lvl, skill, use_base_stats)

    async def calc_bonus(self, player: Player, lvl: int, skill: str, use_base_stats: bool) -> int:
        # Updated per bonuses.irreducible.org/formulas.php
        if lvl > 60:
            lvl = 170 + ((lvl - 60) // 2)
        elif lvl > 40:
            lvl = 150 + (lvl - 40)
        elif lvl > 20:
            lvl = 100 + ((lvl - 20) * 5) // 2
        else:
            lvl = lvl * 5
        if not use_base_stats:
            self.bonus_cache[skill] = lvl
        return await self.stat_modify(player, lvl, skill, use_base_stats)

    async def stat_modify(self, player: Player, lvl: int, skill: str, use_base_stats: bool) -> int:
        bonus = 0.0
        stat_bonus = self.query_skill_stat(skill)
        if not stat_bonus:
            return lvl
        for stat in stat_bonus:
            value = {
                'I': player.query_int,
                'D': player.query_dex,
                'S': player.query_str,
                'C': player.query_con,
                'W': player.query_wis
            }[stat]() if not use_base_stats else {
                'I': player.query_real_int,
                'D': player.query_real_dex,
                'S': player.query_real_str,
                'C': player.query_real_con,
                'W': player.query_real_wis
            }[stat]()
            bonus += math.log(max(1, value)) / 9.8 - 0.25 if value > 0 else -0.25
        if not use_base_stats:
            self.stat_cache[skill] = (bonus, stat_bonus)
        return max(0, int(lvl + (lvl * bonus)))

    async def add_skill_level(self, player: Player, skill: str, lvl: int, exp: Optional[int] = None) -> bool:
        if not skill or not isinstance(lvl, int) or lvl > 1000:
            return False
        if skill.startswith("."):
            skill = skill[1:]
        
        recursive_skills = self.query_related_skills(skill)
        for r_skill in recursive_skills:
            self.skills[r_skill] = self.skills.get(r_skill, 0) + lvl
            if self.skills[r_skill] < 0:
                self.skills[r_skill] = 0
            self.bonus_cache.pop(r_skill, None)

        if exp and lvl == 1 and await self.tm_check_ok(player, skill, driver.previous_object()):
            player.adjust_xp(-exp)
            await player.send(f"You’ve honed {skill} to level {self.skills[skill]} for {exp} XP under Mystra’s gaze.\n")
            driver.tasker.award_made(player.name, driver.previous_object().oid, skill, self.skills[skill])
        elif exp and not await self.tm_check_ok(player, skill, driver.previous_object()):
            self.skills[skill] -= 1
            return False
        
        if player.query_guild():
            guild = driver.load_object(player.query_guild())
            if guild:
                await guild.skills_advanced(player, skill, self.skills[skill])
        await asyncio.sleep(1)
        return True

    async Heck_ok(self, player: Player, skill: str, exp: MudObject) -> bool:
        delay = 30 + random.randint(0, player.query_level()) + random.randint(0, self.query_skill(skill))
        if self.last_info.get("object", [None])[0] == exp.oid:
            delay *= self.last_info["object"][1]
        if player.query_level() * 2 < self.query_skill(skill):
            delay *= 2
        if time.time() - self.last_info["time"] < delay:
            self.last_info["skill"] = [skill, self.last_info.get("skill", [skill, 1])[1] + 1]
            self.last_info["object"] = [exp.oid, self.last_info.get("object", [exp.oid, 1])[1] + 1]
            self.last_info["time"] = int(time.time())
            return False
        self.last_info["skill"] = [skill, 2]
        self.last_info["object"] = [exp.oid, 2]
        self.last_info["time"] = int(time.time())
        return True

    def query_skill_stat(self, skill: str) -> str:
        bits = skill.split(".")
        for i in range(len(bits), -1, -1):
            s = ".".join(bits[:i])
            if s in STAT_BONUS:
                return STAT_BONUS[s]
        return "DDIIW"  # Default fallback

    def query_immediate_children(self, skill: str) -> List[str]:
        return self.immediate_children.get(skill, [])

    def query_all_children(self, skill: str) -> List[str]:
        children = self.query_immediate_children(skill)
        result = children.copy()
        for child in children:
            result.extend(self.query_all_children(f"{skill}.{child}"))
        return result

    def query_related_skills(self, skill: str) -> List[str]:
        return [skill] + self.query_all_children(skill)

    def query_only_leaf(self, skill: str) -> bool:
        return self.only_leaf.get(skill.split(".")[0], False)

async def init(driver_instance):
    driver = driver_instance
    driver.skills_handler = SkillsHandler()