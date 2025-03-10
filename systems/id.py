# /mnt/home2/mud/systems/id.py
# Imported to: object.py
# Imports from: driver.py

from typing import List, Optional
from ..driver import driver, MudObject

class IdHandler:
    def __init__(self):
        self.name = "object"
        self.alias: List[str] = []
        self.faux_alias: List[str] = []
        self.unique_faux_alias: List[str] = []
        self.adjectives: List[str] = []
        self.faux_adjectives: List[str] = []
        self.unique_faux_adjectives: List[str] = []
        self.plurals: List[str] = []
        self.plural_adjectives: List[str] = []

    def set_name(self, str_: str):
        self.name = str_

    def query_name(self) -> str:
        return self.name

    def query_cap_name(self) -> str:
        return self.name.capitalize()

    def set_aliases(self, str_: List[str]):
        self.alias = str_

    def add_alias(self, str_: str | List[str]):
        if isinstance(str_, list):
            self.alias.extend([s for s in str_ if s not in self.alias])
        elif str_ not in self.alias:
            self.alias.append(str_)

    def remove_alias(self, str_: str) -> bool:
        if str_ in self.alias:
            self.alias.remove(str_)
            return True
        return False

    def query_alias(self, no_faux: bool = False) -> List[str]:
        if no_faux or not self.unique_faux_alias or not self.faux_id_allowed():
            return self.alias.copy()
        return self.alias + self.unique_faux_alias

    def add_faux_alias(self, str_: str | List[str]):
        if isinstance(str_, list):
            for s in str_:
                self.add_faux_alias(s)
        elif str_ not in self.alias:
            self.faux_alias.append(str_)
            if str_ not in self.unique_faux_alias:
                self.unique_faux_alias.append(str_)

    def remove_faux_alias(self, str_: str) -> bool:
        if str_ in self.faux_alias:
            self.faux_alias.remove(str_)
            if str_ not in self.faux_alias:
                self.unique_faux_alias = [x for x in self.unique_faux_alias if x != str_]
            return True
        return False

    def query_faux_alias(self) -> List[str]:
        return self.faux_alias.copy()

    def query_unique_faux_alias(self) -> List[str]:
        return self.unique_faux_alias.copy()

    def faux_id_allowed(self) -> bool:
        # Placeholder: assumes no previous objects ignore identifiers
        return True

    def id(self, str_: str) -> bool:
        return str_ == self.name or str_ in self.query_alias()

    def full_id(self, str_: str) -> bool:
        words = [w for w in str_.split() if w]
        if not words:
            return False
        name = words[-1]
        adjectives = words[:-1]
        if not (self.id(name) or self.id_plural(name)):
            return False
        return all(self.id_adjective(adj) for adj in adjectives)

    def set_plurals(self, str_: List[str]):
        self.plurals = str_

    def add_plural(self, str_: str | List[str]):
        if isinstance(str_, list):
            self.plurals.extend([s for s in str_ if s not in self.plurals])
        elif str_ not in self.plurals:
            self.plurals.append(str_)

    def remove_plural(self, str_: str):
        if str_ in self.plurals:
            self.plurals.remove(str_)

    def add_plurals(self, str_: List[str]):
        self.plurals.extend([s for s in str_ if s not in self.plurals])

    def query_plurals(self) -> List[str]:
        return self.plurals.copy()

    def id_plural(self, str_: str) -> bool:
        return str_ in self.plurals

    def set_adjectives(self, str_: List[str]):
        self.adjectives = str_

    def add_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            self.adjectives.extend([s for s in str_ if s not in self.adjectives])
        elif isinstance(str_, str):
            words = str_.split()
            for word in words:
                if word not in self.adjectives:
                    self.adjectives.append(word)

    def remove_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            for s in str_:
                self.remove_adjective(s)
        elif str_ in self.adjectives:
            self.adjectives.remove(str_)

    def add_faux_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            for s in str_:
                self.add_faux_adjective(s)
        elif isinstance(str_, str):
            words = [w for w in str_.split() if w not in self.adjectives]
            for word in words:
                self.faux_adjectives.append(word)
                if word not in self.unique_faux_adjectives:
                    self.unique_faux_adjectives.append(word)

    def remove_faux_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            for s in str_:
                self.remove_faux_adjective(s)
        elif str_ in self.faux_adjectives:
            self.faux_adjectives.remove(str_)
            if str_ not in self.faux_adjectives:
                self.unique_faux_adjectives = [x for x in self.unique_faux_adjectives if x != str_]

    def query_faux_adjectives(self) -> List[str]:
        return self.faux_adjectives.copy()

    def query_unique_faux_adjectives(self) -> List[str]:
        return self.unique_faux_adjectives.copy()

    def query_adjectives(self, no_faux: bool = False) -> List[str]:
        if no_faux or not self.unique_faux_adjectives or not self.faux_id_allowed():
            return self.adjectives.copy()
        return self.adjectives + self.unique_faux_adjectives

    def id_adjective(self, word: str) -> bool:
        return word in self.query_adjectives()

    def set_plural_adjectives(self, str_: List[str]):
        self.plural_adjectives = str_

    def add_plural_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            self.plural_adjectives.extend([s for s in str_ if s not in self.plural_adjectives])
        elif isinstance(str_, str):
            words = str_.split()
            for word in words:
                if word not in self.plural_adjectives:
                    self.plural_adjectives.append(word)

    def remove_plural_adjective(self, str_: str | List[str]):
        if isinstance(str_, list):
            for s in str_:
                self.remove_plural_adjective(s)
        elif str_ in self.plural_adjectives:
            self.plural_adjectives.remove(str_)

    def query_plural_adjectives(self) -> List[str]:
        return self.plural_adjectives.copy()

    def id_plural_adjective(self, word: str) -> bool:
        return word in self.plural_adjectives

    def parse_command_id_list(self) -> List[str]:
        return [self.name, self.oid] + self.query_alias()

    def parse_command_plural_id_list(self) -> List[str]:
        return self.query_plurals()

    def parse_command_adjectiv_id_list(self) -> List[str]:
        return self.query_adjectives()

    def parse_command_plural_adjectiv_id_list(self) -> List[str]:
        return self.query_plural_adjectives()

async def init(driver_instance):
    driver = driver_instance