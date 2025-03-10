# /mnt/home2/mud/systems/help_files.py
# Imported to: object.py, room.py
# Imports from: driver.py
from .nroff import NroffHandler
from typing import List, Optional, Tuple
from ..driver import driver, MudObject

ROOM_HELP_FILE_PROPERTY = "room_help_files"

class HelpFilesHandler:
    def __init__(self):
        self.obj = None
        self.nroff_handler = driver.nroff_handler

    def set_object(self, obj: MudObject):
        self.obj = obj

    def add_help_file(self, help_file: str):
        help_files = self.obj.query_property(ROOM_HELP_FILE_PROPERTY) or []
        if help_file not in help_files:
            help_files.append(help_file)
            self.obj.add_property(ROOM_HELP_FILE_PROPERTY, help_files)

    def remove_help_file(self, help_file: str):
        help_files = self.obj.query_property(ROOM_HELP_FILE_PROPERTY) or []
        if help_file in help_files:
            help_files.remove(help_file)
            self.obj.add_property(ROOM_HELP_FILE_PROPERTY, help_files)

    def query_help_files(self) -> List[str]:
        return self.obj.query_property(ROOM_HELP_FILE_PROPERTY) or []

    def query_help_file_directory(self) -> str:
        return "/doc/unknown/"

    def nroff_file(self, name: str, html: bool = False) -> str:
        if name[0] != '/':
            name = f"{self.query_help_file_directory()}{name}"
        nroff_fn = name.replace("/", ".") + "_nroff"
        output = self.nroff_handler.cat_file(nroff_fn, True) if not html else self.nroff_handler.html_file(nroff_fn, name.split("/")[-1])
        if not output:
            self.nroff_handler.create_nroff(name, nroff_fn)
            output = self.nroff_handler.cat_file(nroff_fn, False) if not html else self.nroff_handler.html_file(nroff_fn, name.split("/")[-1])
        return output or "Unable to process help file."

    def help_function(self) -> Optional[List[Tuple[str, callable]]]:
        help_files = self.query_help_files()
        if not help_files:
            return None
        return [(f.replace("_", " "), lambda f=f: self.nroff_file(f, False)) for f in help_files]

    def help_string(self) -> Optional[str]:
        help_files = self.query_help_files()
        if not help_files:
            return None
        return "".join(self.nroff_file(f, False) for f in help_files)

async def init(driver_instance):
    driver = driver_instance