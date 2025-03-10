# /mnt/home2/mud/systems/misc.py
# Imported to: object.py
# Imports from: driver.py

from typing import Dict, List, Tuple
from ..driver import driver, MudObject

class MiscHandler:
    def __init__(self):
        self.weight = 1
        self.length = 1
        self.width = 1
        self.value = 0
        self.value_info: Dict[str, int] = {}

    def set_width(self, w: int):
        self.width = w

    def query_width(self) -> int:
        return self.width

    def set_length(self, l: int):
        self.length = l

    def query_length(self) -> int:
        return self.length

    def adjust_weight(self, w: int):
        if env := driver.environment(self):
            env.add_weight(w)
        self.weight += w

    def set_weight(self, w: int):
        if env := driver.environment(self):
            env.add_weight(w - self.weight)
        self.weight = w

    def query_weight(self) -> int:
        return self.weight

    def query_complete_weight(self) -> int:
        return self.weight  # Shadows handled in object.py

    def adjust_money(self, amt: int | List[Tuple[str, int]], coin: str = None) -> int:
        # Placeholder for MONEY_HAND; assumes flat value
        if isinstance(amt, list):
            self.value += sum(v for _, v in amt)
        else:
            self.value += amt
        self.value = max(0, self.value)
        return self.value

    def adjust_value(self, i: int) -> int:
        self.value += i
        self.value = max(0, self.value)
        return self.value

    def query_money_array(self) -> List[Tuple[str, int]]:
        # Simplified: assumes copper as base unit
        return [("copper", self.value)]

    def query_money(self, type_: str) -> int:
        return self.value if type_ == "copper" else 0

    def set_value(self, number: int):
        self.value = number

    def set_value_info(self, word: str, number: int):
        self.value_info[word] = number

    def remove_value_info(self, word: str):
        self.value_info.pop(word, None)

    def query_value(self) -> int:
        return self.value

    def query_base_value(self) -> int:
        return self.value

    def query_value_info(self) -> Dict[str, int]:
        return self.value_info.copy()

    def query_value_at(self, place: MudObject) -> int:
        total = self.value
        for key, val in self.value_info.items():
            how = place.query_property(f"{key} valued")
            if how:
                if key == "artifact":
                    total += val  # Simplified, needs charges
                elif key == "enchantment" and hasattr(self, "query_max_enchant"):
                    total += (val * how * self.query_enchant()) // self.query_max_enchant()
                elif key == "material" and hasattr(self, "query_material"):
                    total += self.query_weight() * 1  # Placeholder for PRICE_INDEX
                else:
                    total += val
        return total

    def query_value_real(self, place: str) -> int:
        total = self.value
        for key, val in self.value_info.items():
            if key == "artifact":
                total += val * 3  # Simplified, needs charges
            elif key == "enchantment" and hasattr(self, "query_max_enchant"):
                total += (val * 10 * self.query_enchant()) // self.query_max_enchant()
            elif key == "material" and hasattr(self, "query_material"):
                total += self.query_weight() * 1  # Placeholder for PRICE_INDEX
            else:
                total += val
        return total

    async def move(self, dest: str | MudObject, messin: str = "", messout: str = "") -> int:
        from_ = driver.environment(self)
        w = self.query_complete_weight()
        if isinstance(dest, str):
            dest = driver.load_object(dest)
        if not dest:
            return -1  # MOVE_INVALID_DEST
        if not dest.add_weight(w):
            return -2  # MOVE_TOO_HEAVY
        i = await driver.move_object(self, dest, messin, messout)
        if i != 0:  # MOVE_OK
            dest.add_weight(-w)
            return i
        if from_:
            from_.add_weight(-w)
        return i

    def stats(self) -> List[Tuple[str, int]]:
        guff = [("value", self.value)]
        guff.extend([(f"(info) {k}", v) for k, v in self.value_info.items()])
        return guff

async def init(driver_instance):
    driver = driver_instance