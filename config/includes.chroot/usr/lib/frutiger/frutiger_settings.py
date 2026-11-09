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
    "wallpaper_mode": "timeofday",     # timeofday | static | custom | slideshow
    "wallpaper": "lagoon-day",         # used when static (a name in the pack)
    "custom_wallpaper": "",            # used when custom (your own picture; a copy kept in CUSTOM_DIR)
    "wallpaper_fit": "fill",           # fill | fit | stretch | center | tile (your own pictures)
    "slideshow_source": "pack",        # pack | folder
    "slideshow_folder": "",            # used when the slideshow source is a folder of your own
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
    # Aero touches
    "aero_shine": "on",                # light sweeps across a title bar when you switch windows
    "aero_peek": "on",                 # taskbar previews + bottom-right corner sees through windows
    "aero_caustics": "on",             # shimmering light on the water in the wallpapers
    "aero_wildlife": "on",             # butterflies, dragonflies, leaves; fireflies at night
    "aero_ripples": "on",              # click the empty desktop for a water ripple
    "aero_ambient": "off",             # soft water and birdsong
    "glass_match": "off",              # glass colour follows the wallpaper
}
MOTION = {"live_effects", "weather_effects", "window_effects",
          "aero_shine", "aero_caustics", "aero_wildlife", "aero_ripples"}   # forced off by Calm mode


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


CUSTOM_DIR = os.path.expanduser("~/.local/share/backgrounds/frutiger-custom")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".svg")
# xfdesktop image-style: 1 centered, 2 tiled, 3 stretched, 4 scaled (fit), 5 zoomed (fill)
FIT_STYLE = {"fill": 5, "fit": 4, "stretch": 3, "center": 1, "tile": 2}


def folder_images(folder):
    """Pictures in a folder of your own (not recursive), sorted by name."""
    try:
        return [os.path.join(folder, f) for f in sorted(os.listdir(folder), key=str.lower)
                if f.lower().endswith(IMAGE_EXT) and not f.startswith(".")]
    except OSError:
        return []


def keep_copy(path):
    """Copy a chosen picture into CUSTOM_DIR so the wallpaper survives the original being moved."""
    if not path or os.path.dirname(os.path.abspath(path)) == CUSTOM_DIR:
        return path
    import shutil
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    dest = os.path.join(CUSTOM_DIR, os.path.basename(path))
    try:
        if not (os.path.exists(dest) and os.path.samefile(path, dest)):
            shutil.copy2(path, dest)
        return dest
    except OSError:
        return path


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
