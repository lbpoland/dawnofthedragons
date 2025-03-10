# /mnt/home2/mud/systems/guilds_foyer.py
# Imported to: room.py (as a specialized room)
# Imports from: driver.py, guild_handler.py

from typing import Dict
from ..driver import driver, MudObject
import asyncio

PATH = "/realms/faerun/"
GUILDS = "wizards, witches, thieves, assassins, warriors, priests"

class GuildsFoyer(MudObject):
    def __init__(self, oid: str = "guilds_foyer", name: str = "guilds_foyer"):
        super().__init__(oid, name)
        self.zone = "Newbie"
        self.short = "Garden of Guilds"
        self.light_level = 100
        self.properties = {"no_teleport": 1, "no_godmother": 1}  # From guilds_foyer.c
        self.exits: Dict[str, str] = {}
        self.day_long = (
            "A serene garden blooms here, adorned with trees, shrubs, and flowers of Faerûn. "
            "Six gazebos stand proudly, each with a wrought iron gate bearing a coat of arms. "
            f"These gazebos honor the guilds: {GUILDS}. "
            "To inspect a gate, use 'look wizard' or similar; to enter, type 'wizard', 'witch', etc.\n"
            "A sign stands at the garden’s heart.\n"
        )
        self.night_long = (
            "An octagonal garden glows softly under Selûne’s light, fenced and lit by braziers. "
            "Six gazebos rise, their wrought iron gates marked with guild crests. "
            f"These are dedicated to {GUILDS}. "
            "To examine a gate, use 'look witch'; to enter, type 'witch', 'wizard', etc.\n"
            "A sign rests at the center.\n"
        )
        self.items = {"gazebo": "Six gazebos stand here, each a tribute to a guild of Faerûn."}
        self.room_chats = [
            "An elderly mage in blue robes and a starry hat strides from the wizards’ gazebo southwards.",
            "A small witch in a black cloak sweeps in from the south, vanishing into the witches’ gazebo.",
            "A burly warrior, clad in armor and sword in hand, marches from the warriors’ gazebo south.",
            "A saintly priestess enters from the south, smiling gently, then heads to the priests’ gazebo.",
            "A shadowy assassin slips from the assassins’ gazebo into the foyer.",
            "A furtive thief sneaks from the thieves’ gazebo towards the foyer."
        ]

    async def setup(self):
        """Sets up the foyer with exits and sign."""
        self.add_property("no_teleport", 1)
        self.add_property("no_godmother", 1)
        self.add_exit("foyer", PATH + "foyer", "gate")
        for guild in ["witch", "wizard", "thief", "assassin", "warrior", "priest"]:
            self.add_exit(guild, PATH + f"{guild}s", "gate", {
                "look": "Darkness veils the gazebo’s interior.",
                "closed": 1,
                "door_long": self.get_door_long(guild)
            })
        self.add_item("brazier", "A torch atop a pole casts a warm glow.", night_only=True)
        self.add_sign(
            "A white sign on a post stands resolute.",
            "Each soul may join a guild to hone skills and commands, shaping their path in Faerûn. "
            "Explore these gazebos to learn of each guild’s ways. In Waterdeep, their halls await your oath.\n"
            "Choose wisely—your guild is your destiny.",
            "general"
        )
        self.set_chat_min_max(60, 120)

    def get_door_long(self, guild: str) -> str:
        """Returns guild-specific gate descriptions with Forgotten Realms flair."""
        return {
            "witch": "A broomstick with a clinging cat is etched above this gate, hinting at wild magic.",
            "wizard": "The crest of Candlekeep adorns this gate—a starry hat and book with 'Nunc Id Vides'.",
            "thief": "A slashed purse spills coins on this gate, marked 'Actus Id Verberat' in shadow.",
            "assassin": "A cloak and dagger grace this gate, with gold crosses and 'Nil Mortifi Sine Lucre'.",
            "warrior": "A bloody skull and scythe mark this gate: 'If It Moves, Slay It' echoes in steel.",
            "priest": "Symbols of Mystra—fluff jars to sacred monkeys—dance across this holy gate."
        }.get(guild, "A simple gate stands here.")

    def query_light(self) -> int:
        """Ensures light never drops below 40 (guilds_foyer.c)."""
        light = super().query_light()
        return max(40, light)

async def init(driver_instance):
    driver = driver_instance
    foyer = GuildsFoyer()
    await foyer.setup()
    driver.add_object(foyer)