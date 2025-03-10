# Imported to: living.py, library.py
# Imports from: driver.py
# /mnt/home2/mud/systems/quest.py
from typing import Dict, List, Optional, Tuple, Union
from ..driver import driver, Player, MudObject
import asyncio
import time
import os

class QuestHandler:
    def __init__(self):
        self.quest_name: List[str] = [
            "veil_of_mystra", "shadows_of_menzoberranzan"  # 2025 Forgotten Realms quests
        ]
        self.quest_level: List[int] = [5, 10]  # QP values
        self.quest_title: List[str] = [
            "Veilweaver of Mystra", "Shadowbane of the Underdark"
        ]
        self.quest_story: List[str] = [
            "Restored Mystra’s weave in the Ethereal Veil.",
            "Vanquished a drow priestess in Menzoberranzan."
        ]
        self.last_done_by: List[str] = ["nobody", "nobody"]
        self.num_times_done: List[int] = [0, 0]
        self.quest_status: List[int] = [1, 1]  # 1 = active
        self.total_qp: int = sum(self.quest_level)
        self.SAVE_FILE = "/save/quests"
        self.BACKUP_FILE = "/save/quests/quests"
        self.TEXTS_DIR = "/save/quests/"
        self.load_quests()

    def load_quests(self):
        try:
            data = driver.load_object(self.SAVE_FILE)
            if data:
                self.quest_name = data.get("quest_name", [])
                self.quest_level = data.get("quest_level", [])
                self.quest_title = data.get("quest_title", [])
                self.quest_story = data.get("quest_story", [])
                self.last_done_by = data.get("last_done_by", [])
                self.num_times_done = data.get("num_times_done", [])
                self.quest_status = data.get("quest_status", [])
                self.total_qp = data.get("total_qp", 0)
            if not self.quest_name:
                self.quest_name = []
            if not self.quest_level:
                self.quest_level = []
            if not self.quest_title:
                self.quest_title = []
            if not self.quest_story:
                self.quest_story = []
            if not self.last_done_by:
                self.last_done_by = []
            if not self.num_times_done:
                self.num_times_done = []
            if not self.quest_status and self.quest_name:
                self.quest_status = [1] * len(self.quest_name)
            self.total_qp = sum(level for level, status in zip(self.quest_level, self.quest_status) if status)
        except:
            pass

    def save_quests(self):
        data = {
            "quest_name": self.quest_name,
            "quest_level": self.quest_level,
            "quest_title": self.quest_title,
            "quest_story": self.quest_story,
            "last_done_by": self.last_done_by,
            "num_times_done": self.num_times_done,
            "quest_status": self.quest_status,
            "total_qp": self.total_qp
        }
        driver.save_object(self.SAVE_FILE, data)
        driver.unguarded(lambda: os.system(f"cp {self.SAVE_FILE}.o {self.BACKUP_FILE}.{time.time()}"))

    def query_total_qp(self) -> int:
        return self.total_qp

    def add_quest(self, name: str, level: int, title: str, story: str) -> bool:
        if name in self.quest_name:
            return False
        self.quest_name.append(name)
        self.quest_level.append(level)
        self.quest_title.append(title)
        self.quest_story.append(story)
        self.last_done_by.append("nobody")
        self.num_times_done.append(0)
        self.quest_status.append(1)
        log_name = driver.this_player().name if driver.this_player() else driver.previous_object().oid
        driver.log_file("QUESTS", f"{log_name} added: {name}, {level}, {title}, {story}\n")
        self.save_quests()
        self.total_qp += level
        return True

    def change_quest_status(self, name: str) -> int:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        if temp == -1:
            return -1
        self.quest_status[temp] = 1 - self.quest_status[temp]
        self.total_qp += self.quest_level[temp] if self.quest_status[temp] else -self.quest_level[temp]
        self.save_quests()
        return self.quest_status[temp]

    def query_quest_status(self, name: str) -> int:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return -1 if temp == -1 else self.quest_status[temp]

    def query_quest_level(self, name: str) -> int:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return -1 if temp == -1 else self.quest_level[temp]

    def set_quest_level(self, name: str, level: int) -> bool:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        if temp == -1:
            return False
        log_name = driver.this_player().name if driver.this_player() else driver.previous_object().oid
        driver.log_file("QUESTS", f"{log_name} : level set for {name} to {level}\n")
        self.total_qp += level - self.quest_level[temp] if self.quest_status[temp] else 0
        self.quest_level[temp] = level
        self.save_quests()
        return True

    def query_quest_story(self, name: str) -> str:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return "did nothing" if temp == -1 else self.quest_story[temp]

    def set_quest_story(self, name: str, story: str) -> bool:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        if temp == -1:
            return False
        log_name = driver.this_player().name if driver.this_player() else driver.previous_object().oid
        driver.log_file("QUESTS", f"{log_name} : story set for {name} to {story}\n")
        self.quest_story[temp] = story
        self.save_quests()
        return True

    def query_quest_title(self, name: str) -> str:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return "Unknown Quester" if temp == -1 or not self.quest_title[temp] else self.quest_title[temp]

    def set_quest_title(self, name: str, title: str) -> bool:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        if temp == -1:
            return False
        log_name = driver.this_player().name if driver.this_player() else driver.previous_object().oid
        driver.log_file("QUESTS", f"{log_name} : title set for {name} to {title}\n")
        self.quest_title[temp] = title
        self.save_quests()
        return True

    def query_quest_times(self, name: str) -> int:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return -1 if temp == -1 else self.num_times_done[temp]

    def query_quest_done(self, name: str) -> Union[str, int]:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        return -1 if temp == -1 else self.last_done_by[temp]

    def delete_quest(self, name: str) -> bool:
        temp = self.quest_name.index(name) if name in self.quest_name else -1
        if temp == -1:
            return False
        log_name = driver.this_player().name if driver.this_player() else driver.previous_object().oid
        driver.log_file("QUESTS", f"{log_name} removed : {name}\n")
        self.total_qp -= self.quest_level[temp]
        for attr in [self.quest_name, self.quest_level, self.quest_title, self.quest_story, self.last_done_by, self.num_times_done, self.quest_status]:
            attr.pop(temp)
        self.save_quests()
        return True

    def query_quest_names(self) -> List[str]:
        return self.quest_name.copy()

    def query_quest_levels(self) -> List[int]:
        return self.quest_level.copy()

    def query_quest_titles(self) -> List[str]:
        return self.quest_title.copy()

    def query_quest_stories(self) -> List[str]:
        return self.quest_story.copy()

    def quest_completed(self, name: str, quest: str, prev_ob: MudObject):
    temp = self.quest_name.index(quest) if quest in self.quest_name else -1
    if temp == -1:
        driver.log_file("QUESTS", f"{time.ctime()} {name} tried non-existent quest {quest}\n")
        return
    self.last_done_by[temp] = name
    self.num_times_done[temp] += 1
    self.save_quests()
    driver.log_file("QUESTS", f"{time.ctime()} {name} completed {quest} (given by {prev_ob.name or prev_ob.oid})\n")
    driver.user_event("inform", f"{name} has earned the title '{self.quest_title[temp]}'!", "quest")
    player = driver.find_player(name)
    if player:
        player.attrs.setdefault("titles", []).append(self.quest_title[temp])
        player.attrs["qp"] = player.attrs.get("qp", 0) + self.quest_level[temp]  # 2025 QP tracking
        driver.save_object(player)

    def query_player_fame(self, name: str) -> int:
    if not name or not driver.player_handler.test_user(name):
        return 0
    player_qp = driver.library.query_quest_points(name)
    total_qp = max(1, self.query_total_qp())  # Avoid division by zero
    return min(100, (player_qp * 150) // total_qp)  # 2025 fame cap at 100

    def query_fame_str(self, name: str) -> str:
        fame = self.query_player_fame(name)
        ranges = [(0, 4, "completely unknown"), (5, 14, "unknown"), (15, 24, "unknown"),
                  (25, 34, "moderately well known"), (35, 44, "well known"), (45, 54, "very well known"),
                  (55, 64, "known throughout the region"), (65, 74, "famous"), (75, 84, "renowned"),
                  (85, 94, "Disc renowned"), (95, 100, "so renowned that no introduction is needed")]
        for low, high, desc in ranges:
            if low <= fame <= high:
                return desc
        return "so renowned that no introduction is needed"

    def query_player_story(self, name: str) -> List[str]:
        if not name or not driver.player_handler.test_user(name):
            return []
        quests = self.query_quest_names()
        story = ["Is an under achiever."] if len(quests) == 1 else []
        for quest in quests:
            if driver.library.query_quest_done(name, quest):
                story.insert(0, self.query_quest_story(quest))
        return story

    def print_some_stats(self):
        for i in range(len(self.quest_name)):
            print(f"{self.quest_name[i]}: {self.num_times_done[i]}, {self.quest_level[i]}")

quest_handler = QuestHandler()



    def query_patterns(self) -> List[Tuple[str, Callable]]:
        return [
            ("", lambda: asyncio.run(self.cmd(0, 0))),
            ("<string'player'>", lambda p: asyncio.run(self.cmd(p, 0))),
            ("<string'player'> sorted", lambda p: asyncio.run(self.cmd(p, 1)))
        ]

class QuestCommand:
    def __init__(self):
        self.names: List[str] = []
        self.makers: Dict[Player, Tuple[int, List]] = {}

    async def cmd(self, player: Optional[str] = None, sorted: bool = False) -> int:
        quests = quest_handler.query_quest_names() if not player else driver.library.query_quests(player)
        if not quests:
            await driver.add_failed_mess(f"{'No quests recorded in the Realms' if not player else f'{player} has yet to prove their legend.'}\n")
            return 0
        if sorted:
            quests.sort()
        text = f"$P$Legendary Deeds$P$\n{'Realms-wide quests' if not player else f'Deeds of {player}'} :-\n\n"
        for i, quest in enumerate(quests):
            text += f"{i+1}. {quest} ({quest_handler.query_quest_title(quest)}) {self.quest_text(quest)}\n"
        await driver.tell_object(driver.this_player(), text)
        return 1

    def quest_text(self, quest: str) -> str:
        status = quest_handler.query_quest_status(quest)
        return "(inactive)" if status == 0 else "(lost to the Veil)" if status == -1 else ""

quest_command = QuestCommand()

async def init(driver_instance):
    global driver
    driver = driver_instance
    quest_handler.load_quests()
    for player in driver.players.values():
        player.add_action("quests", lambda obj, caller, arg: asyncio.create_task(quest_command.cmd(arg.split()[0] if arg else None, "sorted" in arg)))

def quest_text(quest: str) -> str:
    return quest_command.quest_text(quest)