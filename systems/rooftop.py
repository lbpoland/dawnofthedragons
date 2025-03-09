# /mnt/home2/mud/systems/rooftop.py
from typing import Optional, List, Dict, Union
from ..driver import driver, MudObject, Player
import math
import random

# Constants from rooftop.c
TOO_SOON = "too soon to proceed from rooftop"
ROCK = "other.movement.climbing.rock"

class Rooftop(MudObject):
    def __init__(self, oid: str, name: str):
        super().__init__(oid, name)
        self.room: Optional[MudObject] = None
        self.wall: Optional[MudObject] = None
        self.damages: Dict[str, int] = {}
        self.damage_types: List[str] = ["weak", "slope", "step", "jump"]
        self.roof_max_weight: int = 0  # Max weight in units (20 units = 1 kg)
        self.gradient: int = 0  # Percentage grade (converted from degrees)
        self.weak_roof_dest: Optional[str] = None
        self.slope_dest: Optional[str] = None
        self.place: str = "roof"
        self.death_reason: Optional[str] = None
        self.jump_info: Dict[str, List[Union[str, int]]] = {}
        self.translations: Dict[str, str] = {}
        # Message arrays
        self.weak_messages: List[str] = [
            "The roof collapses! This is going to be painful...\n",
            "$short$ crashes down through a weak spot in the roof.",
            "$short$ comes crashing to the ground, landing in a rain of debris.",
            "You hear an ominous creak.\n"
        ]
        self.slope_messages: List[str] = [
            "The roof is too steep for you to stand on! It's time to make friends with the floor...\n",
            "$short$ gets in touch with gravity and slides over the edge of the roof.",
            "$short$ comes crashing to the ground, landing in a heap."
        ]
        self.step_messages: List[str] = [
            "You step off the edge of the roof into midair.\n",
            "$short$ steps off the edge of the roof and plummets earthwards.",
            "$short$ comes crashing to the ground, landing in a heap."
        ]
        self.jump_tm_messages: List[str] = [
            "You leap more gracefully through the air.",
            "You feel more able to leap tall buildings in a single bound.",
            "You jump like a mountain goat."
        ]
        self.jump_success_messages: List[str] = [
            "You launch yourself off the edge of the roof and land gracefully on the other side.\n",
            "$short$ jumps gracefully across the gap to the $dir$.",
            "$short$ jumps in from across the gap to the $opp_dir$."
        ]
        self.jump_failure_messages: List[str] = [
            "You launch yourself off the edge of the roof!\nUnfortunately you misjudge the distance and plummet earthwards. This is going to hurt...\n",
            "$short$ jumps off to the $dir$, but misjudges and plummets earthwards.",
            "$short$ plummets to the ground, landing in a heap."
        ]
        self.ghost_fall_messages: List[str] = [
            "You find your consciousness drifting earthwards.\n",
            "$the_short$ drifts earthwards.",
            "$the_short$ drifts in from above, looking somewhat dazed."
        ]
        self.item_slope_messages: List[str] = [
            "$the_short$ tumbles over the edge and plummets to the ground.\n",
            "Hearing a noise, you look up just as $a_short$ falls off the edge of the roof and hits the ground.\n"
        ]
        self.corpse_slope_messages: List[str] = [
            "$the_short$ tumbles over the edge and plummets to the ground with a sickening thud.\n",
            "Hearing a noise, you look up just as $the_short$ tumbles over the edge of the roof and hits the ground with a sickening thud.\n"
        ]

    def setup_shadow(self, room: MudObject):
        """Sets up the rooftop shadow on the given room."""
        self.room = room
        self.wall = driver.clone_object("/systems/wall")
        self.wall.setup_shadow(room)
        self.room.add_command("jump", "<word'direction'>", lambda dir: self.do_roofjump(dir))

    def destruct_shadow(self):
        """Destroys the rooftop shadow and cleans up."""
        if self.room and self.wall:
            self.wall.destruct_shadow()
        self.room = None
        self.wall = None
        self.destruct()

    def set_fall_damage(self, type: str, damage: int):
        """Sets the fall damage for a specific type."""
        damage = abs(damage)
        if type == "all":
            for t in self.damage_types:
                self.damages[t] = damage
        elif type in self.damage_types:
            self.damages[type] = damage

    def query_fall_damage(self, type: str) -> Union[int, Dict[str, int]]:
        """Queries the fall damage for a type."""
        if type == "all":
            return self.damages.copy()
        return self.damages.get(type, 0)

    def calc_fall_damage(self, type: str) -> int:
        """Calculates randomized fall damage."""
        if type == "all":
            return 0
        return self.query_fall_damage(type) + random.randint(0, self.query_fall_damage(type))

    def set_weak_roof(self, maxweight: int, dest: str):
        """Sets the maximum weight capacity and collapse destination."""
        self.roof_max_weight = maxweight
        self.weak_roof_dest = dest

    def set_slope(self, angle: int, loc: str, dest: str):
        """Sets the roof gradient and slip destination."""
        self.gradient = (angle * 100) // 90
        self.place = loc
        self.slope_dest = dest

    def set_jump(self, dir: Union[str, List[str]], dest: str, fall_dest: str, distance: int) -> int:
        """Sets up a jumping exit with skill check."""
        dirs = [dir] if isinstance(dir, str) else dir
        if not all(isinstance(d, str) for d in dirs):
            return 0
        dirs.sort()
        if any(d in self.translations for d in dirs):
            return -1

        key = dirs[0]
        self.jump_info[key] = [dest, fall_dest, distance]
        for d in dirs:
            self.translations[d] = key

        if not self.room.query_exit(key):
            self.room.add_exit(key, dest, "roof")
        self.room.modify_exit(key, [
            "closed", 1,
            "function", lambda verb, ob, special: self.silly_move(verb, ob, special, self.jump_info[self.translations[verb]][1], "step", self.step_messages),
            "look", "You'll have to jump across to see what's on the other side."
        ])
        return 1

    def set_weak_messages(self, player: str, from_: str, to: str, warn: str):
        """Sets messages for weak roof collapse."""
        self.weak_messages = [player, from_, to, warn]

    def set_slope_messages(self, player: str, from_: str, to: str):
        """Sets messages for slipping off a slope."""
        self.slope_messages = [player, from_, to]

    def set_step_messages(self, player: str, from_: str, to: str):
        """Sets messages for stepping off the edge."""
        self.step_messages = [player, from_, to]

    def set_jump_tm_messages(self, messages: List[str]):
        """Sets messages for skill improvement during jumps."""
        self.jump_tm_messages = messages

    def set_jump_success_messages(self, player: str, from_: str, to: str):
        """Sets messages for successful jumps."""
        self.jump_success_messages = [player, from_, to]

    def set_jump_failure_messages(self, player: str, from_: str, to: str):
        """Sets messages for failed jumps."""
        self.jump_failure_messages = [player, from_, to]

    def set_ghost_fall_messages(self, player: str, from_: str, to: str):
        """Sets messages for ghost falls."""
        self.ghost_fall_messages = [player, from_, to]

    def set_corpse_slope_messages(self, from_: str, to: str):
        """Sets messages for corpses sliding off."""
        self.corpse_slope_messages = [from_, to]

    def set_item_slope_messages(self, from_: str, to: str):
        """Sets messages for items sliding off."""
        self.item_slope_messages = [from_, to]

    def set_death_reason(self, reason: str):
        """Sets the death reason for falling."""
        self.death_reason = reason
        driver.call_out(lambda: setattr(self, "death_reason", None), 2)

    def query_death_reason(self) -> str:
        """Returns the death reason."""
        reason = self.death_reason or f"a rooftop ({self.room.oid}) with an incorrectly set death message"
        return driver.convert_message(reason)

    def process_mess(self, msg: str, obj: MudObject, direction: Optional[str] = None) -> str:
        """Processes messages with substitutions."""
        if not msg:
            return ""
        directions = ["north", "northeast", "east", "southeast", "south", "southwest", "west", "northwest"]
        opp_dir = None
        if direction and direction in directions:
            opp_idx = (directions.index(direction) + 4) % 8
            opp_dir = directions[opp_idx]

        transforms = {
            "$dir$": direction,
            "$opp_dir$": opp_dir,
            "$short$": obj.query_short(),
            "$poss$": obj.query_possessive(),
            "$pronoun$": obj.query_pronoun(),
            "$obj$": obj.query_objective(),
            "$a_short$": obj.a_short(),
            "$the_short$": obj.the_short(),
            "$one_short$": obj.one_short()
        }
        for key, val in transforms.items():
            if val:
                msg = msg.replace(key, val)
        return msg

    def do_fall(self, obj: MudObject, dest: Union[str, MudObject], dam_type: str, messages: List[str], dir: Optional[str]):
        """Handles falling mechanics."""
        obj.remove_property(TOO_SOON)
        messages = [self.process_mess(m, obj, dir) for m in messages]
        if isinstance(dest, str):
            destob = driver.load_object(dest)
            if not destob:
                obj.tell(f"Cannot find {dest}.\nMoving you to the void - Please contact a creator.\n")
                obj.move_with_look("/room/void", "Poof. $N appears.\n", "$N plummets earthwards.\n")
                return
        else:
            destob = dest

        obj.tell(messages[0])
        obj.move_with_look(destob, messages[2], messages[1])
        if obj.query_property("dead"):
            return

        damage = self.calc_fall_damage(dam_type)
        if damage >= obj.query_hp():
            self.set_death_reason("plummeting from the rooftops")
            obj.attack_by(self.room)
            obj.do_death()
        else:
            obj.adjust_hp(-damage)

    def silly_move(self, verb: str, ob: MudObject, special: str, dest: str, dam_type: str, messages: List[str]) -> int:
        """Handles stepping off the edge."""
        self.do_fall(ob, dest, dam_type, messages, None)
        return 0  # Notify fail

    def event_enter(self, obj: MudObject, from_room: Optional[MudObject]):
        """Handles entering the rooftop with skill checks."""
        if not obj or obj.query_property("demon") or obj.query_property("floating"):
            return

        obj.add_property(TOO_SOON, 1, 5)

        if self.roof_max_weight:
            contents = self.room.all_inventory()
            total_weight = 0
            for item in contents:
                object_weight = item.query_weight() + item.query_loc_weight()
                total_weight += object_weight

            if total_weight > self.roof_max_weight:
                self.room.tell_room(self.weak_messages[3])
                destob = driver.load_object(self.weak_roof_dest)
                if not destob:
                    self.room.tell_room(f"Error loading room {self.weak_roof_dest}, moving to the void.\nPlease contact a creator.\n")
                    for item in contents:
                        item.move_with_look("/room/void")
                    return
                for item in contents:
                    driver.call_out(lambda o=item: self.do_fall(o, destob, "weak", self.weak_messages, None), 1)
                return

        if self.gradient:
            if obj.query_living():
                if obj.query_property("dead") or not obj.query_max_weight():
                    driver.call_out(lambda o=obj: self.do_fall(o, self.slope_dest, "step", self.ghost_fall_messages, None), 1)
                    return
                encum = (100 * obj.query_loc_weight()) / obj.query_max_weight()
                diff = int(math.sin(math.radians(self.gradient)) * (encum * 10))
                driver.call_out(lambda o=obj: self.gradient_check(o, self.slope_dest, int(diff + (self.gradient * 2))), 1)
            else:
                if obj.query_name() in ["death", "binky"]:
                    return
                if self.gradient > 3:
                    messages = self.corpse_slope_messages if obj.query_corpse() else self.item_slope_messages
                    obj.move(self.slope_dest, self.process_mess(messages[1], obj, None), self.process_mess(messages[0], obj, None))
            return

        obj.remove_property(TOO_SOON)

    def gradient_check(self, obj: MudObject, destination: str, diff: int):
        """Performs a skill check for sloping roofs."""
        obj.remove_property(TOO_SOON)
        result = driver.tasker.perform_task(obj, ROCK, diff + 1, "TM_FIXED")
        if result == "AWARD":
            obj.tell(f"YELLOW: {random.choice(['You balance more confidently on the {self.place}.', 'Climbing becomes easier.'])}\n")
        if result in ["AWARD", "SUCCEED"]:
            obj.tell(f"The {self.place} is steep, but you manage not to fall.\n")
        elif result == "FAIL":
            destob = driver.load_object(destination)
            if not destob:
                obj.tell(f"Error loading room {destination}, moving you to the void.\nPlease contact a creator.\n")
                obj.move_with_look("/room/void")
            else:
                self.do_fall(obj, destob, "slope", self.slope_messages, None)
        else:
            obj.tell("Gnaaaaaaaaaaaah! You should not be getting this message. Please contact a creator.\n")

    def do_roofjump(self, dir: str) -> int:
        """Handles the jump command with skill check."""
        key = self.translations.get(dir)
        if not key or key not in self.jump_info:
            self.room.add_failed_mess("You can't jump there!\n")
            return 0

        info = self.jump_info[key]
        destination = driver.load_object(info[0])
        if not destination:
            self.room.add_failed_mess(f"Error! The file {info[0]} does not exist or does not load. Please contact a creator.\n")
            return 0

        fall_destination = driver.load_object(info[1])
        if not fall_destination:
            self.room.add_failed_mess(f"Error! The file {info[1]} does not exist or does not load. Please contact a creator.\n")
            return 0

        distance = info[2]
        if distance:
            weight = driver.this_player().query_loc_weight()
            max_weight = driver.this_player().query_max_weight()
            distance = int(distance * ((weight * 7) / max_weight + 15))
            result = driver.tasker.perform_task(driver.this_player(), ROCK, distance, "TM_FIXED")
            if result == "AWARD":
                driver.this_player().tell(f"YELLOW: {random.choice(self.jump_tm_messages)}\n")
            if result in ["AWARD", "SUCCEED"]:
                driver.this_player().tell(self.process_mess(self.jump_success_messages[0], driver.this_player(), dir))
                driver.this_player().move_with_look(
                    destination,
                    self.process_mess(self.jump_success_messages[2], driver.this_player(), dir),
                    self.process_mess(self.jump_success_messages[1], driver.this_player(), dir)
                )
            elif result == "FAIL":
                driver.this_player().tell(self.process_mess(self.jump_failure_messages[0], driver.this_player(), dir))
                self.do_fall(driver.this_player(), fall_destination, "jump", self.jump_failure_messages, dir)
            else:
                driver.this_player().tell("Oh dear. Something is broken. Please inform a creator.\n")
            return 1
        return 0

    def test_remove(self, ob: MudObject, flag: int, dest: Union[str, MudObject]) -> bool:
        """Prevents removal if balance hasn’t been caught."""
        if not ob.query_living():
            return self.room.test_remove(ob, flag, dest)

        if isinstance(dest, MudObject):
            dest = dest.oid
        if not isinstance(dest, str) or dest == "/room/rubbish":
            return True

        if ob.query_property(TOO_SOON):
            ob.tell("You haven't quite caught your balance yet.\n")
            return False
        return self.room.test_remove(ob, flag, dest)

async def init(driver_instance):
    driver = driver_instance
