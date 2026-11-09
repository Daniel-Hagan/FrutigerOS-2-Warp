"""Frutiger OS — shared glass drawing (cairo).

Used by the desktop daemon (bubbles, light on the water, wildlife, click
ripples), the screensaver, the Welcome Center globe and the Aurora Ribbon.
The same designs are in the browser preview (docs/preview.html).
"""
import colorsys, math, os, random
import cairo

CAUSTICS = "/usr/share/frutiger/caustics.png"
TAU = 2 * math.pi


def hsl(h, l, s):
    return colorsys.hls_to_rgb(h % 1, l, s)


# ---------------------------------------------------------------- bubbles
def glass_bubble(cr, x, y, r, tint=(.55, .85, 1.0), alpha=1.0):
    """A round glass bubble: faint body, bright rim, rainbow sheen, highlight and reflection."""
    tr, tg, tb = tint
    g = cairo.RadialGradient(x - r * .3, y - r * .35, r * .05, x, y, r)
    g.add_color_stop_rgba(0, 1, 1, 1, .16 * alpha)
    g.add_color_stop_rgba(.6, tr, tg, tb, .12 * alpha)
    g.add_color_stop_rgba(.86, tr * .6, tg * .6, tb * .6, .26 * alpha)
    g.add_color_stop_rgba(.97, 1, 1, 1, .85 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.set_source(g)
    cr.arc(x, y, r, 0, TAU)
    cr.fill()
    # iridescent rim: six pastel arcs around the edge
    if r > 6:
        cols = [(1, .55, .82), (1, .92, .55), (.55, 1, .78), (.47, .75, 1), (.82, .59, 1)]
        cr.set_line_width(max(1, r * .1))
        for i, (cr_, cg_, cb_) in enumerate(cols):
            a0 = 3.6 + i * TAU / len(cols)
            cr.arc(x, y, r * .92, a0, a0 + TAU / len(cols))
            cr.set_source_rgba(cr_, cg_, cb_, .32 * alpha)
            cr.stroke()
    # main highlight (soft ellipse, upper left) and a pin-point glint
    cr.save()
    cr.translate(x - r * .32, y - r * .42)
    cr.rotate(-.5)
    cr.scale(1, .58)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r * .42)
    g.add_color_stop_rgba(0, 1, 1, 1, .95 * alpha)
    g.add_color_stop_rgba(.45, 1, 1, 1, .55 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.set_source(g)
    cr.arc(0, 0, r * .42, 0, TAU)
    cr.fill()
    cr.restore()
    cr.arc(x - r * .42, y - r * .5, max(.8, r * .07), 0, TAU)
    cr.set_source_rgba(1, 1, 1, .95 * alpha)
    cr.fill()
    # reflected light, lower right
    cr.save()
    cr.translate(x + r * .28, y + r * .6)
    cr.rotate(-.35)
    cr.scale(1, .4)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, r * .36)
    g.add_color_stop_rgba(0, 1, 1, 1, .55 * alpha)
    g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.set_source(g)
    cr.arc(0, 0, r * .36, 0, TAU)
    cr.fill()
    cr.restore()


# ---------------------------------------------------------------- light on the water
# where the water is in each wallpaper: (top of the water as a fraction of the screen, strength, vertical squash)
WATER = {"lagoon-day": (.89, .5, .22), "lagoon": (.89, .5, .22), "lagoon-dawn": (.935, .3, .2), "lagoon-sunset": (.935, .28, .2),
         "lagoon-night": (.925, .16, .2), "aurora": (.73, .22, .35), "aquarium": (0, .42, 1), "koi": (0, .38, 1), "bubbles": (0, .3, 1)}
_tile = None


