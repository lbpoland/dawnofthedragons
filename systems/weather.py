# /mnt/home2/mud/systems/weather.py
from typing import Dict, List, Optional, Tuple
from ..driver import driver, MudObject, Player
import math
import random
import time
import os

# Constants adapted from Forgotten Realms and Discworld MUD mechanics
FILE_NAME = "/save/fr_weather"
UPDATE_SPEED = 300  # 5 minutes
CYCLE_SPEED = 3600  # 1 hour
DAYS_PER_YEAR = 365  # Forgotten Realms year (Calendar of Harptos)
SECONDS_PER_DAY = 86400
MINUTES_PER_HOUR = 60
SECONDS_PER_MINUTE = 60
DEFAULT_CLIMATE = "Temperate"  # Default for Faerûn (e.g., Sword Coast)
CLIMATES = ["Tropical", "Arid", "Temperate", "Continental", "Polar", "Highland"]
NOTIFY_TEMPERATURE = 1
NOTIFY_CLOUD = 2
NOTIFY_RAIN = 4
NOTIFY_DAY = 8
TEMP, CLOUD, WINDSP = 0, 1, 2
WEATHER_NO_RAIN_TYPE, WEATHER_SNOW_TYPE, WEATHER_SLEET_TYPE, WEATHER_RAIN_TYPE = 0, 1, 2, 3

