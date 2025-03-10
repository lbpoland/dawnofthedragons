# /mnt/home2/mud/systems/movement.py
# Imported to: rooftop.py, living.py, room.py
# Imports from: driver.py, taskmaster.py

from typing import Optional, Union
from ..driver import driver, MudObject, Player
import asyncio
import random

# Constants from movement-related files (e.g., rooftop.c)
ROCK = "other.movement.climbing.rock"
WALK_SPEED = 2  # Base seconds per move
RUN_SPEED = 1  # Faster for running (2025 update)

class Movement:
    def __init__(self):
        self.move_speed: int = WALK_SPEED
        self.last_move: int = 0  # Timestamp of last move
        self.move_delay: int = 0  # Additional delay from conditions

    def setup(self, obj: MudObject):
        """Sets up movement attributes on an object."""
        obj.move_speed = self.move_speed
        obj.last_move = self.last_move
        obj.move_delay = self.move_delay

    async def move(self, obj: MudObject, dest: Union[str, MudObject], enter_mess: str = "", exit_mess: str = "") -> bool:
        """Handles movement to a destination."""
        if not obj.query_living():
            return await self.move_object(obj, dest, enter_mess, exit_mess)

        current_time = int(time.time())
        if current_time < self.last_move + self.move_speed + self.move_delay:
            if isinstance(obj, Player):
                await obj.send("You’re still catching your breath!\n")
            return False

        dest_obj = dest if isinstance(dest, MudObject) else driver.load_object(dest)
        if not dest_obj:
            if isinstance(obj, Player):
                await obj.send("The Weave denies your path—destination unknown.\n")
            return False

        env = obj.environment()
        if env and not env.test_remove(obj, 0, dest_obj):
            return False
        if not dest_obj.test_add(obj, 0):
            return False

        # Skill check for difficult terrain (2025 update)
        if dest_obj.query_property("terrain_difficulty"):
            result = driver.tasker.perform_task(obj, ROCK, dest_obj.query_property("terrain_difficulty"))
            if result == driver.tasker.FAIL:
                await obj.send("The terrain resists your passage!\n")
                self.move_delay += 1
                return False

        self.last_move = current_time
        await self.execute_move(obj, dest_obj, enter_mess, exit_mess)
        return True

    async def move_object(self, obj: MudObject, dest: Union[str, MudObject], enter_mess: str, exit_mess: str) -> bool:
        """Moves non-living objects."""
        dest_obj = dest if isinstance(dest, MudObject) else driver.load_object(dest)
        if not dest_obj:
            return False

        env = obj.environment()
        if env and not env.remove_inventory(obj):
            return False
        if not dest_obj.add_inventory(obj):
            return False

        await self.execute_move(obj, dest_obj, enter_mess, exit_mess)
        return True

    async def execute_move(self, obj: MudObject, dest: MudObject, enter_mess: str, exit_mess: str):
        """Executes the move and notifies environments."""
        env = obj.environment()
        if env:
            env.remove_inventory(obj)
            if exit_mess:
                await env.tell_room(driver.convert_message(exit_mess, obj))
        dest.add_inventory(obj)
        obj.attrs["env"] = dest.oid
        if enter_mess:
            await dest.tell_room(driver.convert_message(enter_mess, obj))
        
        # Forgotten Realms flair (2025)
        if isinstance(obj, Player) and dest.query_property("mystra_blessing"):
            await obj.send("Mystra’s grace guides your steps.\n")

    async def move_with_look(self, obj: MudObject, dest: Union[str, MudObject], enter_mess: str = "", exit_mess: str = "") -> bool:
        """Moves and triggers a look command for players."""
        success = await self.move(obj, dest, enter_mess, exit_mess)
        if success and isinstance(obj, Player):
            await obj.send(await dest.long())
        return success

    def set_move_speed(self, speed: int):
        """Sets the base movement speed."""
        self.move_speed = max(1, speed)

    def query_move_speed(self) -> int:
        """Returns the current move speed with delay."""
        return self.move_speed + self.move_delay

    def adjust_move_delay(self, delay: int):
        """Adjusts the movement delay (e.g., from fatigue)."""
        self.move_delay = max(0, self.move_delay + delay)

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Movement is a mixin class for objects like Living and Rooftop