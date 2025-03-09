# /mnt/home2/mud/systems/login_handler.py
from typing import Optional
from ..driver import driver, Player, MudObject
import asyncio
import hashlib
import sqlite3
import json
import os

class LoginHandler:
    def __init__(self, db_path: str = "/mnt/home2/mud/players/mud.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                name TEXT PRIMARY KEY, 
                password TEXT, 
                race TEXT, 
                class TEXT, 
                data TEXT
            )
        """)
        self.db.commit()
        self.races = ["human", "elf", "drow", "dwarf", "gnome", "halfling", "orc", "goblin", "dragonborn"]
        self.classes = ["fighter", "wizard", "cleric", "thief"]

    async def init(self, driver_instance):
        self.driver = driver_instance

    async def handle_login(self, player: Player) -> bool:
        await player.send("Welcome to the Realms, traveler, under the gaze of Mystra...")
        await asyncio.sleep(5)
        await player.send("A portal shimmers before you...")
        await asyncio.sleep(5)
        await player.send("You emerge as a spirit in the Ethereal Veil...")
        await asyncio.sleep(5)

        # Check existing player
        await player.send("Enter your name (or 'new' to create, 'g' for name list): ")
        name = await self.get_input(player)
        if name.lower() == "g":
            await player.send("Generated names: Zarathar, Elendir, Kaelith...")
            await player.send("Enter your name: ")
            name = await self.get_input(player)
        elif name.lower() == "new":
            return await self.create_character(player)
        elif name:
            cursor = self.db.execute("SELECT password, data FROM players WHERE name=?", (name,))
            data = cursor.fetchone()
            if data:
                stored_pass, player_data = data
                await player.send("Enter password: ")
                password = await self.get_input(player)
                if hashlib.sha256(password.encode()).hexdigest() == stored_pass:
                    player.name = name
                    player.attrs = json.loads(player_data) if player_data else {}
                    player.location = self.driver.objects["ethereal_veil_start"]
                    await player.send(await player.location.call("look", player))
                    return True
                else:
                    await player.send("Incorrect password!")
                    return False
            else:
                await player.send(f"No player named {name} found. Create a new character? (y/n): ")
                if await self.get_input(player).lower() == "y":
                    return await self.create_character(player)
        return False

    async def create_character(self, player: Player) -> bool:
        await player.send("Choose a name (avoid offensive or book names, e.g., Elminster): ")
        name = await self.get_input(player)
        if not name or any(c in name.lower() for c in "1234567890!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"):
            await player.send("Invalid name! Use letters only.")
            return False
        await player.send("Enter password: ")
        password = await self.get_input(player)
        await player.send("Confirm password: ")
        confirm = await self.get_input(player)
        if password != confirm:
            await player.send("Passwords don’t match!")
            return False
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        await player.send("Choose race (human, elf, drow, dwarf, gnome, halfling, orc, goblin, dragonborn): ")
        race = await self.get_input(player).lower()
        if race not in self.races:
            await player.send("Invalid race!")
            return False
        await player.send("Choose class (fighter, wizard, cleric, thief): ")
        class_ = await self.get_input(player).lower()
        if class_ not in self.classes:
            await player.send("Invalid class!")
            return False
        await player.send("Terms: No profanity, no harassment. Agree? (yes/no): ")
        if await self.get_input(player).lower() != "yes":
            await player.send("You must agree to play!")
            return False

        player.name = name
        player.attrs = {"race": race, "class": class_, "skills": {}, "stats": {"hp": 100, "gp": 100}}
        self.db.execute("INSERT INTO players (name, password, race, class, data) VALUES (?, ?, ?, ?, ?)",
                        (name, hashed_pass, race, class_, json.dumps(player.attrs)))
        self.db.commit()
        player.location = self.driver.objects["ethereal_veil_start"]
        await player.send(await player.location.call("look", player))
        await player.send("Character created! Explore the Ethereal Veil to begin.")
        return True

    async def get_input(self, player: Player) -> str:
        if player.protocol == "telnet":
            data = await player.writer.read(1024)
            return data.decode("utf-8").strip() if data else ""
        else:
            return await player.writer.recv()

# Initialize login handler
login_handler = LoginHandler()

async def init(driver_instance):
    await login_handler.init(driver_instance)
