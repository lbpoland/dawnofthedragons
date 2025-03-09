# /mnt/home2/mud/systems/chatter.py
from typing import List, Optional, Union
from ..driver import driver, MudObject
import asyncio
import random
import time

class Chatter(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.room: Optional[MudObject] = None
        self.chats: Optional[List] = None
        self.min_interval: int = 120
        self.max_interval: int = 240
        self.last_chat: float = 0

    def setup_chatter(self, room: MudObject, args: List):
        """Sets up the chatter with room and chat arguments."""
        self.room = room
        if len(args) >= 3 and isinstance(args[0], int) and isinstance(args[1], int) and isinstance(args[2], list):
            self.min_interval = args[0]
            self.max_interval = args[1]
            self.chats = args[2]
        driver.call_out(self.check_chat, random.randint(self.min_interval, self.max_interval))

    def set_chat_min_max(self, min: int, max: int):
        """Adjusts the minimum and maximum chat intervals."""
        self.min_interval = max(1, min)
        self.max_interval = max(max, self.min_interval)

    def add_room_chats(self, new_chats: List[str]):
        """Adds new chat messages to the existing list."""
        if self.chats:
            self.chats.extend(new_chats)
        else:
            self.chats = new_chats
        driver.call_out(self.check_chat, random.randint(self.min_interval, self.max_interval))

    def remove_room_chats(self, dead_chats: List[str]):
        """Removes specified chat messages."""
        if self.chats:
            self.chats = [chat for chat in self.chats if chat not in dead_chats]
            if not self.chats:
                self.dest_me()

    def query_room_chats(self) -> Optional[List]:
        """Returns the current chat messages."""
        return self.chats.copy() if self.chats else None

    async def check_chat(self):
        """Checks if it's time to send a chat message."""
        if not self.room or not self.chats or time.time() - self.last_chat < self.min_interval:
            return
        if random.random() < 0.5:  # Simplified probability check
            chat = random.choice(self.chats)
            if chat.startswith("#"):
                chat = getattr(self.room, chat[1:], lambda: "Unknown chat function")()
            self.room.tell_room(chat)
            self.last_chat = time.time()
        driver.call_out(self.check_chat, random.randint(self.min_interval, self.max_interval))

    def dest_me(self):
        """Destroys the chatter object."""
        self.room = None
        self.chats = None
        self.destruct()

async def init(driver_instance):
    driver = driver_instance
