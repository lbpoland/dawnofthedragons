# /mnt/home2/mud/systems/description.py
# Imported to: room.py, living.py
# Imports from: driver.py

from typing import Dict, List, Optional, Union
from ..driver import driver, MudObject
import asyncio

class Desc:
    def __init__(self):
        self.short: Optional[str] = None
        self.long: Optional[str] = None
        self.adjectives: List[str] = []
        self.aliases: List[str] = []
        self.plurals: Dict[str, str] = {}  # {singular: plural}
        self.dark: int = 0  # 2025: Dark flag for visibility

    def setup(self, obj: MudObject):
        """Sets up description attributes on an object."""
        obj.short = self.short or "something"
        obj.long = self.long or "A nondescript thing stands before you.\n"
        obj.adjectives = self.adjectives.copy()
        obj.aliases = self.aliases.copy()
        obj.plurals = self.plurals.copy()
        obj.dark = self.dark

    def set_short(self, short: str):
        """Sets the short description."""
        self.short = short.strip()

    def query_short(self, dark: int = 0) -> str:
        """Returns the short description, adjusted for darkness."""
        if dark or self.dark:
            return "a shadowed form"
        return self.short or "something"

    def set_long(self, long: Union[str, List]):
        """Sets the long description."""
        if isinstance(long, list):
            self.long = " ".join(str(item) for item in long)
        else:
            self.long = long.strip()

    def query_long(self) -> str:
        """Returns the long description."""
        return self.long or "A nondescript thing stands before you.\n"

    def add_adjective(self, adj: Union[str, List[str]]):
        """Adds adjectives to the description."""
        if isinstance(adj, str):
            if adj not in self.adjectives:
                self.adjectives.append(adj)
        else:
            for a in adj:
                if a not in self.adjectives:
                    self.adjectives.append(a)

    def query_adjectives(self) -> List[str]:
        """Returns the list of adjectives."""
        return self.adjectives.copy()

    def add_alias(self, alias: Union[str, List[str]]):
        """Adds aliases to the description."""
        if isinstance(alias, str):
            if alias not in self.aliases:
                self.aliases.append(alias)
        else:
            for a in alias:
                if a not in self.aliases:
                    self.aliases.append(a)

    def query_aliases(self) -> List[str]:
        """Returns the list of aliases."""
        return self.aliases.copy()

    def add_plural(self, singular: str, plural: str):
        """Adds a singular-plural pair."""
        self.plurals[singular] = plural

    def query_plural(self, singular: str) -> Optional[str]:
        """Returns the plural form of a singular noun."""
        return self.plurals.get(singular)

    def pluralize(self, word: str) -> str:
        """Generates a plural form if not explicitly set."""
        plural = self.query_plural(word)
        if plural:
            return plural
        if word.endswith("s") or word.endswith("sh") or word.endswith("ch") or word.endswith("x") or word.endswith("z"):
            return word + "es"
        if word.endswith("y") and word[-2] not in "aeiou":
            return word[:-1] + "ies"
        return word + "s"

    def set_dark(self, dark: int):
        """Sets the darkness flag (2025 feature)."""
        self.dark = max(0, min(1, dark))

    def query_dark(self) -> int:
        """Returns the darkness flag."""
        return self.dark

    def a_short(self, dark: int = 0) -> str:
        """Returns the short description with an article."""
        short = self.query_short(dark)
        if short.startswith("the ") or short.startswith("The "):
            return short
        prefix = "an" if short[0] in "aeiou" else "a"
        return f"{prefix} {short}"

    def the_short(self, dark: int = 0) -> str:
        """Returns the short description with 'the'."""
        short = self.query_short(dark)
        if short.startswith("the ") or short.startswith("The "):
            return short
        return f"the {short}"

    def one_short(self, dark: int = 0) -> str:
        """Returns the short description with 'one' (2025 addition)."""
        short = self.query_short(dark)
        return f"one {short}"

    async def describe(self, obj: MudObject, viewer: Optional[MudObject] = None) -> str:
        """Returns a full description for the object."""
        dark = viewer.check_dark(obj.query_light()) if viewer else self.dark
        desc = f"{self.a_short(dark)} stands here.\n"
        if not dark:
            desc += self.query_long()
            if viewer and viewer.attrs.get("see_octarine", False):
                enchant = obj.query_enchant()
                if enchant > 50:
                    desc += f"It glows with Mystra’s arcane touch ({enchant}).\n"
        return desc

async def init(driver_instance):
    driver = driver_instance
    # No global instance; Desc is a mixin class for objects like Room and Living