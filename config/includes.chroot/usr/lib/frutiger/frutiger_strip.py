"""Shared engine for Frutiger OS taskbar strips.

Used by Aquarium Rail, Leaf Shelf, Cloud Bar, Glass Bead String, Aurora Ribbon
(screen edges), Vista Sidebar (right edge), Sundial Clock and Lily Pond (corner).

A strip is a borderless, always-on-top dock window. Edge strips reserve space
(so maximized windows stop short of them); corner widgets float. It shows one
item per app — pinned apps plus any running app — and animates them.

Subclasses implement:
    EDGE      "bottom" (default), "top", "right" or "corner"
    STRIP_H   thickness of the reserved/clickable strip (px); width for "right"
    EXTRA_H   transparent, click-through headroom beside it (hover lifts/labels):
              above for bottom, below for top, to the left for right
    CORNER_W, CORNER_H   size of a corner widget (EDGE == "corner")
    draw_background(cr, w, h, top, t)
    draw_item(cr, item, x, y, t, hover)      x, y = item centre
    item_radius                              hit-test radius
    item_pos(i, n, item, w, top, t)          -> (x, y)

Shared behaviour:
    left click   launch / focus / minimize / cycle windows
    middle click close the app's windows
    right click  pin / unpin
    orb (left end)  opens the Start menu (Whisker Menu); right-click = Personalize
    hover        Aero Peek: a live glass thumbnail of the app's windows; rest on a thumbnail
                 and every other window turns to faint glass
    press        items squish like jelly (not in Calm mode)
"""
import math, os, subprocess, time
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gtk, Gdk, GdkX11, GdkPixbuf, Gio, GLib, Wnck  # noqa: F401
import cairo
import sys
sys.path.insert(0, "/usr/lib/frutiger")
import frutiger_settings as fs
import frutiger_peek as peek

HOME = os.path.expanduser("~")
CONF = os.path.join(HOME, ".config/frutiger")
PIN_FILE = os.path.join(CONF, "orbit-pins")   # shared by Orbit, Aquarium Rail, Leaf Shelf
ORB_IMG = "/usr/share/frutiger/start-orb.png"
DEFAULT_PINS = ["thunar.desktop", "firefox-esr.desktop", "xfce4-terminal.desktop",
                "org.xfce.mousepad.desktop", "frutiger-personalize.desktop"]
SELF_TITLES = {"Frutiger Orbit", "Frutiger Aquarium", "Frutiger Leaf Shelf", "Frutiger Peek"}
_cfg = [0.0, {}]


def setting_on(key):
    """Effective on/off for a desktop.ini switch (Calm mode applied), re-read every few seconds."""
    if time.monotonic() - _cfg[0] > 3:
        _cfg[0], _cfg[1] = time.monotonic(), fs.load()
    return fs.on(_cfg[1], key)


def jelly_scale(age):
    """The press 'squish': (sx, sy) for a press `age` seconds ago (0.46 s long)."""
    keys = ((0, 1, 1), (.22, 1.13, .85), (.46, .94, 1.08), (.70, 1.03, .97), (1, 1, 1))
    p = age / .46
    if not 0 <= p < 1:
        return None
    for (p0, x0, y0), (p1, x1, y1) in zip(keys, keys[1:]):
        if p0 <= p <= p1:
            k = (p - p0) / (p1 - p0)
            return x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    return None