def caustics(cr, W, H, scene, t):
    """Two drifting layers of a caustic pattern, masked to the scene's water."""
    global _tile
    wv = WATER.get(scene)
    if not wv:
        return
    if _tile is None:
        try:
            _tile = cairo.ImageSurface.create_from_png(CAUSTICS)
        except Exception:
            _tile = False
    if not _tile:
        return
    top, strength, squash = wv
    strength *= .6
    y0 = H * top
    mask = cairo.LinearGradient(0, y0, 0, H)
    if scene == "aquarium":
        mask.add_color_stop_rgba(0, 0, 0, 0, strength)
        mask.add_color_stop_rgba(.55, 0, 0, 0, strength)
        mask.add_color_stop_rgba(.88, 0, 0, 0, 0)
    elif top == 0:
        mask.add_color_stop_rgba(0, 0, 0, 0, strength * .7)
        mask.add_color_stop_rgba(.5, 0, 0, 0, strength)
        mask.add_color_stop_rgba(1, 0, 0, 0, strength * .6)
    else:
        mask.add_color_stop_rgba(0, 0, 0, 0, 0)
        mask.add_color_stop_rgba(.22, 0, 0, 0, strength)
        mask.add_color_stop_rgba(1, 0, 0, 0, strength)
    cr.save()
    cr.rectangle(0, y0, W, H - y0)
    cr.clip()
    cr.push_group()
    for size, dx, dy in ((260, 1, 1), (190, -2, 1)):
        k = size / 192.0
        pat = cairo.SurfacePattern(_tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        pat.set_filter(cairo.FILTER_GOOD)
        ox = (t / 26.0 * size * dx) % size
        oy = (t / 26.0 * size * squash * dy) % (size * squash)
        m = cairo.Matrix()
        m.scale(1 / k, 1 / (k * squash))
        m.translate(-ox, -oy)
        pat.set_matrix(m)
        cr.set_source(pat)
        cr.paint()
    cr.pop_group_to_source()
    cr.mask(mask)
    cr.restore()


# ---------------------------------------------------------------- wildlife
BFLY = [((.37, .82, 1), (.1, .44, .82)), ((1, .81, .29), (.94, .42, .1)), ((.61, .94, .42), (.16, .6, .23)), ((1, .6, .82), (.69, .29, .82))]


def _wing(cr, pts):
    cr.move_to(*pts[0])
    for i in range(1, len(pts), 3):
        cr.curve_to(*pts[i], *pts[i + 1], *pts[i + 2])
    cr.close_path()


def draw_butterfly(cr, x, y, ang, flap, pal, s=1.0):
    light, dark = pal
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    cr.scale(s, s)
    for side in (-1, 1):
        cr.save()
        cr.scale(side * max(.18, flap), 1)
        g = cairo.RadialGradient(-6, -8, 1, -8, -4, 20)
        g.add_color_stop_rgb(0, 1, 1, 1)
        g.add_color_stop_rgb(.35, *light)
        g.add_color_stop_rgb(1, *dark)
        _wing(cr, [(-1, -2), (-9, -18), (-22, -17), (-20, -6), (-19, 1), (-9, 2), (-1, 1)])
        _wing(cr, [(-1, 1), (-10, 3), (-17, 12), (-11, 16), (-6, 18), (-2, 10), (-1, 3)])
        cr.set_source(g)
        cr.fill_preserve()
        cr.set_source_rgba(1, 1, 1, .8)
        cr.set_line_width(.8)
        cr.stroke()
        cr.restore()
    cr.save()
    cr.scale(1, 5.6)
    cr.arc(0, .35, 1.6, 0, TAU)
    cr.restore()
    cr.set_source_rgb(.14, .2, .29)
    cr.fill()
    cr.restore()


def draw_dragonfly(cr, x, y, ang, t):
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    cr.scale(1.35, 1.35)
    buzz = .55 + .45 * abs(math.sin(t * 60))
    for wy, span, rot in ((-6, 24, .25), (-2, 22, .1)):
        for side in (-1, 1):
            cr.save()
            cr.translate(0, wy)
            cr.rotate(side * rot)
            cr.scale(span * side / 2, 3 * buzz)
            cr.arc(1, 0, 1, 0, TAU)
            cr.restore()
            g = cairo.LinearGradient(-span, 0, span, 0)
            g.add_color_stop_rgba(0, .92, 1, 1, .85)
            g.add_color_stop_rgba(.5, .7, .9, 1, .55)
            g.add_color_stop_rgba(1, .88, 1, .85, .8)
            cr.set_source(g)
            cr.fill_preserve()
            cr.set_source_rgba(1, 1, 1, .7)
            cr.set_line_width(.5)
            cr.stroke()
    g = cairo.LinearGradient(0, -14, 0, 21)
    g.add_color_stop_rgb(0, .37, .94, .88)
    g.add_color_stop_rgb(1, .1, .44, .69)
    cr.arc(0, -11, 3.2, 0, TAU)
    cr.set_source(g)
    cr.fill()
    cr.rectangle(-1.6, -9, 3.2, 30)
    cr.set_source(g)
    cr.fill()
    cr.restore()


def draw_leaf(cr, x, y, ang, hue):
    cr.save()
    cr.translate(x, y)
    cr.rotate(ang)
    cr.move_to(-13, 13)
    cr.curve_to(-15, -3, -4, -14, 13, -13)
    cr.curve_to(14, 4, 3, 15, -13, 13)
    cr.close_path()
    g = cairo.LinearGradient(-13, -13, 13, 13)
    g.add_color_stop_rgb(0, *hsl(hue / 360, .72, .85))
    g.add_color_stop_rgb(1, *hsl((hue - 20) / 360, .38, .75))
    cr.set_source(g)
    cr.fill_preserve()
    cr.set_source_rgba(1, 1, 1, .8)
    cr.set_line_width(.8)
    cr.stroke()
    cr.move_to(-13, 13)
    cr.curve_to(-3, 3, 4, -4, 13, -13)
    cr.set_source_rgba(1, 1, 1, .7)
    cr.set_line_width(1)
    cr.stroke()
    cr.restore()


def draw_firefly(cr, x, y, a):
    g = cairo.RadialGradient(x, y, 0, x, y, 14)
    g.add_color_stop_rgba(0, 1, .98, .82, a)
    g.add_color_stop_rgba(.25, .91, 1, .48, a * .8)
    g.add_color_stop_rgba(1, .8, 1, .35, 0)
    cr.set_source(g)
    cr.arc(x, y, 14, 0, TAU)
    cr.fill()


class Zoo:
    """Now and then a butterfly, dragonfly or drifting leaf crosses the desktop; fireflies at night."""
    def __init__(self):
        self.items, self.next_at, self.t = [], 4.0, 0.0

    def clear(self):
        self.items = []

    def update(self, dt, W, H, night=False, pond=False):
        self.t += dt
        if self.t >= self.next_at and len(self.items) < 4:
            if night:
                for _ in range(4):
                    self.spawn("ffly", W, H, pond)
            else:
                r = random.random()
                self.spawn("bfly" if r < .45 else "dfly" if r < .75 else "leaf", W, H, pond)
            self.next_at = self.t + (12 if pond else 20) + random.random() * 22
        keep = []
        for c in self.items:
            c["t"] += dt
            if self._step(c, dt, W, H):
                keep.append(c)
        self.items = keep

    def spawn(self, kind, W, H, pond):
        c = {"kind": kind, "t": 0.0}
        if kind == "ffly":
            c.update(x=random.random() * W, y=H * (.45 + random.random() * .45), vx=(random.random() - .5) * 30,
                     vy=(random.random() - .5) * 16, life=14 + random.random() * 8, ph=random.random() * 6)
        elif kind == "leaf":
            c.update(x0=W * (.1 + random.random() * .8), y=-40.0, life=13 + random.random() * 5, sw=60 + random.random() * 60,
                     ph=random.random() * 6, hue=random.choice([95, 80, 45, 30]))
        elif kind == "dfly":
            from_left = random.random() < .5
            pts = [(-60 if from_left else W + 60, H * (.3 + random.random() * .4))]
            for _ in range(4 + random.randint(0, 2)):
                pts.append((60 + random.random() * min(420, W * .5), H - 140 - random.random() * 200) if pond
                           else (W * (.1 + random.random() * .8), H * (.15 + random.random() * .6)))
            pts.append((W + 60 if from_left else -60, H * (.2 + random.random() * .4)))
            c.update(pts=pts, seg=0, seg_t=0.0, hold=0.0, x=pts[0][0], y=pts[0][1], ang=0.0)
        else:
            from_left = random.random() < .5
            c.update(dir=1 if from_left else -1, x=-50.0 if from_left else W + 50.0, yb=H * (.25 + random.random() * .45),
                     sp=55 + random.random() * 35, ph=random.random() * 6, pal=random.choice(BFLY))
        self.items.append(c)

    def _step(self, c, dt, W, H):
        k = c["kind"]
        if k == "ffly":
            c["vx"] += (random.random() - .5) * 40 * dt
            c["vy"] += (random.random() - .5) * 30 * dt
            c["x"] += c["vx"] * dt
            c["y"] += c["vy"] * dt
            return c["t"] < c["life"]
        if k == "leaf":
            c["y"] += (H + 80) / c["life"] * dt
            return c["y"] < H + 40
        if k == "dfly":
            if c["hold"] > 0:
                c["hold"] -= dt
                return True
            (ax, ay), (bx, by) = c["pts"][c["seg"]], c["pts"][c["seg"] + 1]
            dur = max(.5, math.hypot(bx - ax, by - ay) / 380)
            c["seg_t"] += dt / dur
            u = min(1, c["seg_t"])
            e = 2 * u * u if u < .5 else 1 - (-2 * u + 2) ** 2 / 2
            c["x"], c["y"] = ax + (bx - ax) * e, ay + (by - ay) * e
            c["ang"] = math.atan2(by - ay, bx - ax) + math.pi / 2
            if u >= 1:
                c["seg"] += 1
                c["seg_t"] = 0.0
                c["hold"] = .5 + random.random() * 1.4
                if c["seg"] >= len(c["pts"]) - 1:
                    return False
            return True
        c["x"] += c["dir"] * c["sp"] * dt
        return -80 < c["x"] < W + 80

    def draw(self, cr):
        for c in self.items:
            k, t = c["kind"], c["t"]
            if k == "ffly":
                a = min(1, t / 2, (c["life"] - t) / 2) * (.25 + .75 * abs(math.sin(t * 2 + c["ph"])))
                draw_firefly(cr, c["x"], c["y"], max(0, a))
            elif k == "leaf":
                x = c["x0"] + math.sin(t * 1.1 + c["ph"]) * c["sw"]
                ang = math.radians(math.sin(t * 1.1 + c["ph"] + 1) * 50 + t * 20)
                draw_leaf(cr, x, c["y"], ang, c["hue"])
            elif k == "dfly":
                jx = math.sin(t * 9) * 1.5 if c["hold"] > 0 else 0
                draw_dragonfly(cr, c["x"] + jx, c["y"], c["ang"], t)
            else:
                y = c["yb"] + math.sin(t * 2.2 + c["ph"]) * 34 + math.sin(t * 5.3) * 6
                ang = math.radians(c["dir"] * 12 + math.cos(t * 2.2 + c["ph"]) * 14 * c["dir"])
                flap = abs(math.cos(t * 19))
                draw_butterfly(cr, c["x"], y, ang, flap, c["pal"])


# ---------------------------------------------------------------- click ripples
def draw_ripple(cr, x, y, age):
    """Three expanding rings, 1.25 s each, staggered."""
    for i, (delay, lw) in enumerate(((0, 2.0), (.16, 1.5), (.32, 1.0))):
        p = (age - delay) / 1.25
        if not 0 < p < 1:
            continue
        r = 4 + 86 * p
        cr.arc(x, y, r, 0, TAU)
        cr.set_source_rgba(1, 1, 1, .9 * (1 - p))
        cr.set_line_width(lw)
        cr.stroke()


# ---------------------------------------------------------------- Welcome Center globe
def _land():
    rnd, pts = random.Random(7), []
    for la, lo, sp, n in ((48, -100, 22, 70), (12, -60, 14, 40), (-15, -58, 14, 50), (50, 15, 14, 40), (5, 20, 20, 70),
                          (55, 90, 26, 90), (25, 80, 12, 30), (-25, 135, 10, 30), (70, -40, 8, 14)):
        for _ in range(n):
            a, r = rnd.random() * TAU, math.sqrt(rnd.random()) * sp
            pts.append((math.radians(la + math.sin(a) * r * .8), math.radians(lo + math.cos(a) * r * 1.3), 4 + rnd.random() * 5))
    return pts


LAND = _land()


def globe(cr, size, t):
    """A slowly turning glass globe with a glowing ring, drawn in a size x size square."""
    k = size / 84.0
    cr.save()
    cr.scale(k, k)
    cx = cy = 42
    R, tilt, rot = 33, .4, t * .35

    def ring(front):
        cr.save()
        cr.translate(cx, cy)
        cr.rotate(-.35)
        cr.scale(R + 8, 9)
        if front:
            cr.arc(0, 0, 1, 0, math.pi)
        else:
            cr.arc(0, 0, 1, math.pi, TAU)
        cr.restore()
        cr.set_source_rgba(.75, .92, 1, .5)
        cr.set_line_width(3.5)
        cr.stroke_preserve()
        cr.set_source_rgba(1, 1, 1, .8)
        cr.set_line_width(1.4)
        cr.stroke()

    ring(False)
    g = cairo.RadialGradient(cx - R * .35, cy - R * .4, R * .1, cx, cy, R)
    g.add_color_stop_rgb(0, .79, .95, 1)
    g.add_color_stop_rgb(.45, .24, .7, .95)
    g.add_color_stop_rgb(1, .04, .31, .6)
    cr.arc(cx, cy, R, 0, TAU)
    cr.set_source(g)
    cr.fill()
    cr.save()
    cr.arc(cx, cy, R, 0, TAU)
    cr.clip()
    for la, lo, s in LAND:
        l = lo + rot
        ca = math.cos(la)
        X, Y0, Z0 = ca * math.sin(l), math.sin(la), ca * math.cos(l)
        Y, Z = Y0 * math.cos(tilt) - Z0 * math.sin(tilt), Y0 * math.sin(tilt) + Z0 * math.cos(tilt)
        if Z <= 0:
            continue
        cr.arc(cx + X * R, cy - Y * R, s * (.35 + .65 * Z) * R / 40, 0, TAU)
        cr.set_source_rgba((95 + 60 * Z) / 255, (200 + 30 * Z) / 255, (70 + 20 * Z) / 255, .55 + .4 * Z)
        cr.fill()
    g = cairo.RadialGradient(cx - R * .3, cy - R * .35, R * .2, cx, cy, R * 1.02)
    g.add_color_stop_rgba(0, 1, 1, 1, 0)
    g.add_color_stop_rgba(.75, 0, .16, .4, .12)
    g.add_color_stop_rgba(1, 0, .12, .31, .45)
    cr.set_source(g)
    cr.paint()
    cr.restore()
    cr.save()
    cr.translate(cx - R * .25, cy - R * .5)
    cr.scale(1, .5)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, R * .7)
    g.add_color_stop_rgba(0, 1, 1, 1, .9)
    g.add_color_stop_rgba(1, 1, 1, 1, 0)
    cr.set_source(g)
    cr.arc(0, 0, R * .7, 0, TAU)
    cr.fill()
    cr.restore()
    cr.arc(cx, cy, R - .5, 0, TAU)
    cr.set_source_rgba(1, 1, 1, .85)
    cr.set_line_width(1.2)
    cr.stroke()
    ring(True)
    cr.restore()


