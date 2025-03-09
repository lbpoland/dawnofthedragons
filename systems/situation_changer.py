# /mnt/home2/mud/systems/situation_changer.py
from typing import Dict, List, Optional, Union, Callable
from ..driver import driver, MudObject
import asyncio
import random
import time

# Constants from situations.h
WHEN_ANY_TIME = 0xFFFFFF
WHEN_WEE_HOURS = 0x000001  # 1 AM
WHEN_EARLY_MORNING = 0x00001E  # 5-6 AM
WHEN_LATE_MORNING = 0x0001E0  # 8-10 AM
WHEN_AFTERNOON = 0x01E000  # 1-5 PM
WHEN_EVENING = 0x1E0000  # 6-9 PM
WHEN_LATENIGHT = 0xE00000  # 10 PM-12 AM

class Situation:
    def __init__(self):
        self.start_func: Optional[Callable] = None
        self.end_func: Optional[Callable] = None
        self.start_mess: str = ""
        self.end_mess: str = ""
        self.extra_look: str = ""
        self.chat_rate: List[int] = [120, 240]
        self.chats: List[str] = []
        self.add_items: List[Tuple] = []
        self.random_words: List[List[str]] = []

class SituationChanger(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.room: Optional[MudObject] = None
        self.situations: Dict[Union[str, int], Situation] = {}
        self.active_situations: Dict[Union[str, int], dict] = {}
        self.automated_situations: Dict[Union[str, int], dict] = {}
        self.seed: int = hash(str(oid))  # Default seed from file_name

    def set_room(self, room: MudObject) -> 'SituationChanger':
        """Associates the changer with a room."""
        self.room = room
        return self

    def set_seed(self, xval: int, yval: int):
        """Sets a custom random seed for situation timing."""
        self.seed = hash(f"{xval}{yval}")

    def add_situation(self, label: Union[str, int], sit: Situation):
        """Adds a situation to the changer."""
        self.situations[label] = sit

    def start_situation(self, label: Union[str, int], do_start_mess: int):
        """Starts a specified situation."""
        if label not in self.situations or label in self.active_situations:
            return
        sit = self.situations[label]
        if sit.start_func:
            sit.start_func(label, do_start_mess, self.room)
        if do_start_mess and sit.start_mess:
            self.room.tell_room(sit.start_mess)
        if sit.extra_look:
            self.room.add_extra_look(sit.extra_look)
        if sit.chats:
            self.room.add_room_chats(sit.chats)
            if sit.chat_rate:
                self.room.set_chat_min_max(sit.chat_rate[0], sit.chat_rate[1])
        for item, desc in sit.add_items:
            self.room.add_item(item, desc)
        self.active_situations[label] = {"start_time": time.time()}

    def end_situation(self, label: Union[str, int]):
        """Ends a specified situation."""
        if label not in self.active_situations:
            return
        sit = self.situations[label]
        if sit.end_func:
            sit.end_func(label, self.room)
        if sit.end_mess:
            self.room.tell_room(sit.end_mess)
        if sit.extra_look:
            self.room.remove_extra_look(sit.extra_look)
        if sit.chats:
            self.room.remove_room_chats(sit.chats)
        for item, _ in sit.add_items:
            self.room.remove_item(item)
        del self.active_situations[label]

    def change_situation(self, label: Union[str, int, List], duration: Union[int, List], words: Union[int, List] = None, start: bool = True) -> Optional[int]:
        """Changes a situation with a specified duration."""
        labels = label if isinstance(label, list) else [label]
        durations = duration if isinstance(duration, list) else [duration] * len(labels)
        total_duration = sum(d for d in durations if d > 0)
        if total_duration <= 0:
            return None

        handle = driver.call_out(self._handle_situation_change, total_duration, labels, durations, words)
        if start:
            self._start_next_situation(labels, durations, words, 0)
        return handle

    def _start_next_situation(self, labels: List, durations: List, words: Union[int, List], index: int):
        """Starts the next situation in a sequence."""
        if index >= len(labels):
            return
        label = labels[index]
        if label not in self.situations:
            return
        sit = self.situations[label]
        if words and isinstance(words, list):
            for i, word_set in enumerate(sit.random_words):
                if i < len(words) // 2:
                    replacement = words[i * 2 + 1]
                    sit.start_mess = sit.start_mess.replace(f"#{i+1}", replacement)
                    sit.end_mess = sit.end_mess.replace(f"#{i+1}", replacement)
                    sit.extra_look = sit.extra_look.replace(f"#{i+1}", replacement)
                    for j, (item, desc) in enumerate(sit.add_items):
                        sit.add_items[j] = (item, desc.replace(f"#{i+1}", replacement))
                    sit.chats = [c.replace(f"#{i+1}", replacement) for c in sit.chats]
        self.start_situation(label, 1)
        if index + 1 < len(labels) and durations[index] > 0:
            driver.call_out(self._handle_situation_change, durations[index], labels, durations, words, index + 1)

    def _handle_situation_change(self, labels: List, durations: List, words: Union[int, List], next_index: int = 0):
        """Handles the transition between situations."""
        current_label = labels[next_index - 1] if next_index > 0 else labels[0]
        self.end_situation(current_label)
        if next_index < len(labels):
            self._start_next_situation(labels, durations, words, next_index)

    def automate_situation(self, label: Union[str, int, List], duration: Union[int, List], when: int = WHEN_ANY_TIME,
                          chance: int = 1000, category: str = None):
        """Automates situation start/end based on time and chance."""
        labels = label if isinstance(label, list) else [label]
        durations = duration if isinstance(duration, list) else [duration] * len(labels)
        total_duration = sum(d for d in durations if d > 0)
        if total_duration <= 0:
            return
        self.automated_situations[label] = {
            "duration": durations,
            "when": when,
            "chance": chance,
            "category": category,
            "last_check": 0
        }
        driver.call_out(self._check_automated_situation, 60, label)

    def _check_automated_situation(self, label: Union[str, int, List]):
        """Checks if an automated situation should start."""
        if label not in self.automated_situations:
            return
        config = self.automated_situations[label]
        if time.time() - config["last_check"] < 60:
            driver.call_out(self._check_automated_situation, 60, label)
            return
        hour = time.localtime().tm_hour
        if (1 << hour) & config["when"] and random.randint(0, 1000) < config["chance"]:
            if not any(s["category"] == config["category"] for s in self.active_situations.values()):
                self.change_situation(label, config["duration"])
        config["last_check"] = time.time()
        driver.call_out(self._check_automated_situation, 60, label)

    def shutdown_all_situations(self):
        """Shuts down all active and automated situations."""
        for label in list(self.active_situations.keys()):
            self.end_situation(label)
        self.automated_situations.clear()

    def shutdown_situation(self, call: int, label: Union[str, int, List]):
        """Shuts down a specific situation based on call_out handle."""
        if call:
            driver.remove_call_out(call)
        if isinstance(label, list):
            for l in label:
                self.end_situation(l)
        else:
            self.end_situation(label)

    def check_situations(self):
        """Checks and updates active situations."""
        for label, data in list(self.active_situations.items()):
            if time.time() - data["start_time"] >= sum(d for d in self.situations[label].chat_rate if d > 0):
                self.end_situation(label)

    def dest_me(self):
        """Destroys the situation changer object."""
        self.shutdown_all_situations()
        self.room = None
        self.situations.clear()
        self.active_situations.clear()
        self.automated_situations.clear()
        self.destruct()

async def init(driver_instance):
    driver = driver_instance
