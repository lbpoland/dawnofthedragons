from typing import Optional, Dict
from ..driver import driver, MudObject
import asyncio
from . import rituals, deity_handler, effects, skills

class RitualsHandler:
    def __init__(self):
        self.rituals = rituals.ritual_list

    async def perform_ritual(self, player: MudObject, ritual_name: str, target: Optional[MudObject] = None) -> bool:
        ritual = self.rituals.get(ritual_name)
        if not ritual:
            await player.send("No such prayer echoes in the divine realms.\n")
            return False
        
        if player.faith < ritual["cost"]:
            await player.send("Your faith wavers—too weak to call the divine.\n")
            return False
        if not deity_handler.check_deity_approval(player, ritual):
            await player.send(f"{player.deity} turns away from your plea.\n")
            return False
        
        # Stage-based from Discworld/Sekiri
        total_skill = sum(player.query_skill(s) for s in ritual["skills"])
        if total_skill < ritual["difficulty"]:
            await player.send(f"Your faith falters before {ritual_name}.\n")
            return False
        
        for stage in ritual["stages"]:
            await asyncio.sleep(stage["time"])
            skill_check = player.query_skill(stage["skill"]) >= stage["skill_min"]
            message = stage["success" if skill_check else "fail"]
            await player.send(message)
            if not skill_check:
                driver.log_file("FAITH", f"{player.name} failed {ritual_name} at {stage['name']}.\n")
                return False
        
        # Apply ritual
        player.faith -= ritual["cost"]
        ritual["effect"](player, target)
        await player.environment.tell_room(f"{player.short()} invokes {ritual_name}, divine power surging!\n")
        deity_handler.adjust_favor(player, ritual["favor_gain"], f"Performed {ritual_name}")
        return True

    def learn_ritual(self, player: MudObject, ritual_name: str) -> bool:
        ritual = self.rituals.get(ritual_name)
        if not ritual or ritual_name in player.rituals:
            return False
        if deity_handler.check_deity_approval(player, ritual) and all(player.query_skill(s) >= ritual["skills"].get(s, 0) for s in ritual["skills"]):
            player.rituals.append(ritual_name)
            return True
        return False

rituals_handler = RitualsHandler()