# ---------------------------------------------------------------- glass that matches the wallpaper
def wallpaper_color(path):
    """A saturated, mid-light colour that represents the picture (for tinting the glass), as '#rrggbb'."""
    try:
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf
        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 24, 14, False).add_alpha(False, 0, 0, 0)
        data, n, rs = pix.get_pixels(), pix.get_n_channels(), pix.get_rowstride()
        sr = sg = sb = sw = 0.0
        for yy in range(pix.get_height()):
            for xx in range(pix.get_width()):
                i = yy * rs + xx * n
                r, g, b = data[i] / 255, data[i + 1] / 255, data[i + 2] / 255
                h, l, s = colorsys.rgb_to_hls(r, g, b)
                w = .05 + s * s * (1 - abs(l - .5) * 1.6)
                sr, sg, sb, sw = sr + r * w, sg + g * w, sb + b * w, sw + w
        h, l, s = colorsys.rgb_to_hls(sr / sw, sg / sw, sb / sw)
        r, g, b = colorsys.hls_to_rgb(h, max(.36, min(.52, l)), max(.5, min(.85, s * 1.25)))
        return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
    except Exception:
        return None


def scene_name(path):
    """'lagoon-day' for /usr/share/backgrounds/frutiger/pack/lagoon-day.jpg; '' for the user's own pictures."""
    if not path or "/backgrounds/frutiger/" not in path:
        return ""
    return os.path.splitext(os.path.basename(path))[0]
