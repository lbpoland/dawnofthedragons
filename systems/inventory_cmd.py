# /mnt/home2/mud/systems/inventory_cmd.py
# Imported to: living.py (player commands)
# Imports from: driver.py

from typing import List
from ..driver import driver, Player
import asyncio

async def cmd_inventory(player: Player, arg: str) -> bool:
    """Displays the player's inventory with burden info."""
    if player.query_property("dead"):
        await player.send("As a spirit, you drift with naught but mist.\n")
        dead_usable = [item for item in player.query_carried() if item.query_property("dead usable")]
        if dead_usable:
            await player.send(f"Yet, strangely, you clutch {driver.multiple_short(dead_usable)}.\n")
        return True

    burden = player.burden_string()  # Assumes living.py has this method
    contents = await player.list_inventory(player, player)
    await player.send(f"You are {burden} by:\n{contents}")

    if player.query_auto_loading():
        await player.send("\n\033[33mNote: Your inventory is still forming in the Weave.\033[0m\n")
    return True

async def init(driver_instance):
    driver = driver_instance
    driver.add_command("inventory", "", cmd_inventory)
    driver.add_alias("inv", "inventory")