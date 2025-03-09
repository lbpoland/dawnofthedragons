# /mnt/home2/mud/efuns/parser.py
from ..driver import driver, Player

def query_verb() -> Optional[str]:
    """Get the last verb executed."""
    return driver.query_verb()

async def notify_fail(player: Player, msg: str) -> str:
    """Notify a player of a failed action."""
    return await driver.notify_fail(player, msg)
