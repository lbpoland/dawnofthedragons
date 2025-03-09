# /mnt/home2/mud/efuns/skills.py
from ..driver import driver, Player

async def teach(player: Player, target: str, skill: str):
    """Teach a skill to another player."""
    target_obj = None
    for p in driver.players.values():
        if p.name.lower() == target.lower():
            target_obj = p
            break
    if not target_obj:
        await player.send(f"No one named {target} is online.")
        return
    if skill not in player.attrs.get("skills", {}):
        await player.send(f"You don’t know the skill {skill}!")
        return
    target_obj.attrs.setdefault("skills", {})[skill] = player.attrs["skills"][skill]
    await target_obj.send(f"{player.name} teaches you {skill}!")
    await player.send(f"You teach {target} the skill {skill}.")

async def learn(player: Player, skill: str, teacher: str):
    """Learn a skill from a teacher."""
    teacher_obj = None
    for p in driver.players.values():
        if p.name.lower() == teacher.lower():
            teacher_obj = p
            break
    if not teacher_obj:
        await player.send(f"No one named {teacher} is online.")
        return
    if skill not in teacher_obj.attrs.get("skills", {}):
        await player.send(f"{teacher} doesn’t know the skill {skill}!")
        return
    player.attrs.setdefault("skills", {})[skill] = teacher_obj.attrs["skills"][skill]
    await player.send(f"You learn {skill} from {teacher}!")
    await teacher_obj.send(f"{player.name} learns {skill} from you!")

async def advance(player: Player, skill: str, level: int):
    """Advance a skill to a new level."""
    if skill not in player.attrs.get("skills", {}):
        await player.send(f"You don’t know the skill {skill}!")
        return
    player.attrs["skills"][skill] = level
    await player.send(f"You advance your {skill} to level {level}!")
