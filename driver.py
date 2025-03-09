# /mnt/home2/mud/driver.py
import asyncio
import telnetlib3
import zlib
import json
import logging
import sqlite3
from typing import Dict, Callable, Any, Optional
from websockets.server import serve
import aiohttp
from ssl import create_default_context
import uvloop
import aiojobs
import cProfile, pstats
from concurrent.futures import ProcessPoolExecutor
import os
import signal
import importlib
import aiofiles
from heapq import heappush, heappop
import time
import redis  # For clustering
import hashlib

# Use uvloop for faster event loop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/home2/mud/logs/server.log'),
        logging.FileHandler('/mnt/home2/mud/logs/errors.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PyMudDriver")

# Call stack for this_object(), previous_object()
call_stack = []

# Base MUD Object
class MudObject:
    def __init__(self, oid: str, name: str, euid: str = "root"):
        self.oid = oid
        self.name = name
        self.actions: Dict[str, Callable] = {}
        self.attrs: Dict[str, Any] = {}
        self.location: Optional["MudObject"] = None
        self.euid = euid

    def add_action(self, verb: str, func: Callable):
        self.actions[verb] = func

    async def call(self, verb: str, caller: "Player", arg: str = None) -> str:
        global call_stack
        call_stack.append(self)
        try:
            if verb in self.actions:
                return await self.actions[verb](self, caller, arg)
            return await driver.notify_fail(caller, f"{verb} not recognized.")
        finally:
            call_stack.pop()

    def set(self, key: str, value: Any):
        self.attrs[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.attrs.get(key, default)

    def clone(self) -> "MudObject":
        new_oid = f"{self.oid}_clone_{id(self)}"
        clone = MudObject(new_oid, self.name, self.euid)
        clone.actions = self.actions.copy()
        clone.attrs = self.attrs.copy()
        driver.objects[new_oid] = clone
        return clone

    def destruct(self):
        if self.oid in driver.objects:
            del driver.objects[self.oid]
            driver.save_object(self)

# Player Class
class Player:
    def __init__(self, writer, protocol: str = "telnet"):
        self.writer = writer
        self.protocol = protocol
        self.location: Optional[MudObject] = None
        self.compress = False
        self.gmcp_enabled = False
        self.msdp_enabled = False
        self.atcp_enabled = False
        self.msdp_data = {}
        self.ip_address = None
        self.last_active = time.time()
        self.pk_flagged = False

    async def send(self, msg: str):
        data = f"\033[38;2;255;255;255m{msg}\033[0m".encode("utf-8")  # RGB colors
        if self.compress:
            data = zlib.compress(data)
        if self.protocol == "telnet":
            self.writer.write(data + b"\r\n")
            await self.writer.drain()
        elif self.protocol == "websocket":
            await self.writer.send(msg)
        if self.gmcp_enabled:
            await self.send_gmcp({"event": "output", "message": msg})
        if self.msdp_enabled:
            self.msdp_data["last_message"] = msg
            await self.send_msdp(self.msdp_data)
        if self.atcp_enabled:
            await self.send_atcp({"message": msg})

    async def send_gmcp(self, data: Dict):
        if self.gmcp_enabled:
            await self.writer.write(f"\xff\xfa\x90{json.dumps(data)}\xff\xf0".encode())

    async def send_msdp(self, data: Dict):
        if self.msdp_enabled:
            await self.writer.write(f"\xff\xfa\x69{json.dumps(data)}\xff\xf0".encode())

    async def send_atcp(self, data: Dict):
        if self.atcp_enabled:
            await self.writer.write(f"\xff\xfa\xc8{json.dumps(data)}\xff\xf0".encode())

    async def prompt(self):
        await self.send("> ")

# PyMudDriver
class PyMudDriver:
    def __init__(self, db_path: str = "/mnt/home2/mud/players/mud.db"):
        self.loop = asyncio.get_event_loop()
        self.objects: Dict[str, MudObject] = {}
        self.players: Dict[Any, Player] = {}
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.scheduler = aiojobs.Scheduler()
        self.executor = ProcessPoolExecutor(max_workers=6)  # 6 cores
        self.task_queue = []  # Priority queue for events
        self.plugins = {}
        self.redis = redis.Redis(host='localhost', port=6379, db=0)  # Clustering
        self.last_verb = None
        self.start_time = time.time()
        self.init_db()
    def load_plugins(self):
        for plugin in [
            "systems.combat", "systems.skills_handler", "systems.tactics", "systems.inventory_handler",
            "systems.soul_handler", "systems.term_handler", "systems.network_handler", "systems.quests_handler",
            "systems.crafting_handler", "systems.zones", "systems.living", "systems.parser",
            "systems.organizations", "systems.houses", "systems.pk", "systems.mounts", "systems.commands",
            "systems.terrain_handler", "systems.login_handler", "systems.ritual_handler", "systems.spell_handler",
            "efuns.core", "efuns.network", "efuns.parser", "efuns.communication", "efuns.combat",
            "efuns.skills", "efuns.tools"
        ]:
        self.load_plugin(plugin)

    def init_db(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS objects (oid TEXT PRIMARY KEY, data TEXT)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_oid ON objects (oid)")
        self.db.commit()

    def load_object(self, oid: str, cls: type, name: str, euid: str = "root") -> MudObject:
        cursor = self.db.execute("SELECT data FROM objects WHERE oid=?", (oid,))
        data = cursor.fetchone()
        obj = cls(oid, name, euid)
        if data:
            obj.attrs = json.loads(data[0])
        self.objects[oid] = obj
        return obj

    def save_object(self, obj: MudObject):
        self.db.execute("INSERT OR REPLACE INTO objects VALUES (?, ?)",
                        (obj.oid, json.dumps(obj.attrs)))
        self.db.commit()

    async def call_out(self, delay: float, func: Callable, *args):
        heappush(self.task_queue, (time.time() + delay, func, args))
        await self.scheduler.spawn(self.process_tasks())

    async def process_tasks(self):
        while self.task_queue:
            timestamp, func, args = heappop(self.task_queue)
            if time.time() < timestamp:
                await asyncio.sleep(timestamp - time.time())
            await func(*args)

    async def call_other(self, oid: str, verb: str, caller: Player, arg: str = None) -> str:
        if oid in self.objects:
            return await self.objects[oid].call(verb, caller, arg)
        return "Object not found."

    def this_object(self) -> Optional[MudObject]:
        return call_stack[-1] if call_stack else None

    def previous_object(self) -> Optional[MudObject]:
        return call_stack[-2] if len(call_stack) > 1 else None

    async def read_file(self, path: str) -> str:
        async with aiofiles.open(path, "r") as f:
            return await f.read()

    async def write_file(self, path: str, content: str):
        async with aiofiles.open(path, "w") as f:
            await f.write(content)

    def uptime(self) -> int:
        return int(time.time() - self.start_time)

    def query_verb(self) -> Optional[str]:
        return self.last_verb

    async def notify_fail(self, caller: Player, msg: str) -> str:
        return msg

    def seteuid(self, obj: MudObject, euid: str):
        obj.euid = euid

    def geteuid(self, obj: MudObject) -> str:
        return obj.euid

    def mud_status(self) -> Dict[str, Any]:
        return {
            "uptime": self.uptime(),
            "players": len(self.players),
            "objects": len(self.objects),
            "tasks": len(self.task_queue),
            "memory_usage": os.getpid()  # Approximate
        }

    async def heartbeat(self):
        while True:
            for obj in list(self.objects.values()):
                if "heart_beat" in obj.actions:
                    await obj.call("heart_beat", None)
            await asyncio.sleep(1.0)

    async def telnet_handler(self, reader, writer):
        player = Player(writer, "telnet")
        self.players[writer] = player
        player.ip_address = writer.transport.get_extra_info('peername')[0]
        writer.write(b"\xff\xfb\x01\xff\xfb\x03\033[1z<MXP>\xff\xfb\x5a\xff\xfb\xc9\xff\xfb\x90\xff\xfb\xc8")
        await writer.drain()
        await self.handle_login(player)

    async def websocket_handler(self, websocket):
        player = Player(websocket, "websocket")
        self.players[websocket] = player
        player.ip_address = websocket.remote_address[0]
        await self.handle_login(player)

    async def handle_login(self, player: Player):
        await player.send("Welcome to the Realms, traveler, under the gaze of Mystra...")
        await self.call_out(5, player.send, "A portal shimmers before you...")
        await self.call_out(10, player.send, "You emerge as a spirit in the Ethereal Veil...")
        await self.call_out(15, player.send, "Choose your path [race/class]...")
        player.location = self.objects["ethereal_veil_start"]
        await player.send(await player.location.call("look", player))
        await player.prompt()

        while True:
            try:
                if player.protocol == "telnet":
                    data = await player.writer.read(1024)
                    if not data:
                        break
                    if data.startswith(telnetlib3.IAC):
                        if data[1:3] == telnetlib3.DO + b"\x5a":
                            player.compress = True
                        elif data[1:3] == telnetlib3.DO + b"\xc9":
                            player.msdp_enabled = True
                        elif data[1:3] == telnetlib3.DO + b"\x90":
                            player.gmcp_enabled = True
                        elif data[1:3] == telnetlib3.DO + b"\xc8":
                            player.atcp_enabled = True
                        continue
                    cmd = data.decode("utf-8").strip().split()
                else:
                    message = await player.writer.recv()
                    cmd = message.strip().split()

                if cmd:
                    self.last_verb, *args = cmd
                    arg = " ".join(args) if args else None
                    response = await player.location.call(self.last_verb, player, arg)
                    await player.send(response)
                await player.prompt()
            except Exception as e:
                logger.error(f"Client error: {e}")
                break
        if player.protocol == "telnet":
            player.writer.close()
            await player.writer.wait_closed()
        del self.players[player.writer]

    async def rest_api(self):
        async with aiohttp.web.Application() as app:
            async def get_status(request):
                return aiohttp.web.json_response(self.mud_status())
            app.router.add_get("/status", get_status)
            runner = aiohttp.web.AppRunner(app)
            await runner.setup()
            site = aiohttp.web.TCPSite(runner, "0.0.0.0", 8080)
            await site.start()

    def load_plugin(self, module_name: str):
        module = importlib.import_module(module_name)
        self.plugins[module_name] = module
        if hasattr(module, "init"):
            module.init(self)

    async def profile(self, func: Callable, *args):
        profiler = cProfile.Profile()
        profiler.enable()
        await func(*args)
        profiler.disable()
        stats = pstats.Stats(profiler).sort_stats("cumulative")
        stats.print_stats()

    async def start(self):
        # Initialize world
        self.load_object("ethereal_veil_start", MudObject, "Ethereal Veil Start")
        self.objects["ethereal_veil_start"].add_action("look", lambda obj, caller, arg: "A misty expanse under Mystra's gaze...")

        # Initialize weather and events
        await importlib.import_module("systems.weather").init(self)
        await importlib.import_module("systems.events").init(self)

        # SSL Context
        ssl_context = create_default_context()
        ssl_context.load_cert_chain("cert.pem", "key.pem")

        # Servers
        telnet_server = await telnetlib3.create_server(self.telnet_handler, port=4000, host="::", ssl=ssl_context)
        ws_server = await serve(self.websocket_handler, "::", 4001, ssl=ssl_context)
        rest_task = self.loop.create_task(self.rest_api())
        heartbeat_task = self.loop.create_task(self.heartbeat())

        # Crash Recovery
        def handle_signal(sig, frame):
            logger.info("Shutting down gracefully...")
            self.db.commit()
            asyncio.get_event_loop().stop()
        signal.signal(signal.SIGINT, handle_signal)

        logger.info("PyMudDriver running: Telnet@4000, WS@4001, REST@8080")
        await asyncio.gather(telnet_server.serve_forever(), ws_server, rest_task, heartbeat_task)

# Global driver instance
driver = PyMudDriver()

if __name__ == "__main__":
    asyncio.run(driver.start())
