#!/usr/bin/env python3
"""Draw the original Frutiger cursor theme (glossy white with a soft blue sheen).

Writes PNGs + xcursorgen configs to
  config/includes.chroot/usr/share/icons/Frutiger-Cursors/src/
The chroot hook compiles them with xcursorgen (package x11-apps) and adds the
standard cursor-name symlinks. Needs Pillow.
"""
import math, os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "config/includes.chroot/usr/share/icons/Frutiger-Cursors/src")
os.makedirs(OUT, exist_ok=True)
SIZES = (24, 32, 48)
SS = 4                      # supersampling


def canvas(size):
    return Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))


def finish(img, size, shadow=True):
    big = img
    if shadow:
        a = big.split()[3].filter(ImageFilter.GaussianBlur(SS * 1.2))
        sh = Image.new("RGBA", big.size, (0, 20, 50, 0))
        sh.putalpha(a.point(lambda v: v * .45))
        sh = sh.transform(sh.size, Image.AFFINE, (1, 0, -SS * 1.2, 0, 1, -SS * 1.6))
        big = Image.alpha_composite(sh, big)
    return big.resize((size, size), Image.LANCZOS)


def glossy_poly(d, pts, size, fill_top=(255, 255, 255), fill_bot=(214, 236, 255), outline=(10, 25, 45)):
    """Polygon with a vertical white->ice-blue gradient and a dark outline."""
    s = size * SS / 32
    P = [(x * s, y * s) for x, y in pts]
    mask = Image.new("L", d.im.size if hasattr(d, "im") else (size * SS, size * SS))
    ImageDraw.Draw(mask).polygon(P, fill=255)
    grad = Image.new("RGBA", mask.size)
    gd = ImageDraw.Draw(grad)
    ys = [p[1] for p in P]
    y0, y1 = min(ys), max(ys)
    for y in range(mask.size[1]):
        k = min(1, max(0, (y - y0) / max(1, y1 - y0)))
        c = tuple(round(a + (b - a) * k) for a, b in zip(fill_top, fill_bot))
        gd.line([(0, y), (mask.size[0], y)], fill=c + (255,))
    grad.putalpha(mask)
    return grad, P, outline


def poly_cursor(name, pts, hot, extra=None):
    cfg = []
    for size in SIZES:
        img = canvas(size)
        grad, P, outline = glossy_poly(ImageDraw.Draw(img), pts, size)
        img = Image.alpha_composite(img, grad)
        d = ImageDraw.Draw(img)
        d.line(P + [P[0]], fill=outline + (255,), width=max(SS, int(SS * size / 24)), joint="curve")
        if extra:
            extra(d, size)
        out = finish(img, size)
        fn = f"{name}-{size}.png"
        out.save(os.path.join(OUT, fn))
        cfg.append(f"{size} {round(hot[0] * size / 32)} {round(hot[1] * size / 32)} {fn}")
    open(os.path.join(OUT, name + ".cfg"), "w").write("\n".join(cfg) + "\n")


ARROW = [(2, 1), (2, 25), (7.5, 19.5), (11.5, 28.5), (15, 27), (11, 18.5), (18.5, 18.5)]


def gloss_on_arrow(d, size):
    s = size * SS / 32
    d.polygon([(3.6 * s, 4 * s), (3.6 * s, 14 * s), (9 * s, 9.6 * s)], fill=(255, 255, 255, 200))


poly_cursor("default", ARROW, (2, 1), gloss_on_arrow)

HAND = [(9, 2), (12, 2), (12.5, 12), (14, 11), (16.5, 11.5), (17, 13), (19, 12.5), (21, 13.5), (21.5, 15), (23.5, 15),
        (25, 17), (24.5, 24), (21.5, 29.5), (11.5, 29.5), (7.5, 23.5), (4.5, 19.5), (5, 17), (8, 17.5), (8.6, 3.5)]
poly_cursor("pointer", HAND, (10.5, 2))

MOVE = [(16, 1), (21, 7), (18, 7), (18, 14), (25, 14), (25, 11), (31, 16), (25, 21), (25, 18), (18, 18), (18, 25), (21, 25),
        (16, 31), (11, 25), (14, 25), (14, 18), (7, 18), (7, 21), (1, 16), (7, 11), (7, 14), (14, 14), (14, 7), (11, 7)]
poly_cursor("move", MOVE, (16, 16))

DOUBLE = [(1, 16), (8, 9), (8, 13.5), (24, 13.5), (24, 9), (31, 16), (24, 23), (24, 18.5), (8, 18.5), (8, 23)]


def rot(pts, deg):
    a = math.radians(deg)
    return [(16 + (x - 16) * math.cos(a) - (y - 16) * math.sin(a), 16 + (x - 16) * math.sin(a) + (y - 16) * math.cos(a)) for x, y in pts]


poly_cursor("ew-resize", DOUBLE, (16, 16))
poly_cursor("ns-resize", rot(DOUBLE, 90), (16, 16))
poly_cursor("nwse-resize", rot(DOUBLE, 45), (16, 16))
poly_cursor("nesw-resize", rot(DOUBLE, -45), (16, 16))
IBEAM = [(10, 2), (14, 2), (16, 4), (18, 2), (22, 2), (22, 4.5), (17.5, 4.5), (17.5, 27.5), (22, 27.5), (22, 30), (18, 30),
         (16, 28), (14, 30), (10, 30), (10, 27.5), (14.5, 27.5), (14.5, 4.5), (10, 4.5)]
