# /mnt/home2/mud/systems/classes.py
from typing import Dict, List, Optional, Tuple
from ..driver import driver, Player, MudObject
import asyncio

class ClassHandler:
    # Rethemed Discworld guilds to Forgotten Realms classes
    CLASSES: Dict[str, Dict] = {
        "Fighter": {
            "skill_bonuses": {"fighting.combat.melee": 10, "fighting.combat.tactics": 5},
            "description": "A master of martial combat.",
            "commands": ["strike"],
            "max_level": 300
        },
        "Rogue": {
            "skill_bonuses": {"covert.manipulation.stealing": 10, "fighting.combat.dodge": 5},
            "description": "A stealthy trickster adept at sneaking.",
            "commands": ["sneak", "steal"],
            "max_level": 300
        },
        "Mage": {
            "skill_bonuses": {"magic.spellcasting": 10, "other.perception": 5},
            "description": "A wielder of arcane magic.",
            "commands": ["cast"],
            "max_level": 300
        },
        "Cleric": {
            "skill_bonuses": {"magic.spellcasting": 5, "fighting.combat.parry": 5},
            "description": "A divine servant channeling divine power.",
            "commands": ["heal"],
            "max_level": 300
        }
    }

    def __init__(self):
        self.classes: Dict[str, List[MudObject]] = {}  # Class name to list of members

    async def init(self, driver_instance):
        self.driver = driver_instance
        for player in driver.players:
            player.add_action("class", self.class_command)
            player.add_action("party", self.party_command)

    # Class Methods (retaining Discworld guild mechanics)
    async def class_command(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player) or caller.oid != obj.oid:
            return "Only players can manage their class."
        args = arg.lower().split()
        if not args:
            return self.display_classes(caller)
        command = args[0]
        if command == "join":
            if len(args) < 2:
                return "Syntax: class join <class_name>"
            return await self.join_class(caller, args[1])
        elif command == "leave":
            return await self.leave_class(caller)
        elif command == "info":
            return self.display_classes(caller)
        return "Syntax: class [join|leave|info] [class_name]"

    async def join_class(self, player: Player, class_name: str) -> str:
        class_name = class_name.capitalize()
        if class_name not in self.CLASSES:
            return f"Unknown class '{class_name}'. Available classes: {', '.join(self.CLASSES.keys())}"
        if player.attrs.get("class"):
            return "You must leave your current class before joining another."
        if not await self.check_join_requirements(player, class_name):
            return "You do not meet the requirements to join this class."
        self.classes.setdefault(class_name, []).append(player)
        player.attrs["class"] = class_name
        player.attrs["class_level"] = 1
        self.apply_class_bonuses(player, class_name)
        return f"You have joined the {class_name} class! {self.CLASSES[class_name]['description']}"

    async def check_join_requirements(self, player: Player, class_name: str) -> bool:
        # Placeholder for Discworld guild-style requirements (e.g., skill levels)
        return True  # Implement specific requirements as needed

    async def leave_class(self, player: Player) -> str:
        class_name = player.attrs.get("class")
        if not class_name:
            return "You are not a member of any class."
        if not await self.check_leave_conditions(player, class_name):
            return "You cannot leave this class at this time."
        self.classes[class_name].remove(player)
        if not self.classes[class_name]:
            del self.classes[class_name]
        self.remove_class_bonuses(player, class_name)
        player.attrs.pop("class")
        player.attrs["class_level"] = 0
        return f"You have left the {class_name} class."

    async def check_leave_conditions(self, player: Player, class_name: str) -> bool:
        # Placeholder for Discworld guild-style leave conditions
        return True  # Implement specific conditions as needed

    def display_classes(self, player: Player) -> str:
        current_class = player.attrs.get("class")
        level = player.attrs.get("class_level", 0)
        output = "Available classes:\n"
        for class_name, data in self.CLASSES.items():
            output += f"  {class_name}: {data['description']} (Max Level: {data['max_level']})\n"
        if current_class:
            output += f"\nYou are a level {level} {current_class}."
        else:
            output += "\nYou are not a member of any class."
        return output

    def apply_class_bonuses(self, player: Player, class_name: str):
        bonuses = self.CLASSES[class_name]["skill_bonuses"]
        for skill, bonus in bonuses.items():
            current = player.attrs["skills"].get(skill, 0)
            player.attrs["skills"][skill] = current + bonus

    def remove_class_bonuses(self, player: Player, class_name: str):
        bonuses = self.CLASSES[class_name]["skill_bonuses"]
        for skill, bonus in bonuses.items():
            current = player.attrs["skills"].get(skill, 0)
            player.attrs["skills"][skill] = max(0, current - bonus)

    def query_class(self, player: Player) -> Optional[str]:
        return player.attrs.get("class")

    def query_class_level(self, player: Player) -> int:
        return player.attrs.get("class_level", 0)

    def set_class_level(self, player: Player, level: int):
        max_level = self.CLASSES.get(player.attrs.get("class"), {}).get("max_level", 300)
        player.attrs["class_level"] = max(1, min(max_level, level))

    def advancement_restriction(self, player: Player) -> bool:
        level = self.query_class_level(player)
        max_level = self.CLASSES.get(player.attrs.get("class"), {}).get("max_level", 300)
        return level >= max_level

    # Party Methods (retaining Discworld group mechanics)
    async def party_command(self, obj: MudObject, caller: Player, arg: str) -> str:
        if not isinstance(caller, Player) or caller.oid != obj.oid:
            return "Only players can manage parties."
        args = arg.lower().split()
        if not args:
            return self.display_party(caller)
        command = args[0]
        if command == "create":
            if len(args) < 2:
                return "Syntax: party create <party_name>"
            return await self.create_party(caller, args[1])
        elif command == "join":
            if len(args) < 2:
                return "Syntax: party join <party_name>"
            return await self.join_party(caller, args[1])
        elif command == "leave":
            return await self.leave_party(caller)
        elif command == "info":
            return self.display_party(caller)
        return "Syntax: party [create|join|leave|info] [party_name]"

    async def create_party(self, player: Player, party_name: str) -> str:
        if player.attrs.get("party"):
            return "You must leave your current party before creating a new one."
        if party_name in self.parties:
            return f"A party named '{party_name}' already exists."
        if not await self.check_party_create(player, party_name):
            return "You cannot create a party at this time."
        self.parties[party_name] = [player]
        player.attrs["party"] = party_name
        return f"You have created the party '{party_name}'."

    async def check_party_create(self, player: Player, party_name: str) -> bool:
        # Placeholder for Discworld group creation restrictions
        return True  # Implement specific restrictions as needed

    async def join_party(self, player: Player, party_name: str) -> str:
        if player.attrs.get("party"):
            return "You must leave your current party before joining another."
        if party_name not in self.parties:
            return f"No party named '{party_name}' exists."
        if not await self.check_party_join(player, party_name):
            return "You cannot join this party at this time."
        self.parties[party_name].append(player)
        player.attrs["party"] = party_name
        return f"You have joined the party '{party_name}'."

    async def check_party_join(self, player: Player, party_name: str) -> bool:
        # Placeholder for Discworld group join restrictions
        return True  # Implement specific restrictions as needed

    async def leave_party(self, player: Player) -> str:
        party_name = player.attrs.get("party")
        if not party_name:
            return "You are not a member of any party."
        if not await self.check_party_leave(player, party_name):
            return "You cannot leave this party at this time."
        self.parties[party_name].remove(player)
        if not self.parties[party_name]:
            del self.parties[party_name]
        player.attrs.pop("party")
        return f"You have left the party '{party_name}'."

    async def check_party_leave(self, player: Player, party_name: str) -> bool:
        # Placeholder for Discworld group leave conditions
        return True  # Implement specific conditions as needed

    def display_party(self, player: Player) -> str:
        party_name = player.attrs.get("party")
        if not party_name:
            return "You are not a member of any party."
        members = self.parties[party_name]
        output = f"Party '{party_name}':\n"
        for member in members:
            output += f"  {member.name} (Level {self.query_class_level(member)} {self.query_class(member)})\n"
        return output

    def share_xp(self, party_name: str, xp: int):
        if party_name not in self.parties:
            return
        members = self.parties[party_name]
        xp_per_member = xp // len(members)
        for member in members:
            member.attrs["xp"] = member.attrs.get("xp", 0) + xp_per_member

    parties: Dict[str, List[MudObject]] = {}  # Party name to list of members

class_handler = ClassHandler()

async def init(driver_instance):
    await class_handler.init(driver_instance)
