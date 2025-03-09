# /mnt/home2/mud/efuns/network.py
from ..driver import driver, Player

def socket_create(mode: str, callback: Callable) -> int:
    """Create a socket (placeholder - extend for actual socket use)."""
    # Future: Implement actual socket creation
    return 0

def query_ip_number(player: Player) -> str:
    """Get the IP address of a player."""
    return player.ip_address

def query_idle(player: Player) -> int:
    """Get the idle time of a player in seconds."""
    return int(time.time() - player.last_active)