poly_cursor("text", IBEAM, (16, 16))
CROSS = [(14.5, 1), (17.5, 1), (17.5, 14.5), (31, 14.5), (31, 17.5), (17.5, 17.5), (17.5, 31), (14.5, 31), (14.5, 17.5),
         (1, 17.5), (1, 14.5), (14.5, 14.5)]
poly_cursor("crosshair", CROSS, (16, 16))


def not_allowed():
    cfg = []
    for size in SIZES:
        img = canvas(size)
        d = ImageDraw.Draw(img)
        s = size * SS / 32
        d.ellipse([3 * s, 3 * s, 29 * s, 29 * s], fill=(10, 25, 45, 255))
        d.ellipse([4.5 * s, 4.5 * s, 27.5 * s, 27.5 * s], fill=(235, 70, 50, 255))
        d.ellipse([8.5 * s, 8.5 * s, 23.5 * s, 23.5 * s], fill=(0, 0, 0, 0))
        d.line([(9 * s, 9 * s), (23 * s, 23 * s)], fill=(235, 70, 50, 255), width=int(4 * s))
        d.ellipse([7 * s, 5.5 * s, 20 * s, 12 * s], fill=(255, 255, 255, 110))
        fn = f"not-allowed-{size}.png"
        finish(img, size).save(os.path.join(OUT, fn))
        cfg.append(f"{size} {size // 2} {size // 2} {fn}")
    open(os.path.join(OUT, "not-allowed.cfg"), "w").write("\n".join(cfg) + "\n")


not_allowed()


def ring_frame(d, cx, cy, r, k, s, frames):
    """8 glossy blue beads around a ring; the bright one travels."""
    for i in range(8):
        a = i * math.pi / 4 - math.pi / 2
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        lit = (i - k * 8 / frames) % 8
        bright = max(.25, 1 - lit / 8)
        rr = 2.6 * s
        col = (int(40 + 120 * bright), int(150 + 90 * bright), 255, 255)
        d.ellipse([x - rr - .7 * s, y - rr - .7 * s, x + rr + .7 * s, y + rr + .7 * s], fill=(10, 40, 80, int(200 * bright) + 40))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
        d.ellipse([x - rr * .6, y - rr * .8, x + rr * .3, y - rr * .1], fill=(255, 255, 255, int(220 * bright)))


def busy(name, with_arrow):
    frames, cfg = 12, []
    for size in SIZES:
        for k in range(frames):
            img = canvas(size)
            s = size * SS / 32
            if with_arrow:
                grad, P, outline = glossy_poly(ImageDraw.Draw(img), [(x * .8, y * .8) for x, y in ARROW], size)
                img = Image.alpha_composite(img, grad)
                ImageDraw.Draw(img).line(P + [P[0]], fill=outline + (255,), width=max(SS, int(SS * size / 24)))
                ring_frame(ImageDraw.Draw(img), 23 * s, 23 * s, 6.5 * s, k, s * .75, frames)
            else:
                ring_frame(ImageDraw.Draw(img), 16 * s, 16 * s, 11 * s, k, s, frames)
            fn = f"{name}-{size}-{k:02d}.png"
            finish(img, size).save(os.path.join(OUT, fn))
            hx, hy = (2, 1) if with_arrow else (16, 16)
            cfg.append(f"{size} {round(hx * size / 32)} {round(hy * size / 32)} {fn} 60")
    open(os.path.join(OUT, name + ".cfg"), "w").write("\n".join(cfg) + "\n")


busy("wait", False)
busy("progress", True)

# standard names -> our drawings (the hook makes these symlinks)
ALIASES = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "context-menu", "copy", "alias", "dnd-move", "dnd-copy", "dnd-link", "vertical-text", "cell", "help", "question_arrow", "whats_this"],
    "pointer": ["hand1", "hand2", "pointing_hand", "grab", "grabbing", "openhand", "closedhand", "dnd-none", "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"],
    "text": ["xterm", "ibeam"],
    "wait": ["watch", "clock"],
    "progress": ["left_ptr_watch", "half-busy", "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"],
    "move": ["fleur", "all-scroll", "size_all", "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
    "ew-resize": ["col-resize", "sb_h_double_arrow", "h_double_arrow", "e-resize", "w-resize", "right_side", "left_side", "size_hor", "split_h", "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "ns-resize": ["row-resize", "sb_v_double_arrow", "v_double_arrow", "n-resize", "s-resize", "top_side", "bottom_side", "size_ver", "split_v", "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "nwse-resize": ["nw-resize", "se-resize", "top_left_corner", "bottom_right_corner", "size_fdiag", "bd_double_arrow", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "nesw-resize": ["ne-resize", "sw-resize", "top_right_corner", "bottom_left_corner", "size_bdiag", "fd_double_arrow", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "crosshair": ["cross", "tcross", "cross_reverse", "diamond_cross", "plus"],
    "not-allowed": ["crossed_circle", "forbidden", "no-drop", "circle", "pirate", "X_cursor", "03b6e0fcb3499374a867c041f52298f0"],
}
with open(os.path.join(OUT, "aliases.txt"), "w") as f:
    for target, names in ALIASES.items():
        for n in names:
            f.write(f"{n} {target}\n")
print("cursor sources written to", OUT)
