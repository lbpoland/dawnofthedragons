# /mnt/home2/mud/efuns/tools.py
from ..driver import driver, Player

async def profile(func: Callable, *args):
    """Profile a function’s performance."""
    await driver.profile(func, *args)

async def cluster_sync():
    """Synchronize state across a cluster (placeholder)."""
    # Future: Implement Redis pub/sub for clustering
    driver.redis.publish("mud_sync", json.dumps(driver.mud_status()))

async def mount(player: Player, mount: str):
    """Mount a creature for faster movement."""
    mount_obj = None
    for oid in player.location.attrs.get("contents", []):
        if oid in driver.objects and driver.objects[oid].name.lower() == mount.lower():
            mount_obj = driver.objects[oid]
            break
    if not mount_obj:
        await player.send(f"No {mount} here to mount!")
        return
    player.attrs["mount"] = mount_obj.oid
    await player.send(f"You mount the {mount}!")

async def flag_pk(player: Player, status: bool):
    """Flag a player for PK in raid zones."""
    player.pk_flagged = status
    await player.send(f"You are now {'PK-flagged' if status else 'not PK-flagged'}.")

async def pledge_house(player: Player, house: str):
    """Pledge allegiance to a noble house."""
    house_obj = None
    for oid in driver.objects:
        if driver.objects[oid].name.lower() == house.lower():
            house_obj = driver.objects[oid]
            break
    if not house_obj:
        await player.send(f"No house named {house} exists!")
        return
    player.attrs["house"] = house_obj.oid
    await player.send(f"You pledge allegiance to {house}!")