class PeekPopup(Gtk.Window):
    """Aero Peek thumbnails for one taskbar item: a glass card with a live preview of each window."""
    TW, TH, PAD = 190, 120, 10

    def __init__(self, strip):
        super().__init__(type=Gtk.WindowType.POPUP)
        self.strip, self.item, self.pix, self.rects = strip, None, [], []
        self.set_title("Frutiger Peek")
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_press)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("enter-notify-event", lambda *a: self.strip.peek_hold(True))
        self.connect("leave-notify-event", self.on_leave)
        self.hot, self.peek_timer, self.refresh_timer = None, 0, 0

    def show_for(self, item, x, y, edge):
        self.item = item
        wins = item.windows[:3]
        n = max(1, len(wins))
        W = self.PAD + n * (self.TW + self.PAD)
        H = self.TH + 2 * self.PAD + 20
        self.size = (W, H)
        self.set_size_request(W, H)
        self.resize(W, H)
        g = self.strip.mon
        if edge == "right":
            px, py = x - W - 16, y - H / 2
        elif edge == "top":
            px, py = x - W / 2, y + 40
        else:
            px, py = x - W / 2, y - H - 34
        px = max(g.x + 4, min(g.x + g.width - W - 4, px))
        py = max(g.y + 4, min(g.y + g.height - H - 4, py))
        self.move(int(px), int(py))
        self.grab()
        self.show_all()
        try:
            self.get_window().shape_combine_region(peek_shape(W, H), 0, 0) if not self.get_screen().is_composited() else None
        except Exception:
            pass
        if not self.refresh_timer:
            self.refresh_timer = GLib.timeout_add(1000, self.regrab)

    def grab(self):
        self.pix = [(w, peek.capture(w.get_xid(), self.TW, self.TH)) for w in self.item.windows[:3]] if self.item else []
        self.queue_draw()

    def regrab(self):
        if not self.get_visible():
            self.refresh_timer = 0
            return False
        self.grab()
        return True

    def hide_now(self):
        if self.peek_timer:
            GLib.source_remove(self.peek_timer)
            self.peek_timer = 0
        peek.unpeek()
        self.hot = None
        self.hide()

    def on_draw(self, _w, cr):
        W, H = self.size
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        rounded(cr, .5, .5, W - 1, H - 1, 10)
        r, g, b = accent()
        grad = cairo.LinearGradient(0, 0, 0, H)
        grad.add_color_stop_rgba(0, min(1, r + .35), min(1, g + .35), min(1, b + .35), .82)
        grad.add_color_stop_rgba(.5, r, g, b, .72)
        grad.add_color_stop_rgba(1, r * .8, g * .8, b * .8, .8)
        cr.set_source(grad)
        cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, .7)
        cr.set_line_width(1)
        cr.stroke()
        self.rects = []
        for i, (w, pix) in enumerate(self.pix):
            x0, y0 = self.PAD + i * (self.TW + self.PAD), self.PAD + 18
            cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(11)
            name = w.get_name() or ""
            name = name if len(name) < 30 else name[:28] + "…"
            cr.set_source_rgba(0, 0, 0, .5)
            cr.move_to(x0 + 1, y0 - 6)
            cr.show_text(name)
            cr.set_source_rgba(1, 1, 1, 1)
            cr.move_to(x0, y0 - 7)
            cr.show_text(name)
            if pix:
                pw, ph = pix.get_width(), pix.get_height()
                px, py = x0 + (self.TW - pw) / 2, y0 + (self.TH - ph) / 2
                Gdk.cairo_set_source_pixbuf(cr, pix, px, py)
                cr.paint()
            else:                                  # minimized: show the app's icon
                pw = ph = 64
                px, py = x0 + (self.TW - pw) / 2, y0 + (self.TH - ph) / 2
                icon = self.strip.icon_for(self.item, 64)
                if icon:
                    Gdk.cairo_set_source_pixbuf(cr, icon, px, py)
                    cr.paint_with_alpha(.85)
            cr.rectangle(px - .5, py - .5, pw + 1, ph + 1)
            cr.set_source_rgba(1, 1, 1, .9 if self.hot is w else .55)
            cr.set_line_width(2 if self.hot is w else 1)
            cr.stroke()
            self.rects.append((w, x0, y0, self.TW, self.TH))
        return False

    def window_at(self, x, y):
        for w, x0, y0, tw, th in self.rects:
            if x0 <= x <= x0 + tw and y0 <= y <= y0 + th:
                return w
        return None

    def on_motion(self, _w, ev):
        w = self.window_at(ev.x, ev.y)
        if w is not self.hot:
            self.hot = w
            self.queue_draw()
            if self.peek_timer:
                GLib.source_remove(self.peek_timer)
                self.peek_timer = 0
            if w is None:
                peek.unpeek()
            else:
                self.peek_timer = GLib.timeout_add(450, self.start_peek, w)

    def start_peek(self, w):
        self.peek_timer = 0
        if self.hot is w and not w.is_minimized():
            peek.peek({w.get_xid()})
        return False

    def on_leave(self, *_):
        self.hot = None
        peek.unpeek()
        self.strip.peek_hold(False)

    def on_press(self, _w, ev):
        w = self.window_at(ev.x, ev.y)
        ts = ev.time or Gtk.get_current_event_time()
        self.hide_now()
        if w:
            w.activate(ts)
        return True


