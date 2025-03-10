# /mnt/home2/mud/systems/guild_list.py
# Imported to: login_handler.py (optional admin command)
# Imports from: driver.py

from typing import Dict
from ..driver import driver, Player
import asyncio

async def cmd_guild_list(player: Player, arg: str) -> bool:
    """Lists guild memberships across all players."""
    if not player.attrs.get("creator", False):  # Restrict to creators
        await player.send("Only sages of the realm may view this list.\n")
        return False

    guilds: Dict[str, int] = {}
    for user in driver.users():
        if user.attrs.get("creator", False):
            continue
        guild_ob = user.query_guild()
        if not guild_ob:
            guilds["none"] = guilds.get("none", 0) + 1
        else:
            # Extract guild name from path (e.g., "/guilds/wizard" -> "wizard")
            guild = guild_ob.split("/")[-1] if "/" in guild_ob else guild_ob
            guilds[guild] = guilds.get(guild, 0) + 1

    output = "Guild memberships across Faerûn:\n"
    for guild, count in guilds.items():
        output += f"  {guild}: {count}\n"
    
    await player.send(output)
    return True

async def init(driver_instance):
    driver = driver_instance
    driver.add_command("guildlist", "", cmd_guild_list)