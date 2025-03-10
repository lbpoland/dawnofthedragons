from typing import Dict
from ..driver import MudObject
from . import effects

async def cure_light_wounds_effect(caster: MudObject, target: MudObject):
    healing = random.randint(1, 8) + 1 + (caster.piety // 20)
    target.hp = min(target.max_hp, target.hp + healing)
    await target.send(f"Ilmater’s mercy heals you for {healing}!\n")

ritual_list: Dict[str, Dict] = {
    "Cure Light Wounds": {
        "cost": 10,
        "skills": {"faith.rituals.healing": 25},
        "difficulty": 40,
        "stages": [
            {"name": "prayer", "time": 1, "skill": "faith.rituals.healing", "skill_min": 25, "success": "You beseech Ilmater’s aid.\n", "fail": "Your plea goes unheard.\n"},
        ],
        "effect": cure_light_wounds_effect,
        "deity": "Ilmater",
        "favor_gain": 5,
    },
    "Bless": {
        "cost": 15,
        "skills": {"faith.rituals.good": 30},
        "difficulty": 50,
        "stages": [
            {"name": "invoke", "time": 1, "skill": "faith.rituals.good", "skill_min": 30, "success": "Selûne’s light blesses you.\n", "fail": "The light dims.\n"},
        ],
        "effect": lambda c, t: t.add_effect(effects.Effect("blessed", duration=60, strength=1)),
        "deity": "Selûne",
        "favor_gain": 5,
    },
    # Add 20+ from https://forgottenrealms.fandom.com/wiki/Category:Rituals - e.g., "Analyze Portal", "Simbul’s Conversion"
}