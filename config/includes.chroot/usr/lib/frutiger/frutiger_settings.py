"""Frutiger OS desktop settings (~/.config/frutiger/desktop.ini), shared by
Personalize, the Welcome Center, frutiger-desktopd, frutiger-gadgets and the session.

Every feature has its own switch; Calm mode turns off all motion at once
(live wallpaper effects, weather effects, animated screensaver, window fades,
time-of-day/slideshow changes) without touching the individual switches.
"""
import configparser, os

PATH = os.path.expanduser("~/.config/frutiger/desktop.ini")
BG = "/usr/share/backgrounds/frutiger"

DEFAULTS = {
    "wallpaper_mode": "timeofday",     # timeofday | static | slideshow
    "wallpaper": "lagoon-day",         # used when static (a name in the pack)
    "slideshow_minutes": "15",
    "live_effects": "on",              # rising bubbles + ripples over the wallpaper
    "weather_effects": "off",          # rain / snow over the wallpaper (needs a city; uses the internet)
    "weather_city": "",
    "weather_lat": "",
    "weather_lon": "",
    "gadgets": "on",                   # master switch for desktop gadgets
    "gadget_clock": "on",
    "gadget_weather": "on",
    "gadget_cpu": "on",
    "gadget_notes": "off",
    "gadget_slideshow": "off",
    "sounds": "on",
    "click_sounds": "off",
    "screensaver": "on",
    "screensaver_minutes": "10",
    "window_effects": "on",            # window fades / glass open-close
    "calm_mode": "off",
}
MOTION = {"live_effects", "weather_effects", "window_effects"}   # forced off by Calm mode


def load():
    cp = configparser.ConfigParser()
    cp.read_dict({"desktop": DEFAULTS})
    cp.read(PATH)
    return dict(cp["desktop"])


def save(values):
    cp = configparser.ConfigParser()
    merged = dict(DEFAULTS)
    merged.update({k: str(v) for k, v in values.items()})
    cp["desktop"] = merged
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        cp.write(f)
    os.replace(tmp, PATH)


def on(cfg, key):
    """Effective on/off for a switch, with Calm mode applied."""
    if key in MOTION and cfg.get("calm_mode") == "on":
        return False
    if key == "wallpaper_dynamic":
        return cfg.get("calm_mode") != "on"
    return cfg.get(key, DEFAULTS.get(key, "off")) == "on"


def mtime():
    try:
        return os.path.getmtime(PATH)
    except OSError:
        return 0


def pack():
    """Wallpaper pack: name -> path."""
    d = os.path.join(BG, "pack")
    try:
        return {os.path.splitext(f)[0]: os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith((".jpg", ".png"))}
    except FileNotFoundError:
        return {}


def time_of_day(hour):
    if 5 <= hour < 8:
        return "lagoon-dawn"
    if 8 <= hour < 17:
        return "lagoon-day"
    if 17 <= hour < 20:
        return "lagoon-sunset"
    return "lagoon-night"
