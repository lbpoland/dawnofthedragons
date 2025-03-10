# Imported to: rooftop.py, room.py
# Imports from: driver.py
# /mnt/home2/mud/systems/wall.py
from typing import List, Optional, Union, Tuple
from ..driver import driver, MudObject, Player

class Wall(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.belows: List[str] = []  # Paths to rooms below
        self.bottom: Optional[Union[str, List]] = None  # Destination when falling
        self.ghost_action: Optional[Union[str, List]] = None  # Action for ghosts
        self.moves: List = []  # Movement data (e.g., ["up", "mess", "dest"])
        self.no_drop: int = 0  # Flag to prevent dropping objects
        self.death_mess: Optional[str] = None  # Custom death message
        self.old_here: Optional[str] = None  # Original "here" property
        self.room: Optional[MudObject] = None

    def setup_shadow(self, thing: MudObject):
        """Sets up the wall shadow on the given room."""
        self.room = thing

    def destruct_shadow(self):
        """Destroys the wall shadow and cleans up."""
        if self.room:
            if self.old_here:
                self.room.add_property("here", self.old_here)
            else:
                self.room.remove_property("here")
        self.room = None
        self.destruct()

    def query_belows(self) -> List[str]:
        """Returns the list of rooms below."""
        return self.belows.copy()

    def query_bottom(self) -> Optional[Union[str, List]]:
        """Returns the bottom destination."""
        return self.bottom.copy() if isinstance(self.bottom, list) else self.bottom

    def query_ghost_action(self) -> Optional[Union[str, List]]:
        """Returns the ghost action."""
        return self.ghost_action.copy() if isinstance(self.ghost_action, list) else self.ghost_action

    def query_moves(self) -> List:
        """Returns the movement data."""
        return self.moves.copy()

    def query_no_drop(self) -> int:
        """Returns the no_drop flag."""
        return self.no_drop

    def query_death_mess(self) -> Optional[str]:
        """Returns the custom death message."""
        return self.death_mess

    def query_at_bottom(self) -> bool:
        """Checks if the wall is at the bottom."""
        return self.bottom is None

    def query_move(self, word: str) -> Optional[List]:
        """Queries movement data for a specific direction."""
        try:
            i = self.moves.index(word)
            return self.moves[i + 1:i + 4]
        except ValueError:
            return None

    def calc_co_ord(self):
        """Calculates coordinates based on connected rooms."""
        if not self.room:
            return
        self.room.calc_co_ord()
        co_ord = self.room.query_co_ord()
        if co_ord:
            return
        for word in ["down", "up"]:
            i = self.moves.index(word) if word in self.moves else -1
            if i == -1:
                continue
            other = self.moves[i + 2]
            other_obj = driver.find_object(other)
            if not other_obj:
                continue
            other_co_ord = other_obj.query_co_ord()
            if not other_co_ord:
                continue
            delta = self.room.query_room_size_array()[2] + other_obj.query_room_size_array()[2]
            co_ord = other_co_ord.copy()
            if word == "down":
                co_ord[2] += delta
            else:
                co_ord[2] -= delta
            self.room.set_co_ord(co_ord)
            return

    def set_wall(self, args: List):
        """Configures the wall with provided arguments."""
        for i in range(0, len(args), 2):
            key = args[i]
            value = args[i + 1]
            if key == "bottom":
                self.bottom = value
                if not self.no_drop:
                    self.old_here = self.room.query_property("here")
                    self.room.add_property("here", "falling past you")
            elif key == "below":
                self.belows.extend(value if isinstance(value, list) else [value])
            elif key == "move":
                j = self.moves.index(value[0]) if value[0] in self.moves else -1
                if j == -1:
                    self.moves.extend(value)
                else:
                    self.moves[j + 1:j + 4] = value[1:4]
            elif key in ["death mess", "death_mess"]:
                self.death_mess = value
            elif key in ["ghost action", "ghost_action"]:
                self.ghost_action = value
            elif key in ["no drop", "no_drop"]:
                self.no_drop = value
                if self.bottom:
                    if self.old_here:
                        self.room.add_property("here", self.old_here)
                    else:
                        self.room.remove_property("here")

    async def event_enter(self, thing: MudObject, mess: str, from_room: MudObject):
    if not self.room:
        return
    await self.room.event_enter(thing, f"{thing.name} scales the wall under Mystra’s gaze.", from_room)
    if not thing.query_living() and self.bottom and not self.no_drop:
        driver.call_out(lambda t=thing: self.fall_down(t), 0)

    async def fall_down(self, thing: MudObject):
    if not thing or thing.environment() != self.room:
        return
    damage = self.room.query_room_size_array()[2]
    for below in self.belows:
        below_room = driver.find_object(below)
        if below_room:
            await below_room.tell_room(f"{thing.a_short()} falls past in a blur of shadow.\n")
            damage += 2 * below_room.query_room_size_array()[2]
    driver.log_file("WALLS", f"{time.ctime()} {thing.name} fell from {self.room.oid}\n")
    # Rest unchanged, just async-ified
        if isinstance(self.bottom, str):
            if thing.query_living():
                thing.move_with_look(self.bottom,
                                     f"{thing.a_short()} falls from above with a loud thump.",
                                     f"{thing.a_short()} drops downwards out of sight.")
            else:
                thing.move(self.bottom,
                           f"{thing.a_short()} falls from above with a loud thump.",
                           f"{thing.a_short()} drops downwards out of sight.")
            return
        word = self.bottom[0]
        damage += driver.find_object(word).query_room_size_array()[2]
        if len(self.bottom) > 1 and isinstance(self.bottom[1], str):
            if thing.query_living():
                thing.move_with_look(word,
                                     getattr(driver.find_object(word), self.bottom[1])(thing, self.room),
                                     f"{thing.a_short()} drops downwards out of sight.")
            else:
                thing.move(word,
                           getattr(driver.find_object(word), self.bottom[1])(thing, self.room),
                           f"{thing.a_short()} drops downwards out of sight.")
        else:
            if thing.query_living():
                thing.move_with_look(word,
                                     f"{thing.a_short()} falls from above with a loud crunch.",
                                     f"{thing.a_short()} drops downwards out of sight.")
                damage *= self.bottom[1] * thing.query_complete_weight()
                damage //= 10000
                damage -= thing.query_ac("blunt", damage)
                if damage > 0:
                    if damage > thing.query_hp():
                        thing.tell(self.death_mess or "You hit the ground with a sickening crunch.\n")
                        thing.attack_by(self.room)
                        thing.adjust_hp(-damage, self.room)
                    else:
                        thing.adjust_hp(-damage, self.room)
                        thing.tell("Ouch, that hurt!\n")
            else:
                thing.move(word,
                           f"{thing.a_short()} falls from above with a loud thump.",
                           f"{thing.a_short()} drops downwards out of sight.")

async def init(driver_instance):
    driver = driver_instance
