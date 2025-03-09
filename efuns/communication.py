# /mnt/home2/mud/efuns/communication.py
from ..driver import driver, Player, MudObject

async def say(player: Player, msg: str):
    """Say a message to all in the room."""
    if not player.location:
        await player.send("You are nowhere to say anything!")
        return
    contents = player.location.attrs.get("contents", [])
    for oid in contents:
        if oid in driver.objects and oid != player.oid:
            await driver.call_other(oid, "receive_message", player, f"{player.name} says: {msg}")
    await player.send(f"You say: {msg}")

async def emote(player: Player, msg: str):
    """Perform an emote visible to all in the room."""
    if not player.location:
        await player.send("You are nowhere to emote!")
        return
    contents = player.location.attrs.get("contents", [])
    for oid in contents:
        if oid in driver.objects:
            await driver.call_other(oid, "receive_message", player, f"{player.name} {msg}")
    await player.send(f"You emote: {player.name} {msg}")

async def tell(player: Player, target: str, msg: str):
    """Send a private message to another player."""
    target_obj = None
    for p in driver.players.values():
        if p.name.lower() == target.lower():
            target_obj = p
            break
    if not target_obj:
        await player.send(f"No one named {target} is online.")
        return
    await target_obj.send(f"{player.name} tells you: {msg}")
    await player.send(f"You tell {target}: {msg}")

async def shout(player: Player, msg: str):
    """Shout a message to all players."""
    for p in driver.players.values():
        await p.send(f"{player.name} shouts: {msg}")
