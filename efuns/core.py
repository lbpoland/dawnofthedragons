# /mnt/home2/mud/efuns/core.py
from typing import Any, Callable, Optional
from ..driver import driver, Player, MudObject

async def write(player: Player, msg: str):
    """Write a message to a player."""
    await player.send(msg)

async def call_out(delay: float, func: Callable, *args):
    """Schedule a function to run after a delay."""
    await driver.call_out(delay, func, *args)

def add_action(obj: MudObject, verb: str, func: Callable):
    """Bind a verb to an action on an object."""
    obj.add_action(verb, func)

def move_object(obj: MudObject, destination: Optional[MudObject]):
    """Move an object to a new location."""
    if obj.location:
        obj.location.attrs.get("contents", []).remove(obj.oid)
    obj.location = destination
    if destination:
        contents = destination.attrs.get("contents", [])
        contents.append(obj.oid)
        destination.attrs["contents"] = contents
    driver.save_object(obj)
    if destination:
        driver.save_object(destination)

async def call_other(oid: str, verb: str, caller: Player, arg: str = None) -> str:
    """Call a verb on another object."""
    return await driver.call_other(oid, verb, caller, arg)

def this_object() -> Optional[MudObject]:
    """Return the current object in the call stack."""
    return driver.this_object()

def previous_object() -> Optional[MudObject]:
    """Return the previous object in the call stack."""
    return driver.previous_object()

def clone_object(obj: MudObject) -> MudObject:
    """Clone an object."""
    return obj.clone()

def destruct(obj: MudObject):
    """Destroy an object."""
    obj.destruct()

def map_array(arr: list, func: Callable) -> list:
    """Map a function over an array."""
    return list(map(func, arr))

def filter_array(arr: list, func: Callable) -> list:
    """Filter an array with a function."""
    return list(filter(func, arr))

async def catch(func: Callable, *args) -> tuple[Any, Optional[str]]:
    """Catch errors in a function call."""
    try:
        result = await func(*args)
        return result, None
    except Exception as e:
        return None, str(e)

def shadow(obj: MudObject, func: Callable):
    """Shadow an object's method with a new function."""
    # Simplified shadowing - extend as needed
    obj.actions["shadowed"] = func

def seteuid(obj: MudObject, euid: str):
    """Set the effective user ID of an object."""
    driver.seteuid(obj, euid)

def geteuid(obj: MudObject) -> str:
    """Get the effective user ID of an object."""
    return driver.geteuid(obj)

async def read_file(path: str) -> str:
    """Read a file asynchronously."""
    return await driver.read_file(path)

async def write_file(path: str, content: str):
    """Write to a file asynchronously."""
    await driver.write_file(path, content)

def uptime() -> int:
    """Return the driver's uptime in seconds."""
    return driver.uptime()
