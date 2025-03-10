from typing import Dict
from ..driver import MudObject
from . import effects

async def fireball_effect(caster: MudObject, target: MudObject):
    damage = sum(random.randint(1, 6) for _ in range(6))
    target.hp -= damage
    await target.environment.tell_room(f"A fireball explodes, searing {target.short()} for {damage} damage!\n")

spell_list: Dict[str, Dict] = {
    "Fireball": {
        "cost": 30,
        "skills": {"magic.evocation": 50},
        "difficulty": 75,
        "stages": [
            {"name": "focus", "time": 1, "skill": "magic.evocation", "skill_min": 25, "success": "You channel fiery intent.\n", "fail": "The spark fizzles in your mind.\n"},
            {"name": "release", "time": 1, "skill": "magic.evocation", "skill_min": 50, "success": "Flames roar from your hands!\n", "fail": "The fire sputters out.\n"},
        ],
        "effect": fireball_effect,
        "school": "evocation",
        "level": 3,
    },
    "Shield": {
        "cost": 15,
        "skills": {"magic.abjuration": 25},
        "difficulty": 40,
        "stages": [
            {"name": "ward", "time": 0.5, "skill": "magic.abjuration", "skill_min": 25, "success": "A barrier forms before you.\n", "fail": "The ward collapses.\n"},
        ],
        "effect": lambda c, t: c.add_effect(effects.Effect("shielded", duration=60, strength=4)),
        "school": "abjuration",
        "level": 1,
    },
    # Add 300+ spells from https://forgottenrealms.fandom.com/wiki/Category:Spells & Spells_by_class
    # Example: "Magic Missile", "Etherealness", "Wish" - fully sourced, staged, FR-themed
}