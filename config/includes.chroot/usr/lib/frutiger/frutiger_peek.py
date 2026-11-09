"""Frutiger OS — Aero Peek helpers.

peek(keep)  turns every ordinary window except the ones in `keep` (X ids) into
            faint glass, so you can see what's behind them (or the desktop);
unpeek()    puts them back.
capture()   a live thumbnail of a window (None if it's minimized).

Uses _NET_WM_WINDOW_OPACITY, which picom (detect-client-opacity) and xfwm4's own
compositor both honour; without a compositor nothing happens.
"""
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("GdkX11", "3.0")
from gi.repository import Gdk, GdkX11, GdkPixbuf  # noqa: F401

GHOST = int(.07 * 0xffffffff)
_saved = {}            # xid -> previous opacity (None = none set)
_d = None


def _display():
    global _d
    if _d is None:
        from Xlib import display
        _d = display.Display()
    return _d


def _clients(d):
    root = d.screen().root
    prop = root.get_full_property(d.intern_atom("_NET_CLIENT_LIST_STACKING"), 0)
    return list(prop.value) if prop else []


def _ordinary(d, w):
    t = w.get_full_property(d.intern_atom("_NET_WM_WINDOW_TYPE"), 0)
    types = set(t.value) if t else set()
    skip = {d.intern_atom(n) for n in ("_NET_WM_WINDOW_TYPE_DOCK", "_NET_WM_WINDOW_TYPE_DESKTOP",
                                        "_NET_WM_WINDOW_TYPE_NOTIFICATION", "_NET_WM_WINDOW_TYPE_UTILITY")}
    return not (types & skip)


def peek(keep=()):
    try:
        from Xlib import Xatom
        d = _display()
        op = d.intern_atom("_NET_WM_WINDOW_OPACITY")
        for xid in _clients(d):
            w = d.create_resource_object("window", xid)
            if not _ordinary(d, w):
                continue
            if xid in keep:
                if xid in _saved:
                    _restore(d, w, xid, op)
                continue
            if xid not in _saved:
                cur = w.get_full_property(op, Xatom.CARDINAL)
                _saved[xid] = cur.value[0] if cur else None
            w.change_property(op, Xatom.CARDINAL, 32, [GHOST])
        d.flush()
    except Exception as e:
        print("peek:", e)


def _restore(d, w, xid, op):
    from Xlib import Xatom
    old = _saved.pop(xid, None)
    if old is None:
        w.delete_property(op)
    else:
        w.change_property(op, Xatom.CARDINAL, 32, [old])


def unpeek():
    if not _saved:
        return
    try:
        d = _display()
        op = d.intern_atom("_NET_WM_WINDOW_OPACITY")
        for xid in list(_saved):
            try:
                _restore(d, d.create_resource_object("window", xid), xid, op)
            except Exception:
                _saved.pop(xid, None)
        d.flush()
    except Exception as e:
        print("unpeek:", e)


def capture(xid, max_w, max_h):
    """Scaled pixbuf of a window's contents, or None when it can't be read (minimized, gone)."""
    try:
        disp = Gdk.Display.get_default()
        win = GdkX11.X11Window.foreign_new_for_display(disp, xid)
        if win is None:
            return None
        w, h = win.get_width(), win.get_height()
        if w < 4 or h < 4:
            return None
        pix = Gdk.pixbuf_get_from_window(win, 0, 0, w, h)
        if pix is None:
            return None
        k = min(max_w / w, max_h / h)
        return pix.scale_simple(max(1, int(w * k)), max(1, int(h * k)), GdkPixbuf.InterpType.BILINEAR)
    except Exception:
        return None
