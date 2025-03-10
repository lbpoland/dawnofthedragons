# /mnt/home2/mud/systems/skills_cmd.py
# Imported to: living.py (player commands)
# Imports from: driver.py, skills.py

from typing import Optional
from ..driver import driver, Player
import asyncio

def bonus_to_string(bonus: int) -> str:
    if bonus < 0:
        return "incompetent"
    ranges = [(0, 50, "novice"), (51, 100, "apprentice"), (101, 200, "competent"),
              (201, 300, "proficient"), (301, 350, "skilled"), (351, 400, "adept"),
              (401, 500, "expert")]
    for low, high, label in ranges:
        if low <= bonus <= high:
            return label
    return "master"

def level_to_string(level: int) -> str:
    ranges = [(0, 15, "novice"), (16, 30, "apprentice"), (31, 45, "competent"),
              (46, 60, "proficient"), (61, 75, "skilled"), (76, 85, "adept"),
              (86, 95, "expert")]
    for low, high, label in ranges:
        if low <= level <= high:
            return label
    return "master"

async def rec_list(player: Player, skills: List[str], path: str, all: bool, lvl: int, only_leaf: bool) -> str:
    rp = player.attrs.get("role_playing", False)
    result = ""
    for skill in skills:
        full_skill = f"{path}.{skill}" if path else skill
        sk = player.skills_handler.query_skill(full_skill)
        bonus = await player.skills_handler.query_skill_bonus(player, full_skill)
        no_bonus = player.skills_handler.no_bonus.get(full_skill, False)
        children = player.skills_handler.query_immediate_children(full_skill)
        o_l = player.skills_handler.query_only_leaf(full_skill)
        
        if not (only_leaf or o_l) or (not children and (sk > 0 or (all and not player.skills_handler.only_show_if_non_zero.get(full_skill, False)))):
            if rp:
                result += f"{'| ' * (lvl - 1)}{skill:<{20 - (lvl - 1) * 2}} {bonus_to_string(bonus) if not no_bonus else level_to_string(sk):>12}\n"
            else:
                result += f"{'| ' * (lvl - 1)}{skill:<{20 - (lvl - 1) * 2}} {sk:>4} {bonus if not no_bonus else '-':>4}\n"
        
        if children and (only_leaf or o_l or all or sk > 5 * lvl):
            sub_result = await rec_list(player, children, full_skill, all, lvl + 1, only_leaf or o_l)
            if sub_result:
                if rp:
                    result += f"{'| ' * (lvl - 1)}{skill:<{20 - (lvl - 1) * 2}}\n{sub_result}"
                else:
                    result += f"{'| ' * (lvl - 1)}{skill:<{20 - (lvl - 1) * 2}}    -    -\n{sub_result}"

    return result

async def cmd_skills(player: Player, arg: Optional[str]) -> bool:
    rp = player.attrs.get("role_playing", False)
    result = "=" * player.query_cols() + "\n"
    result += f"{'SKILLS'.center(20)} {'Proficiency' if rp else 'Level/Bonus'}\n"
    result += "=" * player.query_cols() + "\n"
    
    top_skills = [s for s in STAT_BONUS.keys() if "." not in s]
    if arg and arg in STAT_BONUS:
        skills = player.skills_handler.query_immediate_children(arg)
        result += await rec_list(player, skills, arg, True, 1, False)
    else:
        result += await rec_list(player, top_skills, "", arg == "all", 1, False)
    
    await player.send(result)
    return True

async def init(driver_instance):
    driver = driver_instance
    driver.add_command("skills", "", lambda p, _: cmd_skills(p, None))
    driver.add_command("skills", "<word'skill'>", cmd_skills)