class WeatherHandler(MudObject):
    def __init__(self, oid: str = "weather_handler", name: str = "weather_handler"):
        super().__init__(oid, name)
        self._pattern: Dict[str, List[int]] = {}
        self._current: Dict[str, List[int]] = {}
        self._variance: List[int] = [10, 75, 20]  # Temp, cloud, wind variance
        self._rooms: Dict[MudObject, int] = {}
        self._lastupdate: int = 0
        self._day: int = 0
        self._sunrise: int = 0
        self._sunset: int = 0
        self._toy: int = 0  # Time of year
        self.mooncycle: int = 0  # Selûne’s phases
        self.moonupdate: int = 0

    def setup(self):
        """Initializes the weather handler for Forgotten Realms."""
        self.set_name("weather controller")
        self.set_short("weather controller")
        self.set_long("A mystical device attuned to the weather patterns of Faerûn.\n")
        if os.path.exists(FILE_NAME):
            self.restore_object(FILE_NAME)  # Placeholder for file restore
        for climate in CLIMATES:
            self._pattern.setdefault(climate, [0, 0, 0])
            self._current.setdefault(climate, [0, 0, 0])
        driver.call_out(self.update_weather, UPDATE_SPEED)
        self.set_day()
        self.update_pattern()

    def weather_notify(self, room: MudObject, notifications: int) -> bool:
        """Adds a room to the notification list."""
        if notifications < 0 or notifications > (NOTIFY_TEMPERATURE | NOTIFY_CLOUD | NOTIFY_RAIN | NOTIFY_DAY):
            return False
        self._rooms[room] = notifications
        return True

    def day_number(self) -> int:
        """Returns the day of the Faerûnian year (1-365)."""
        return (int(time.time()) % (DAYS_PER_YEAR * SECONDS_PER_DAY)) // SECONDS_PER_DAY + 1

    def minute_number(self) -> int:
        """Returns the minute of the day (0-1439)."""
        return (int(time.time()) % SECONDS_PER_DAY) // SECONDS_PER_MINUTE

    def query_moon_string(self, env: MudObject) -> str:
        """Returns Selûne’s visibility string."""
        if self.mooncycle > 10:
            return "It is night and Selûne is not visible.\n"
        cloud = self.cloud_index(env)
        if cloud > 70:
            return f"It is night and Selûne’s {self.query_moon_phase()} is shrouded by clouds.\n"
        prefix = "The waters" if env.query_water() else "The land"
        return f"{prefix} glow with the silver light of Selûne’s {self.query_moon_phase()}.\n"

    def query_moon_state(self) -> int:
        """Returns Selûne’s state (0-6)."""
        if self.mooncycle < 6:
            return self.mooncycle + 1
        if self.mooncycle < 11:
            return 11 - self.mooncycle
        return 0

    def query_moon_phase(self) -> str:
        """Returns Selûne’s phase."""
        return ["crescent", "quarter", "half", "three quarter", "gibbous", "full",
                "gibbous", "three quarter", "half", "quarter", "crescent", "", "", ""][self.mooncycle]

    def query_stars(self, env: MudObject) -> int:
        """Returns the percentage of visible stars."""
        if self.query_day(env) or self.cloud_index(env) > 70:
            return 0
        cloud = self.cloud_index(env)
        if cloud == 0:
            return 100
        elif 1 <= cloud <= 39:
            return 80
        elif 40 <= cloud <= 59:
            return 40
        elif 60 <= cloud <= 69:
            return 20
        return 10

    def query_star_string(self, env: MudObject) -> str:
        """Returns a description of visible stars."""
        if self.query_day(env):
            return "The sun’s light drowns out the stars.\n"
        stars = self.query_stars(env)
        if 1 <= stars <= 20:
            return "A few brave stars pierce the night sky.\n"
        elif 21 <= stars <= 40:
            return "A scattering of stars dots the heavens.\n"
        elif 41 <= stars <= 60:
            return "Many stars glimmer above Faerûn.\n"
        elif 61 <= stars <= 80:
            return "A host of stars shines brightly.\n"
        elif 81 <= stars <= 100:
            return "The sky blazes with countless stars.\n"
        return "No stars pierce the darkened sky.\n"

    def query_season(self) -> str:
        """Returns the Faerûnian season."""
        day = self.day_number()
        if 335 <= day <= 365 or 1 <= day <= 59:  # Hammer to Alturiak
            return "winter"
        elif 60 <= day <= 150:  # Ches to Tarsakh
            return "spring"
        elif 151 <= day <= 243:  # Mirtul to Eleasis
            return "summer"
        return "autumn"  # Eleint to Nightal

    def query_tod(self) -> str:
        """Returns the time of day."""
        minute = self.minute_number()
        if minute < self._sunrise or minute > self._sunset:
            return "night"
        if 0 <= minute <= 700:
            return "morning"
        elif 701 <= minute <= 740:
            return "midday"
        elif 741 <= minute <= 1080:
            return "afternoon"
        return "evening"

    def query_day(self, env: MudObject) -> int:
        """Returns the day state (0-10)."""
        return self._day

    def query_darkness(self, env: MudObject) -> int:
        """Returns the light percentage."""
        result = 10
        day = self.query_day(env)
        if day == 10:
            return 100
        if self.mooncycle <= 10:
            result += (self.mooncycle * 10 if self.mooncycle < 6 else (5 - (self.mooncycle % 6)) * 10)
        cloud = self.cloud_index(env)
        if cloud > 0:
            result -= cloud // 15
        if result < 0:
            result = 0
        if day > 0:
            result += (100 - result) // (10 - day)
        return result

    def query_visibility(self, env: MudObject) -> int:
        """Returns the visibility percentage."""
        result = 100
        temp = self.temperature_index(env)
        rain = self.rain_index(env)
        rt = self.query_rain_type(temp, rain)
        if rt == WEATHER_SNOW_TYPE:
            rain += 50
        elif rt == WEATHER_SLEET_TYPE:
            rain += 20
        if rain > 0:
            result = 0 if rain > 100 else (result * (100 - rain)) // 100
        return result

    def calc_actual(self, env: MudObject, type: int) -> int:
        """Calculates the actual weather value."""
        climate = env.query_climate() or DEFAULT_CLIMATE
        clim = env.query_property("climate") or [0, 0, 0]
        return self._current[climate][type] + clim[type]

    def temperature_index(self, env: MudObject) -> int:
        """Calculates the temperature with diurnal effects."""
        temp = self.calc_actual(env, TEMP)
        climate = env.query_climate() or DEFAULT_CLIMATE
        tod = 10 - self.query_day(env)
        if tod:
            diurnal = {
                "Tropical": 10, "Arid": lambda t: 15 + (t // 2),
                "Temperate": 15, "Continental": 15, "Polar": 20, "Highland": 20
            }.get(climate, 15)
            if callable(diurnal):
                diurnal = diurnal(self._pattern[climate][0])
            temp -= (diurnal * tod) // 10
        j = int(math.sqrt(max(0, self._current[climate][CLOUD])))
        if temp < 10 and tod == 10:
            temp += j
        elif temp > 30 and not tod:
            temp -= j
        temp -= int(math.sqrt(self._current[climate][WINDSP]))
        return temp

    def cloud_index(self, env: MudObject) -> int:
        """Calculates the cloud cover."""
        return max(0, self.calc_actual(env, CLOUD))

    def rain_index(self, env: MudObject) -> int:
        """Calculates the rain intensity."""
        rain = self.calc_actual(env, CLOUD) - (self.calc_actual(env, TEMP) // 2) - 100
        return max(0, rain)

    def temp_string(self, temp: int) -> str:
        """Returns a temperature description."""
        if temp >= 51:
            return "blazing beyond mortal endurance"
        elif 46 <= temp <= 50:
            return "scorching like the deserts of Calimshan"
        elif 41 <= temp <= 45:
            return "sweltering as in Chult"
        elif 36 <= temp <= 40:
            return "very hot"
        elif 31 <= temp <= 35:
            return "hot"
        elif 26 <= temp <= 30:
            return "warm as a summer day"
        elif 23 <= temp <= 25:
            return "pleasantly warm"
        elif 20 <= temp <= 22:
            return "mild"
        elif 16 <= temp <= 19:
            return "cool as an autumn breeze"
        elif 13 <= temp <= 15:
            return "chilly"
        elif 10 <= temp <= 12:
            return "brisk"
        elif 7 <= temp <= 9:
            return "cold"
        elif 4 <= temp <= 6:
            return "very cold"
        elif 1 <= temp <= 3:
            return "bitterly cold"
        elif -3 <= temp <= 0:
            return "frigid"
        elif -10 <= temp <= -4:
            return "freezing as in Icewind Dale"
        elif -20 <= temp <= -11:
            return "numbing"
        elif -30 <= temp <= -21:
            return "deadly cold"
        return "glacial like the Reghed wastes"

    def precipitation_string(self, rain: int, rt: int, wind: int) -> str:
        """Returns a precipitation intensity description."""
        if -1000 <= rain <= 20:
            return "lightly"
        elif 21 <= rain <= 40:
            return "steadily" if wind < 20 else "hard"
        elif 41 <= rain <= 60:
            return "heavily"
        return "torrentially" if rt == WEATHER_RAIN_TYPE else "very heavily"

    def rain_string(self, env: MudObject) -> str:
        """Returns the rain description."""
        temp = self.temperature_index(env)
        rain = self.rain_index(env)
        rt = self.query_rain_type(temp, rain)
        wind = self.calc_actual(env, WINDSP)
        return f"Rain falls {self.precipitation_string(rain, rt, wind)} across the land" if rt == WEATHER_RAIN_TYPE else "The skies are dry"

    def snow_string(self, env: MudObject) -> str:
        """Returns the snow description."""
        temp = self.temperature_index(env)
        rain = self.rain_index(env)
        rt = self.query_rain_type(temp, rain)
        wind = self.calc_actual(env, WINDSP)
        return f"Snow falls {self.precipitation_string(rain, rt, wind)} from the heavens" if rt == WEATHER_SNOW_TYPE else "No snow blankets the ground"

    def sleet_string(self, env: MudObject) -> str:
        """Returns the sleet description."""
        temp = self.temperature_index(env)
        rain = self.rain_index(env)
        rt = self.query_rain_type(temp, rain)
        wind = self.calc_actual(env, WINDSP)
        return f"Sleet pelts the land {self.precipitation_string(rain, rt, wind)}" if rt == WEATHER_SLEET_TYPE else "The air is free of sleet"

    def cloud_string(self, env: MudObject) -> str:
        """Returns the cloud description."""
        cloud = self.cloud_index(env)
        if -1000 <= cloud <= 5:
            return "a clear Faerûnian sky"
        elif 6 <= cloud <= 10:
            return " wisps of cirrus clouds"
        elif 11 <= cloud <= 25:
            return "scattered clouds like those over Waterdeep"
        elif 26 <= cloud <= 40:
            return "light cloud cover"
        elif 41 <= cloud <= 60:
            return "a canopy of clouds"
        elif 61 <= cloud <= 80:
            return "thick clouds"
        elif 81 <= cloud <= 110:
            return "dense, brooding clouds"
        elif 111 <= cloud <= 130:
            return "ominous gray cover"
        elif 131 <= cloud <= 160:
            return "dark storm clouds"
        return "tempestuous storm clouds"

    def weather_string(self, env: MudObject, obscured: Optional[str] = None) -> str:
        """Returns the full weather description for Forgotten Realms."""
        temp = self.temperature_index(env)
        cloud = self.cloud_index(env)
        wind = self.calc_actual(env, WINDSP)
        rain = self.rain_index(env)
        if hasattr(env, "room_weather"):
            temp, cloud, wind, rain = env.room_weather(temp, cloud, wind, rain)
        rt = self.query_rain_type(temp, rain)

        str_ = "The air is "
        tstr = self.temp_string(temp)
        str_ += f"an {tstr} " if tstr[0] in "aeiou" else f"a {tstr} "
        str_ += f"{self.query_season()}’s {self.query_tod()} with "
        str_ += {
            range(-1000, 6): "calm stillness",
            range(6, 11): "a gentle breeze",
            range(11, 16): "a steady wind",
            range(16, 21): "a strong gust",
            range(21, 31): "a howling wind",
            range(31, 41): "fierce gusts",
            range(41, 51): "storm winds",
            range(51, 61): "gale-force winds",
            range(61, 1001): "a roaring tempest"
        }.get(next(r for r in [range(-1000, 6), range(6, 11), range(11, 16), range(16, 21),
                              range(21, 31), range(31, 41), range(41, 51), range(51, 61),
                              range(61, 1001)] if wind in r), "no wind")

        if not obscured:
            str_ += ", " if rain else " beneath "
            str_ += self.cloud_string(env)

        if rain:
            str_ += " and "
            intensity = "light" if rain <= 20 else ("steady" if rain <= 40 and wind < 20 else "driving" if rain <= 40 else "heavy" if rain <= 60 else "torrential" if rt == WEATHER_RAIN_TYPE else "very heavy")
            str_ += f"{intensity} {['', 'snow', 'sleet', 'rain'][rt]}"

        if obscured:
            str_ += f". {obscured}"
        if rain > 20 and wind > 30:
            str_ += ".\nThunder rumbles across the sky" if obscured else ".\nLightning splits the heavens with thunderous roars"
        return str_

    def query_rain_type(self, temp: int, rain: int) -> int:
        """Determines the precipitation type."""
        if rain <= 0:
            return WEATHER_NO_RAIN_TYPE
        if temp <= -2:
            return WEATHER_SNOW_TYPE
        elif -1 <= temp <= 3:
            return WEATHER_SLEET_TYPE
        return WEATHER_RAIN_TYPE

    def query_snowing(self, env: MudObject) -> bool:
        """Checks if it’s snowing."""
        temp, rain = self._get_weather_values(env)
        return self.query_rain_type(temp, rain) == WEATHER_SNOW_TYPE

    def query_raining(self, env: MudObject) -> bool:
        """Checks if it’s raining."""
        temp, rain = self._get_weather_values(env)
        return self.query_rain_type(temp, rain) > WEATHER_SNOW_TYPE

    def query_temperature(self, env: MudObject) -> int:
        """Returns the temperature."""
        return self._get_weather_values(env)[0]

    def query_cloud(self, env: MudObject) -> int:
        """Returns the cloud cover."""
        return self._get_weather_values(env)[1]

    def query_windsp(self, env: MudObject) -> int:
        """Returns the wind speed."""
        return self._get_weather_values(env)[2]

    def _get_weather_values(self, env: MudObject) -> Tuple[int, int, int]:
        """Helper to get weather values with room overrides."""
        temp = self.temperature_index(env)
        cloud = self.cloud_index(env)
        wind = self.calc_actual(env, WINDSP)
        rain = self.rain_index(env)
        if hasattr(env, "room_weather"):
            temp, cloud, wind, rain = env.room_weather(temp, cloud, wind, rain)
        return temp, cloud, wind

    def calc_variance(self, climate: str, type: int, seasonal: int) -> int:
        """Calculates weather variance."""
        diff = seasonal - self._pattern[climate][type]
        ret = random.randint(0, diff * 2) * (-1 if diff < 0 else 1)
        ret += random.randint(0, self._variance[type]) if random.randint(0, 2) else -random.randint(0, self._variance[type])
        return ret

    def set_day(self):
        """Sets the day state based on Faerûnian time."""
        self._toy = self.day_number()
        min_ = self.minute_number()
        self._sunrise = 6 * MINUTES_PER_HOUR + (182 - self._toy if self._toy < 183 else self._toy - 182) // 2
        self._sunset = 18 * MINUTES_PER_HOUR - (182 - self._toy if self._toy < 183 else self._toy - 182) // 2
        if min_ <= self._sunrise or min_ >= self._sunset:
            self._day = 0
        else:
            self._day = (min_ - self._sunrise) // 3 if self._sunrise < min_ < self._sunrise + 30 else \
                        (self._sunset - min_) // 3 if self._sunset - 30 < min_ < self._sunset else 10

    def migrate(self, climate: str, type: int):
        """Migrates current weather towards the pattern."""
        diff = self._pattern[climate][type] - self._current[climate][type]
        if diff > self._variance[type] // 2:
            diff = self._variance[type] // 2
        self._current[climate][type] += -random.randint(0, -diff) if diff < 0 else random.randint(0, diff)

    def update_pattern(self):
        """Updates the weather pattern hourly for Forgotten Realms."""
        driver.call_out(self.update_pattern, CYCLE_SPEED)
        toy = self._toy
        for climate in CLIMATES:
            temp, cloud, wind = {
                "Tropical": (30 + (toy // 36), 50 + random.randint(0, 100), random.randint(0, 10)),  # Chult-like
                "Arid": (35 + (toy // 36), (100 - toy // 4) - 50, random.randint(0, 15)),  # Calimshan
                "Temperate": (toy // 6 - 5, (182 - toy if toy < 183 else toy - 182) // 2 - 25, 10 - (toy // 36)),  # Sword Coast
                "Continental": (toy // 5 - 10, (365 - toy) // 4 + 50, 15 - (toy // 36)),  # Damara
                "Polar": (toy // 36 - 20, (182 - toy if toy < 183 else toy - 182) // 2 - 25, 20 - (toy // 36)),  # Icewind Dale
                "Highland": (toy // 10 - 15, (182 - toy if toy < 183 else toy - 182) // 2, 25 - (toy // 36))  # Spine of the World
            }[climate]
            tvar, cvar, wvar = [self.calc_variance(climate, i, v) for i, v in enumerate([temp, cloud, wind])]
            self._pattern[climate] = [temp + tvar, cloud + cvar, wind + wvar]
        self.save_object(FILE_NAME)

    def update_weather(self):
        """Updates the current weather every 5 minutes."""
        self._lastupdate = int(time.time())
        driver.call_out(self.update_weather, UPDATE_SPEED)
        list_ = {}
        roomlist = {}
        for user in [u for u in driver.users() if u and u.environment() and u.environment().query_property("location") == "outside"]:
            temp, cloud, wind = self._get_weather_values(user.environment())
            list_[user] = [temp, cloud, self.rain_index(user.environment()), self._day]
        newrooms = {r: n for r, n in self._rooms.items() if r}
        self._rooms = newrooms
        for room, notifications in self._rooms.items():
            temp, cloud, wind = self._get_weather_values(room)
            roomlist[room] = [temp, cloud, self.rain_index(room), self._day]

        if self.moonupdate + (SECONDS_PER_DAY * 2) < int(time.time()):
            self.mooncycle = (self.mooncycle + 1) % 14  # Selûne’s 28-day cycle, approximated
            self.moonupdate = int(time.time())

        for climate in CLIMATES:
            for type_ in [TEMP, CLOUD, WINDSP]:
                self.migrate(climate, type_)
        self.set_day()
        self.save_object(FILE_NAME)

        for user, warray in list_.items():
            self.do_inform(user, *warray)
        for room, notifications in self._rooms.items():
            self.do_room_inform(room, *roomlist[room], notifications)

    def do_inform(self, who: Player, old_temp: int, old_cloud: int, old_rain: int, old_day: int):
        """Informs players of weather changes."""
        temp, cloud, wind = self._get_weather_values(who.environment())
        new_rain = self.rain_index(who.environment())
        old_rt = self.query_rain_type(old_temp, old_rain)
        new_rt = self.query_rain_type(temp, new_rain)
        str_ = ""
        if self._day != old_day:
            where = self.sun_direction(1)  # Sunset
            if old_day == 10 and self._day < 10:
                str_ += f"The sun dips toward the {where} horizon.\n"
            elif old_day > 0 and self._day == 0:
                str_ += f"Darkness falls as the sun sets {where}.\n"
            elif old_day > self._day and 0 < self._day < 9:
                str_ += f"The sun sinks lower in the {where} sky.\n"
            where = self.sun_direction(0)  # Sunrise
            if self._day > 0 and old_day == 0:
                str_ += f"A faint glow rises {where} as dawn nears.\n"
            elif self._day == 10 and old_day < 10:
                str_ += f"The sun climbs {where}, heralding day.\n"
            elif self._day > old_day and 0 < self._day < 9:
                str_ += f"Light strengthens {where} with morning’s advance.\n"
        if self._day and old_cloud != cloud:
            if old_cloud < 60 and cloud > 20 and not cloud % 2:
                str_ += f"The {self.query_tod()} sun vanishes behind clouds.\n"
            elif old_cloud > 20 and cloud < 60 and cloud % 2:
                str_ += f"The {self.query_tod()} sun breaks through the clouds.\n"
        if old_rt != new_rt:
            str_ += ["", "The snow ceases", "The sleet stops", "The rain ends"][old_rt]
            str_ += " and " if old_rt and new_rt else " " if new_rt else ""
            str_ += ["", "snow begins to fall", "sleet starts", "rain begins"][new_rt] + ".\n"
        elif new_rt > 0:
            str_ += f"The {['', 'snow', 'sleet', 'rain'][new_rt]} persists.\n"
        if new_rt and not any(o.query_property("umbrella") for o in who.query_holding() + who.query_wearing()) or not random.randint(0, 50):
            who.add_effect("/std/effects/other/wetness", (new_rain * new_rt // 2) * (UPDATE_SPEED // 60))
        if str_:
            who.tell(f"ORANGE: {str_}\n")

    def do_room_inform(self, room: MudObject, old_temp: int, old_cloud: int, old_rain: int, old_day: int, notifications: int):
        """Informs rooms of weather changes."""
        temp, cloud, wind = self._get_weather_values(room)
        new_rain = self.rain_index(room)
        has_changed = 0
        if self._day != old_day and notifications & NOTIFY_DAY:
            has_changed |= NOTIFY_DAY
        if old_temp != temp and notifications & NOTIFY_TEMPERATURE:
            has_changed |= NOTIFY_TEMPERATURE
        if old_cloud != cloud and notifications & NOTIFY_CLOUD:
            has_changed |= NOTIFY_CLOUD
        if old_rain != new_rain and notifications & NOTIFY_RAIN:
            has_changed |= NOTIFY_RAIN
        if has_changed:
            driver.call_out(lambda: self.notify_room(room, has_changed, self._day, temp, cloud, new_rain), 1)

    def notify_room(self, room: MudObject, has_changed: int, day: int, temp: int, cloud: int, rain: int):
        """Notifies a room of weather changes."""
        if room:
            room.event_weather(has_changed, day, temp, cloud, rain)

    def sun_direction(self, which: int) -> str:
        """Returns the sun direction (0 for sunrise, 1 for sunset)."""
        day = self.day_number()
        # Simplified directions based on Faerûn’s geography
        if 1 <= day <= 91 or 275 <= day <= 365:  # Winter
            return "eastern" if which == 0 else "western"
        elif 92 <= day <= 182:  # Spring
            return "northeastern" if which == 0 else "southwestern"
        elif 183 <= day <= 274:  # Summer
            return "northern" if which == 0 else "southern"
        return "southeastern" if which == 0 else "northwestern"  # Autumn

    def query_sunrise(self, doy: int) -> int:
        """Returns sunrise time in seconds past midnight."""
        adjust = (182 - doy if doy < 183 else doy - 182) // 2
        return (6 * MINUTES_PER_HOUR) + adjust

    def query_sunset(self, doy: int) -> int:
        """Returns sunset time in seconds past midnight."""
        adjust = (182 - doy if doy < 183 else doy - 182) // 2
        return (18 * MINUTES_PER_HOUR) - adjust

    def save_object(self, filename: str):
        """Placeholder for saving state."""
        pass

    def restore_object(self, filename: str):
        """Placeholder for restoring state."""
        pass

async def init(driver_instance):
    driver = driver_instance
    driver.weather_handler = WeatherHandler()
    driver.weather_handler.setup()