def peek_shape(W, H):
    return shape_region(rects=[(0, 0, W, H)])


# ---------------------------------------------------------------- settings
def accent():
    try:
        h = open(os.path.join(CONF, "accent")).read().strip().lstrip("#")
        return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return (0x2a / 255, 0xa7 / 255, 0xe8 / 255)


def app_info(did):
    try:
        return Gio.DesktopAppInfo.new(did)
    except TypeError:
        return None


def load_pins():
    try:
        ids = [l.strip() for l in open(PIN_FILE) if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        ids = DEFAULT_PINS
    return [a for a in (app_info(i) for i in ids) if a]


def save_pins(ids):
    os.makedirs(CONF, exist_ok=True)
    with open(PIN_FILE, "w") as f:
        f.write("\n".join(ids) + "\n")


def app_for_window(w):
    """Best guess at the .desktop entry behind a window (WM_CLASS matching)."""
    names = [n for n in (w.get_class_instance_name(), w.get_class_group_name()) if n]
    for n in names:
        for cand in (n + ".desktop", n.lower() + ".desktop"):
            info = app_info(cand)
            if info:
                return info
    lowered = {n.lower() for n in names}
    for info in Gio.AppInfo.get_all():
        if isinstance(info, Gio.DesktopAppInfo):
            wm = (info.get_startup_wm_class() or "").lower()
            if wm and wm in lowered:
                return info
    for n in names:
        for group in Gio.DesktopAppInfo.search(n):
            for did in group:
                info = app_info(did)
                if info:
                    return info
    return None


def shape_region(circles=(), rects=(), ellipses=()):
    """A cairo.Region made of circles (x, y, r), rectangles (x, y, w, h) and
    ellipses (x, y, rx, ry), built from 3-px stripes. Used as the window's
    shape so only what's drawn exists on screen — no box around the widget
    even when no compositor is running (VMs, old graphics)."""
    reg = cairo.Region()
    for x, y, w, h in rects:
        reg.union(cairo.RectangleInt(int(x), int(y), max(1, int(w)), max(1, int(h))))
    for x, y, r in circles:
        ellipses = list(ellipses) + [(x, y, r, r)]
    for x, y, rx, ry in ellipses:
        for yy in range(int(y - ry), int(y + ry) + 1, 3):
            k = 1 - ((yy + 1.5 - y) / max(1, ry)) ** 2
            if k > 0:
                half = rx * math.sqrt(k)
                reg.union(cairo.RectangleInt(int(x - half), yy, max(1, int(2 * half)), 3))
    return reg


def set_strut(gtkwin, side, size, start, end):
    """Reserve `size` px along one screen edge (EWMH strut) via python3-xlib.
    side: "bottom" | "top" | "right"; start/end: the span along that edge."""
    try:
        from Xlib import display as xdisplay, Xatom
        gw = gtkwin.get_window()
        idx = {"right": 1, "top": 2, "bottom": 3}[side]
        strut = [0, 0, 0, 0]
        strut[idx] = size
        partial = strut + [0] * 8
        partial[4 + idx * 2] = start          # *_start
        partial[5 + idx * 2] = end            # *_end
        d = xdisplay.Display()
        xw = d.create_resource_object("window", gw.get_xid())
        xw.change_property(d.intern_atom("_NET_WM_STRUT"), Xatom.CARDINAL, 32, strut)
        xw.change_property(d.intern_atom("_NET_WM_STRUT_PARTIAL"), Xatom.CARDINAL, 32, partial)
        d.flush()
    except Exception as e:  # never crash the taskbar over a strut
        print("strut:", e)


# ---------------------------------------------------------------- model
class Item:
    """One app on the strip: a pinned launcher and/or its open windows."""
    def __init__(self, app, key):
        self.app, self.key = app, key
        self.windows = []
        self.pinned = False
        self.seed = (sum(map(ord, key)) % 997) / 997.0   # stable per-app randomness

    @property
    def running(self):
        return bool(self.windows)

    @property
    def active(self):
        return any(w.is_active() for w in self.windows)

    @property
    def attention(self):
        return any(w.needs_attention() for w in self.windows)

    @property
    def label(self):
        if self.app:
            return self.app.get_display_name()
        return self.windows[0].get_name() if self.windows else "?"


# ---------------------------------------------------------------- the strip window
class Strip(Gtk.Window):
    TITLE = "Frutiger Strip"
    EDGE = "bottom"
    STRIP_H = 64
    EXTRA_H = 40
    CORNER_W, CORNER_H = 260, 280
    ORB = 52            # start-orb size (0 = none)
    CLOCK = True
    FPS = 24
    item_radius = 28

    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title(self.TITLE)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.stick()
        self.set_app_paintable(True)
        vis = self.get_screen().get_rgba_visual()
        if vis:
            self.set_visual(vis)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK |
                        Gdk.EventMask.LEAVE_NOTIFY_MASK)
        self.connect("draw", self.on_draw)
        self.connect("button-press-event", self.on_press)
        self.connect("motion-notify-event", self.on_motion)
        self.connect("leave-notify-event", lambda *a: self.set_hover(None))
        self.connect("realize", lambda *a: GLib.idle_add(self.after_realize))

        self.icon_theme = Gtk.IconTheme.get_default()
        self.icon_theme.connect("changed", lambda *a: (self.icon_cache.clear(), self.queue_draw()))
        self.icon_cache, self.app_cache = {}, {}
        self.orb = GdkPixbuf.Pixbuf.new_from_file_at_size(ORB_IMG, 52, 52)
        self.screen = Wnck.Screen.get_default()
        for sig in ("window-opened", "window-closed", "active-window-changed"):
            self.screen.connect(sig, lambda *a: self.refresh())
        self.items, self.pos = [], {}
        self._label_rect = None
        self.hover = None
        self.jelly = {}                 # item key -> press time
        self.peek_popup, self.peek_timer, self.peek_hide_timer, self.peek_inside = None, 0, 0, False
        self.t0 = time.monotonic()
        self.place()
        self.refresh()
        GLib.timeout_add(int(1000 / self.FPS), self.tick)
        GLib.timeout_add_seconds(10, lambda: (self.queue_draw(), True)[1])   # clock
        self.show_all()

    # ---- geometry
    def place(self):
        disp = Gdk.Display.get_default()
        mon = disp.get_primary_monitor() or disp.get_monitor(0)
        g = mon.get_geometry()
        self.mon = g
        S, E = self.STRIP_H, self.EXTRA_H
        if self.EDGE == "bottom":
            self.W, self.H = g.width, S + E
            self.rect = (0, E, self.W, S)                 # the strip itself, in window coords
            pos = (g.x, g.y + g.height - self.H)
        elif self.EDGE == "top":
            self.W, self.H = g.width, S + E
            self.rect = (0, 0, self.W, S)
            pos = (g.x, g.y)
        elif self.EDGE == "right":
            self.W, self.H = S + E, g.height
            self.rect = (E, 0, S, self.H)
            pos = (g.x + g.width - self.W, g.y)
        else:                                             # corner widget, bottom-left of the work area
            wa = mon.get_workarea()
            self.W, self.H = self.CORNER_W, self.CORNER_H
            self.rect = (0, 0, self.W, self.H)
            pos = (wa.x + 6, wa.y + wa.height - self.H - 6)
        self.top = self.rect[1]                           # kept for older subclasses (y where the strip starts)
        self.orb_hit = self.orb_center() + (self.ORB / 2,)
        self.set_size_request(self.W, self.H)
        self.resize(self.W, self.H)
        self.move(*pos)

    def orb_center(self):
        x, y, w, h = self.rect
        if self.EDGE == "right":
            return (x + w / 2, 14 + self.ORB / 2)
        return (14 + self.ORB / 2, y + h / 2)

    def hover_offset(self):
        return {"top": (0, 8), "right": (-8, 0)}.get(self.EDGE, (0, -10))

    def after_realize(self):
        x, y, w, h = self.rect
        g = self.mon
        if self.EDGE == "bottom":
            set_strut(self, "bottom", h, g.x, g.x + g.width - 1)
        elif self.EDGE == "top":
            set_strut(self, "top", h, g.x, g.x + g.width - 1)
        elif self.EDGE == "right":
            set_strut(self, "right", w, g.y, g.y + g.height - 1)
        self.apply_shape()
        return False

    def base_shape(self):
        """Shape parts that are always there: (circles, rects, ellipses)."""
        return [], [self.rect], []

    def apply_shape(self, label_rect=None):
        circles, rects, ellipses = self.base_shape()
        circles = list(circles) + [(x, y, self.item_radius + 14) for x, y in self.pos.values()]
        if self.ORB:
            ox, oy = self.orb_center()
            circles.append((ox, oy, self.ORB / 2 + 2))
        rects = list(rects) + ([label_rect] if label_rect else [])
        key = (tuple((int(a), int(b), int(c)) for a, b, c in circles), tuple(tuple(int(v) for v in r) for r in rects))
        if key != getattr(self, "_shape_key", None):
            self._shape_key = key
            self.shape_combine_region(shape_region(circles, rects, ellipses))

    # ---- model
    def app_of(self, w):
        xid = w.get_xid()
        if xid not in self.app_cache:
            self.app_cache[xid] = app_for_window(w)
        return self.app_cache[xid]

    def refresh(self):
        self.screen.force_update()
        items, order = {}, []
        for app in load_pins():
            it = Item(app, app.get_id())
            it.pinned = True
            items[it.key] = it
            order.append(it.key)
        live = set()
        for w in self.screen.get_windows():
            if w.is_skip_tasklist() or w.get_name() in SELF_TITLES:
                continue
            live.add(w.get_xid())
            app = self.app_of(w)
            key = app.get_id() if app else "win:%d" % w.get_xid()
            if key not in items:
                items[key] = Item(app, key)
                order.append(key)
            items[key].windows.append(w)
        self.app_cache = {k: v for k, v in self.app_cache.items() if k in live}
        self.items = [items[k] for k in order]
        self.queue_draw()

    # ---- icons
    def icon_for(self, item, size):
        if item.app and item.app.get_icon():
            key = (item.app.get_icon().to_string(), size)
            if key not in self.icon_cache:
                pix = None
                info = self.icon_theme.lookup_by_gicon(item.app.get_icon(), size, Gtk.IconLookupFlags.FORCE_SIZE)
                if info:
                    try:
                        pix = info.load_icon()
                    except GLib.Error:
                        pix = None
                self.icon_cache[key] = pix
            if self.icon_cache[key]:
                return self.icon_cache[key]
        if item.windows:
            pix = item.windows[0].get_icon()
            return pix.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR) if pix else None
        return None

    def paint_icon(self, cr, item, x, y, size, alpha=1.0):
        pix = self.icon_for(item, size)
        if pix:
            cr.save()
            Gdk.cairo_set_source_pixbuf(cr, pix, x - size / 2, y - size / 2)
            cr.paint_with_alpha(alpha)
            cr.restore()

    # ---- drawing
    def tick(self):
        self.queue_draw()
        return True

    def on_draw(self, _w, cr):
        t = time.monotonic() - self.t0
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        self.draw_background(cr, self.W, self.H, self.top, t)
        n = len(self.items)
        self.pos = {}
        dx, dy = self.hover_offset()
        for i, it in enumerate(self.items):
            x, y = self.item_pos(i, n, it, self.W, self.top, t)
            hov = self.hover is it
            if hov:
                x, y = x + dx, y + dy
            self.pos[it.key] = (x, y)
            js = jelly_scale(time.monotonic() - self.jelly[it.key]) if it.key in self.jelly else None
            if js:
                cr.save()
                cr.translate(x, y)
                cr.scale(*js)
                cr.translate(-x, -y)
                self.draw_item(cr, it, x, y, t, hov)
                cr.restore()
            else:
                self.jelly.pop(it.key, None)
                self.draw_item(cr, it, x, y, t, hov)
        self.draw_foreground(cr, t)
        self._label_rect = None
        if self.ORB:
            ox, oy = self.orb_center()
            Gdk.cairo_set_source_pixbuf(cr, self.orb, ox - self.ORB / 2, oy - self.ORB / 2)
            cr.paint()
        if self.CLOCK:
            self.draw_clock(cr)
        if self.hover and self.hover.key in self.pos:
            x, y = self.pos[self.hover.key]
            r = self.item_radius
            if self.EDGE == "top":
                self.draw_label(cr, self.hover, x, y + r + 30)
            elif self.EDGE == "right":
                self.draw_label(cr, self.hover, self.rect[0] - 90, y + 11)
            else:
                self.draw_label(cr, self.hover, x, y - r - 6)
        if self.get_realized():
            self.apply_shape(self._label_rect)
        return False

    def draw_foreground(self, cr, t):
        pass

    def draw_clock(self, cr):
        now = time.localtime()
        text = time.strftime("%-I:%M %p", now)
        cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)
        e = cr.text_extents(text)
        rx, ry, rw, rh = self.rect
        x, y = rx + rw - e.width - 22, ry + rh / 2 + e.height / 2
        cr.set_source_rgba(0, 0, 0, .45)
        cr.move_to(x + 1, y + 1)
        cr.show_text(text)
        cr.set_source_rgba(1, 1, 1, 1)
        cr.move_to(x, y)
        cr.show_text(text)

    def draw_label(self, cr, item, cx, bottom):
        text = item.label
        text = text if len(text) < 30 else text[:28] + "…"
        cr.select_font_face("Noto Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        e = cr.text_extents(text)
        w, h = e.width + 20, 22
        x = min(max(4, cx - w / 2), self.W - w - 4)
        y = max(2, bottom - h)
        self._label_rect = (x - 2, y - 2, w + 4, h + 4)
        rounded(cr, x, y, w, h, 11)
        cr.set_source_rgba(.04, .16, .28, .78)
        cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, .55)
        cr.set_line_width(1)
        cr.stroke()
        cr.set_source_rgba(1, 1, 1, 1)
        cr.move_to(x + 10 - e.x_bearing, y + h / 2 + e.height / 2)
        cr.show_text(text)

    # ---- interaction
    def hit(self, x, y):
        best, bd = None, None
        for it in self.items:
            if it.key not in self.pos:
                continue
            ix, iy = self.pos[it.key]
            d = (x - ix) ** 2 + (y - iy) ** 2
            if d <= (self.item_radius + 4) ** 2 and (bd is None or d < bd):
                best, bd = it, d
        return best

    def set_hover(self, it):
        if it is not self.hover:
            self.hover = it
            self.queue_draw()
            self.peek_hover(it)

    # ---- Aero Peek
    def peek_hover(self, it):
        if self.peek_timer:
            GLib.source_remove(self.peek_timer)
            self.peek_timer = 0
        if it is not None and it.running and setting_on("aero_peek"):
            if self.peek_hide_timer:
                GLib.source_remove(self.peek_hide_timer)
                self.peek_hide_timer = 0
            self.peek_timer = GLib.timeout_add(420, self.peek_show, it)
        elif not self.peek_inside:
            self.peek_schedule_hide()

    def peek_show(self, it):
        self.peek_timer = 0
        if self.hover is not it or it.key not in self.pos:
            return False
        if self.peek_popup is None:
            self.peek_popup = PeekPopup(self)
        x, y = self.pos[it.key]
        wx, wy = self.get_window().get_origin()[1:] if self.get_window() else (0, 0)
        self.peek_popup.show_for(it, wx + x, wy + y, self.EDGE)
        return False

    def peek_hold(self, inside):
        self.peek_inside = inside
        if inside:
            if self.peek_hide_timer:
                GLib.source_remove(self.peek_hide_timer)
                self.peek_hide_timer = 0
        elif self.hover is None:
            self.peek_schedule_hide()

    def peek_schedule_hide(self):
        if self.peek_popup and self.peek_popup.get_visible() and not self.peek_hide_timer:
            self.peek_hide_timer = GLib.timeout_add(300, self.peek_hide)

    def peek_hide(self):
        self.peek_hide_timer = 0
        if self.peek_popup and not self.peek_inside:
            self.peek_popup.hide_now()
        return False

    def on_motion(self, _w, ev):
        self.set_hover(self.hit(ev.x, ev.y))

    def on_press(self, _w, ev):
        ts = ev.time or Gtk.get_current_event_time()
        ox, oy, r = self.orb_hit
        if (ev.x - ox) ** 2 + (ev.y - oy) ** 2 <= r * r:
            subprocess.Popen(["frutiger-personalize"] if ev.button == 3 else ["xfce4-popup-whiskermenu"])
            return True
        it = self.hit(ev.x, ev.y)
        if not it:
            return False
        if self.peek_popup:
            self.peek_popup.hide_now()
        if setting_on("window_effects"):                    # jelly squish (off in Calm mode)
            self.jelly[it.key] = time.monotonic()
        if ev.button == 3:                                   # pin / unpin
            ids = [a.get_id() for a in load_pins()]
            if it.pinned:
                ids = [i for i in ids if i != it.key]
            elif it.app:
                ids.append(it.app.get_id())
            save_pins(ids)
            self.refresh()
        elif ev.button == 2:                                 # close
            for w in it.windows:
                w.close(ts)
        elif not it.windows:                                 # launch
            if it.app:
                it.app.launch([], None)
        elif len(it.windows) == 1:                           # focus / minimize
            w = it.windows[0]
            if w.is_active() and not w.is_minimized():
                w.minimize()
            else:
                w.activate(ts)
        else:                                                # cycle through windows
            act = [i for i, w in enumerate(it.windows) if w.is_active()]
            nxt = it.windows[(act[0] + 1) % len(it.windows) if act else 0]
            nxt.activate(ts)
        return True

    # ---- to override
    def draw_background(self, cr, w, h, top, t):
        pass

    def item_pos(self, i, n, item, w, top, t):
        x0, x1 = 90, w - 120
        step = min(84, (x1 - x0) / max(1, n))
        return x0 + step * (i + .5), top + self.STRIP_H / 2

    def draw_item(self, cr, item, x, y, t, hover):
        pass


def rounded(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()


def run(cls):
    GLib.set_prgname(cls.PRGNAME)
    os.makedirs(CONF, exist_ok=True)
    win = cls()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()
