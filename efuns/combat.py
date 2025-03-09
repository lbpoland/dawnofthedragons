# /mnt/home2/mud/efuns/combat.py
from ..driver import driver, Player, MudObject

async def kill(player: Player, target: str):
    """Initiate combat with a target."""
    if not player.location:
        await player.send("You are nowhere to fight!")
        return
    contents = player.location.attrs.get("contents", [])
    target_obj = None
    for oid in contents:
        if oid in driver.objects and driver.objects[oid].name.lower() == target.lower():
            target_obj = driver.objects[oid]
            break
    if not target_obj:
        await player.send(f"No {target} here to fight!")
        return
    await player.send(f"You attack {target_obj.name}!")
    await driver.call_other(target_obj.oid, "receive_attack", player, None)

async def tactics(player: Player, strategy: str):
    """Set combat tactics (offensive, defensive, balanced)."""
    valid_strategies = ["offensive", "defensive", "balanced"]
    if strategy not in valid_strategies:
        await player.send(f"Invalid tactic! Choose: {', '.join(valid_strategies)}")
        return
    player.attrs["tactics"] = strategy
    await player.send(f"You set your tactics to {strategy}.")
