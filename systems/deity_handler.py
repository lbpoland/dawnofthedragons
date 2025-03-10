from typing import Dict, Optional
from ..driver import driver, MudObject

class DeityHandler:
    def __init__(self):
        # All deities from https://forgottenrealms.fandom.com/wiki/Category:Deities
        self.deities: Dict[str, Dict] = {
            "Mystra": {"alignment": "NG", "domains": ["Magic", "Knowledge"], "desc": "Lady of Mysteries", "rituals": ["Shield", "Simbul’s Conversion"], "favor_acts": {"cast_spell": 5}},
            "Tempus": {"alignment": "CN", "domains": ["War"], "desc": "Foehammer", "rituals": ["Wrath"], "favor_acts": {"kill": 10}},
            "Selûne": {"alignment": "CG", "domains": ["Moon", "Life"], "desc": "Moonmaiden", "rituals": ["Bless"], "favor_acts": {"aid": 5}},
            "Ilmater": {"alignment": "LG", "domains": ["Healing"], "desc": "Crying God", "rituals": ["Cure Light Wounds"], "favor_acts": {"heal": 5}},
            "Bane": {"alignment": "LE", "domains": ["Tyranny"], "desc": "Black Hand", "rituals": ["Fear"], "favor_acts": {"dominate": 10}},
            # Add 100+ from wiki - e.g., Shar, Corellon, Torm
        }

    def worship(self, player: MudObject, deity_name: str) -> bool:
        if deity_name not in self.deities:
            return False
        player.deity = deity_name
        player.favor = 0
        player.piety = 0
        player.alignment = self.align_to_value(self.deities[deity_name]["alignment"])
        return True

    def adjust_favor(self, player: MudObject, amount: int, reason: str):
        player.favor = max(-100, min(100, player.favor + amount))
        driver.log_file("FAITH", f"{player.name} gained {amount} favor with {player.deity} for {reason}.\n")

    def check_deity_approval(self, player: MudObject, ritual: Dict) -> bool:
        deity = self.deities.get(player.deity)
        return deity and ritual["deity"] == player.deity and abs(player.alignment - self.align_to_value(deity["alignment"])) < 500

    def align_to_value(self, alignment: str) -> int:
        align_map = {"LG": 1000, "NG": 500, "CG": 250, "LN": 750, "N": 0, "CN": -250, "LE": -750, "NE": -500, "CE": -1000}
        return align_map.get(alignment, 0)

deity_handler = DeityHandler()