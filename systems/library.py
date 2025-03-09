# /mnt/home2/mud/systems/library.py
from typing import Dict, List, Optional
from ..driver import driver, Player, MudObject
import asyncio
import os

class Library:
    def __init__(self):
        self.SAVE_FILE = "/save/library"
        self.player_quests: Dict[str, List[str]] = {}
        self.load_library()

    def load_library(self):
        try:
            data = driver.load_object(self.SAVE_FILE)
            if data:
                self.player_quests = data.get("player_quests", {})
        except:
            self.player_quests = {}

    def save_library(self):
        data = {"player_quests": self.player_quests}
        driver.save_object(self.SAVE_FILE, data)

    def query_quest_points(self, name: str) -> int:
        if not name or not driver.player_handler.test_user(name):
            return 0
        return sum(quest_handler.query_quest_level(q) for q in self.query_quests(name) if q in quest_handler.query_quest_names())

    def query_quests(self, name: str) -> List[str]:
        if not name or not driver.player_handler.test_user(name):
            return []
        return self.player_quests.get(name, [])

    def query_quest_done(self, name: str, quest: str) -> bool:
        if not name or not driver.player_handler.test_user(name) or quest not in quest_handler.query_quest_names():
            return False
        return quest in self.player_quests.get(name, [])

    def record_quest_completion(self, name: str, quest: str):
        if not name or not driver.player_handler.test_user(name) or quest not in quest_handler.query_quest_names():
            return
        if quest not in self.player_quests.get(name, []):
            self.player_quests.setdefault(name, []).append(quest)
            self.save_library()
            quest_handler.quest_completed(name, quest, driver.previous_object())

library = Library()

async def init(driver_instance):
    driver = driver_instance
    # No player actions needed for library, handled via quest_handler

# Ensure quest_handler uses library for completions
from .quest import quest_handler
quest_handler.quest_completed = lambda name, quest, prev_ob: library.record_quest_completion(name, quest)
