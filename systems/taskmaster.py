# /mnt/home2/mud/systems/taskmaster.py
from typing import Dict, Optional, Tuple, ClassVar
from ..driver import driver, Player, MudObject
import asyncio
import random
import math

class tasker_result:
    def __init__(self, result: int, degree: int, raw: int):
        self.result = result
        self.degree = degree
        self.raw = raw

class Taskmaster:
    # Task types from /include/tasks.h
    TM_CONTINUOUS = 1
    TM_FREE = 2
    TM_FIXED = 4
    TM_COMMAND = 8
    TM_RITUAL = 16
    TM_SPELL = 32
    TM_NONE = 64

    # Task outcomes
    AWARD = 1
    SUCCEED = 2
    FAIL = 3
    BARF = 0  # Error code

    # Degree constants (inferred from mudlib)
    TASKER_MARGINAL = 1
    TASKER_NORMAL = 2
    TASKER_EXCEPTIONAL = 3
    TASKER_CRITICAL = 4
    TASKER_MARGINAL_UPPER = 10
    TASKER_NORMAL_UPPER = 30

    # Skill categories and caps (from wiki and mudlib context)
    SKILL_CATEGORIES: ClassVar[Dict[str, int]] = {
        "fighting.combat.melee": 300,
        "fighting.combat.dodge": 300,
        "fighting.combat.parry": 300,
        "fighting.combat.unarmed": 300,
        "fighting.combat.tactics": 300,
        "other.perception": 200,
        "magic.spellcasting": 250  # Forgotten Realms adaptation
    }

    BASE = 100  # Base skill level for exponential decay (inferred)
    DECAY = 50  # Decay constant for upper limit (inferred)
    MODIFIER = 10  # Modifier for upper limit (inferred)
    E_MODIFIER = 10  # Modifier for attempt_task_e (inferred)

    def __init__(self):
        self.skills: Dict[str, Dict[str, int]] = {}  # {oid: {skill: level}}
        self.stats: Dict[str, Dict] = {}  # {skill: {level: {name: count}}}
        self.critical_chances: List[int] = []  # Precomputed critical chances
        self.last_save = 0
        self.control: Optional[Tuple[object, str]] = None
        self.last = 0
        self.skill = ""

    async def init(self, driver_instance):
        self.driver = driver_instance
        seteuid("Root")  # Simulate LPC seteuid for persistence
        self.precompute_critical_chances()
        for obj in self.driver.objects.values():
            if isinstance(obj, (Player, MudObject)) and hasattr(obj, "attrs"):
                self.init_skills(obj)
                obj.add_action("skills", self.skills_command)

    def precompute_critical_chances(self):
        a = 0.93260  # Constants from create() for y = a*e^(b*i)
        b = 0.06978
        self.critical_chances = [int(a * math.exp(b * (i + 1))) for i in range(100)]

    def init_skills(self, obj: MudObject):
        if obj.oid not in self.skills:
            self.skills[obj.oid] = {skill: 10 for skill in self.SKILL_CATEGORIES.keys()}
            obj.attrs["skills"] = self.skills[obj.oid]
            self.driver.save_object(obj)

    async def skills_command(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player) or caller.oid != obj.oid:
            return "Only players can view their own skills."
        skills = self.skills.get(caller.oid, {})
        output = "Your skills:\n"
        for skill, level in skills.items():
            output += f"  {skill}: {level} (Cap: {self.SKILL_CATEGORIES[skill]})\n"
        return output

    def query_skill_bonus(self, obj: MudObject, skill: str) -> int:
        return self.skills.get(obj.oid, {}).get(skill, 1)

    def set_control(self, args: Tuple[object, str]):
        self.control = args

    def reset_control(self):
        self.control = None

    def query_stats(self, s_name: str) -> Dict:
        if self.skill != s_name:
            self.skill = s_name
            save_file = f"/save/tasks/{s_name}.o"
            if self.driver.file_exists(save_file):
                self.stats = self.driver.load_object(save_file) or {}
            else:
                self.stats = {}
        return self.stats.copy()

    def award_made(self, p_name: str, o_name: str, s_name: str, level: int):
        if isinstance(self.driver.objects.get(p_name), Player):
            await self.driver.call_other(p_name, "inform", f"{p_name} gains a level in {s_name} from {o_name} at level {level}", "skill")

    def compare_skills(self, offob: MudObject, offskill: str, defob: MudObject,
                      defskill: str, modifier: int, off_tm_type: int = TM_CONTINUOUS,
                      def_tm_type: int = TM_CONTINUOUS, degree: int = 0) -> Tuple[int, int] | tasker_result:
        if not offob or not defob or not offskill or not defskill:
            return self.BARF

        offbonus = self.query_skill_bonus(offob, offskill)
        defbonus = self.query_skill_bonus(defob, defskill)
        if not defbonus:
            defbonus = 1
        if not offbonus:
            offbonus = 1

        perc = (50 * offbonus * offbonus) / (offbonus * defbonus) if offbonus > defbonus else 100 - (50 * defbonus * defbonus) / (offbonus * defbonus)
        perc += modifier
        perc = max(1, min(99, perc))

        chance = random.randint(0, 99)
        success_margin = perc - chance
        if success_margin > 0:
            res = self.AWARD if off_tm_type & self.TM_CONTINUOUS and chance < perc * 0.1 else self.SUCCEED
            if degree:
                deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                      self.TASKER_MARGINAL if success_margin < self.TASKER_MARGINAL_UPPER else \
                      self.TASKER_NORMAL if success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
                return tasker_result(res, deg, success_margin)
            perform_result = self.perform_task(offob, offskill, defbonus - modifier, off_tm_type, 0)
            return self.OFFAWARD if perform_result == self.AWARD else self.OFFWIN
        else:
            res = self.AWARD if def_tm_type & self.TM_CONTINUOUS and chance > perc * 0.9 else self.SUCCEED
            if degree:
                deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                      self.TASKER_MARGINAL if -success_margin < self.TASKER_MARGINAL_UPPER else \
                      self.TASKER_NORMAL if -success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
                return tasker_result(res, deg, success_margin)
            perform_result = self.perform_task(defob, defskill, offbonus - modifier, def_tm_type, 0)
            return self.DEFAWARD if perform_result == self.AWARD else self.DEFWIN

    def perform_task(self, person: MudObject, skill: str, difficulty: int,
                    tm_type: int = TM_FREE, degree: int = 0) -> int | tasker_result:
        if not person or not skill:
            return self.BARF

        bonus = self.query_skill_bonus(person, skill)
        if bonus < difficulty:
            return self.FAIL if not degree else tasker_result(self.FAIL, self.TASKER_EXCEPTIONAL, -100)

        upper = 100
        extra = 0
        if tm_type == self.TM_FIXED:
            result = self.attempt_task(difficulty, bonus, 100, 0, degree)
        elif tm_type == self.TM_FREE:
            result = self.attempt_task(difficulty, bonus, 25, 0, degree)
        elif tm_type == self.TM_CONTINUOUS:
            result = self.attempt_task(difficulty, bonus, 50, 0, degree)
        elif tm_type == self.TM_COMMAND:
            if skill.startswith("covert"):
                result = self.attempt_task_e(difficulty, bonus, 60, 40, degree)
            else:
                result = self.attempt_task(difficulty, bonus, 100, 0, degree)
        elif tm_type == self.TM_RITUAL:
            result = self.attempt_task_e(difficulty, bonus, 50, 25, degree)
        elif tm_type == self.TM_SPELL:
            result = self.attempt_task_e(difficulty, bonus, 60, 40, degree)
        elif tm_type == self.TM_NONE:
            result = self.attempt_task_e(difficulty, bonus, 1, 0, degree)
            if isinstance(result, tasker_result) and result.result == self.AWARD:
                result.result = self.SUCCEED
            elif result == self.AWARD:
                result = self.SUCCEED
        else:
            upper = tm_type if tm_type else 100
            result = self.attempt_task(difficulty, bonus, upper, 0, degree)

        if isinstance(result, tasker_result) and result.result == self.AWARD or result == self.AWARD:
            if hasattr(person, "advancement_restriction") and person.advancement_restriction() or \
               not hasattr(person, "add_skill_level") or not person.add_skill_level(skill, 1, self):
                if isinstance(result, tasker_result):
                    result.result = self.SUCCEED
                else:
                    result = self.SUCCEED
        return result

    def attempt_task(self, difficulty: int, bonus: int, upper: int, extra: int, degree: int = 0) -> int | tasker_result:
        if bonus < difficulty:
            return self.FAIL if not degree else tasker_result(self.FAIL, self.TASKER_EXCEPTIONAL, -100)

        margin = 3 * math.sqrt(difficulty) if not extra else extra if isinstance(extra, int) else extra[0] + extra[1] * math.sqrt(difficulty)
        if not margin:
            return self.BARF

        if bonus > difficulty + margin:
            return self.SUCCEED if not degree else tasker_result(self.SUCCEED, self.TASKER_EXCEPTIONAL, 100)

        success_margin = ((100 * (bonus - difficulty)) // margin) - random.randint(0, 99)
        if success_margin <= 0:
            if degree:
                deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                      self.TASKER_MARGINAL if -success_margin < self.TASKER_MARGINAL_UPPER else \
                      self.TASKER_NORMAL if -success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
                return tasker_result(self.FAIL, deg, success_margin)
            return self.FAIL

        adjusted_upper = upper
        if self.control:
            adjusted_upper = int(person.stat_modify(upper, skill))  # Placeholder for stat_modify
            tmp = math.exp((self.query_skill_bonus(person, skill) - self.BASE) / self.DECAY)
            adjusted_upper = int(adjusted_upper / tmp) - self.MODIFIER
            adjusted_upper = max(0, adjusted_upper)

        if random.randint(0, 99) < (adjusted_upper * (difficulty + margin - bonus)) // margin:
            res = self.AWARD
        else:
            res = self.SUCCEED

        if degree:
            deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                  self.TASKER_MARGINAL if success_margin < self.TASKER_MARGINAL_UPPER else \
                  self.TASKER_NORMAL if success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
            return tasker_result(res, deg, success_margin)
        return res

    def attempt_task_e(self, difficulty: int, bonus: int, upper: int, half: int, degree: int = 0) -> int | tasker_result:
        if bonus < difficulty:
            return self.FAIL if not degree else tasker_result(self.FAIL, self.TASKER_EXCEPTIONAL, -100)

        half = 6 * math.sqrt(difficulty) if not half else half
        if not half:
            half = 1
        fail_chance = math.exp(-0.693 * (bonus - difficulty) / half)
        success_margin = (random.randint(0, 999) - (1000 * fail_chance)) // 10

        if success_margin < 0:
            if degree:
                deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                      self.TASKER_MARGINAL if -success_margin < self.TASKER_MARGINAL_UPPER else \
                      self.TASKER_NORMAL if -success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
                return tasker_result(self.FAIL, deg, success_margin)
            return self.FAIL

        adjusted_upper = upper
        if self.control:
            adjusted_upper = int(person.stat_modify(upper, skill))  # Placeholder
            tmp = math.exp((self.query_skill_bonus(person, skill) - self.BASE) / self.DECAY)
            adjusted_upper = int(adjusted_upper / tmp) - self.E_MODIFIER
            adjusted_upper = max(0, adjusted_upper)

        if random.randint(0, 999) < (adjusted_upper * fail_chance * 10) and bonus < difficulty + (half * 5):
            res = self.AWARD
        else:
            res = self.SUCCEED

        if degree:
            deg = self.TASKER_CRITICAL if self.is_critical(success_margin) else \
                  self.TASKER_MARGINAL if success_margin < self.TASKER_MARGINAL_UPPER else \
                  self.TASKER_NORMAL if success_margin < self.TASKER_NORMAL_UPPER else self.TASKER_EXCEPTIONAL
            return tasker_result(res, deg, success_margin)
        return res

    def is_critical(self, margin: int) -> int:
        if margin < 0:
            margin = -margin
        if margin > 100:
            margin = 100
        if margin == 0:
            return 0
        return 1 if random.randint(0, 9999) < self.critical_chances[margin - 1] else 0

# Initialize taskmaster handler
taskmaster = Taskmaster()

async def init(driver_instance):
    await taskmaster.init(driver_instance)
