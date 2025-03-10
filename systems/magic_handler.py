from typing import Optional, Dict
from ..driver import driver, MudObject
import asyncio
from . import spells, effects, skills

class MagicHandler:
    def __init__(self):
        self.spells = spells.spell_list

    async def cast_spell(self, caster: MudObject, spell_name: str, target: Optional[MudObject] = None) -> bool:
        spell = self.spells.get(spell_name)
        if not spell:
            await caster.send("That spell eludes the Veil’s grasp.\n")
            return False
        
        # Skill check and mana cost from Discworld design
        total_skill = sum(caster.query_skill(s) for s in spell["skills"])
        if total_skill < spell["difficulty"]:
            await caster.send(f"Your grasp on {spell_name} falters—arcane knowledge insufficient.\n")
            return False
        if caster.gp < spell["cost"]:
            await caster.send("The Ethereal Veil denies you—too little power remains.\n")
            return False
        
        # Stage-based casting from Sekiri/Discworld
        for stage in spell["stages"]:
            await asyncio.sleep(stage["time"])
            skill_check = caster.query_skill(stage["skill"]) >= stage["skill_min"]
            message = stage["success" if skill_check else "fail"]
            await caster.send(message)
            if not skill_check:
                driver.log_file("MAGIC", f"{caster.name} failed {spell_name} at {stage['name']}.\n")
                return False
        
        # Apply spell
        caster.gp -= spell["cost"]
        spell["effect"](caster, target)
        await caster.environment.tell_room(f"{caster.short()} unleashes {spell_name}, the Veil shimmering!\n")
        driver.log_file("MAGIC", f"{caster.name} cast {spell_name} on {target.short() if target else 'none'}.\n")
        return True

    def learn_spell(self, player: MudObject, spell_name: str) -> bool:
        spell = self.spells.get(spell_name)
        if not spell or spell_name in player.spells:
            return False
        if all(player.query_skill(s) >= spell["skills"].get(s, 0) for s in spell["skills"]):
            player.spells.append(spell_name)
            return True
        return False

    def query_spell(self, spell_name: str) -> Optional[Dict]:
        return self.spells.get(spell_name)

magic_handler = MagicHandler()