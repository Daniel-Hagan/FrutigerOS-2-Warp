#!/usr/bin/env python3
"""Generate Frutiger OS theme bitmaps: xfwm4 window frame + caption buttons.

Usage:  python3 tools/gen_assets.py [--accent 2aa7e8] [--alpha 0.55]
Writes into config/includes.chroot/usr/share/themes/Frutiger-Aero/xfwm4/
Requires Pillow (apt install python3-pil).
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--accent", default="2aa7e8", help="glass tint, hex RGB")
ap.add_argument("--alpha", type=float, default=0.55, help="frame opacity 0-1")
ap.add_argument("--out", help="output xfwm4 directory (default: the theme in this repo)")
args = ap.parse_args()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = args.out or os.path.join(ROOT, "config/includes.chroot/usr/share/themes/Frutiger-Aero/xfwm4")
os.makedirs(OUT, exist_ok=True)

AR, AG, AB = (int(args.accent[i:i + 2], 16) for i in (0, 2, 4))
TITLE_H, BORDER, CORNER, RADIUS = 30, 7, 9, 8


def mix(c1, c2, t):
    return tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))


def glass_px(y, h, active=True):
    """Colour of the glass at row y of a band h tall: glossy top half, tint below."""
    base_a = args.alpha if active else args.alpha * 0.55
    tint = (AR, AG, AB) if active else mix((AR, AG, AB), (200, 210, 220), 0.6)
    t = y / max(1, h - 1)
    if t < 0.5:  # specular highlight band
        rgb = mix((255, 255, 255), tint, 0.35 + t * 0.9)
        a = base_a + (0.5 - t) * 0.5
    else:
        rgb = mix(tint, (255, 255, 255), (t - 0.5) * 0.3)
        a = base_a
    return rgb + (round(min(1, a) * 255),)


def band(w, h, active, outline_left=False, outline_right=False, outline_top=False, outline_bottom=False,
         round_tl=False, round_tr=False, round_bl=False, round_br=False, height_ref=None, y0=0):
    """Glass band with dark outer stroke + light inner stroke and optional rounded corners."""
    href = height_ref or h
    im = Image.new("RGBA", (w, h))
    px = im.load()
    for y in range(h):
        c = glass_px(y + y0, href, active)
        for x in range(w):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    dark = (0, 30, 60, 170 if active else 110)
    light = (255, 255, 255, 170 if active else 110)
    if outline_top:
        d.line([(0, 0), (w, 0)], fill=dark); d.line([(0, 1), (w, 1)], fill=light)
    if outline_bottom:
        d.line([(0, h - 1), (w, h - 1)], fill=dark); d.line([(0, h - 2), (w, h - 2)], fill=light)
    if outline_left:
        d.line([(0, 0), (0, h)], fill=dark); d.line([(1, 0), (1, h)], fill=light)
    if outline_right:
        d.line([(w - 1, 0), (w - 1, h)], fill=dark); d.line([(w - 2, 0), (w - 2, h)], fill=light)
    # rounded corners: clear pixels outside the radius, re-stroke the arc
    for flag, cx, cy in ((round_tl, RADIUS, RADIUS), (round_tr, w - RADIUS - 1, RADIUS),
                         (round_bl, RADIUS, h - RADIUS - 1), (round_br, w - RADIUS - 1, h - RADIUS - 1)):
        if not flag:
            continue
        for y in range(h):
            for x in range(w):
                inx = (x < cx) if cx == RADIUS else (x > cx)
                iny = (y < cy) if cy == RADIUS else (y > cy)
                if inx and iny:
                    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                    if dist > RADIUS:
                        px[x, y] = (0, 0, 0, 0)
                    elif dist > RADIUS - 1:
                        px[x, y] = dark
                    elif dist > RADIUS - 2:
                        px[x, y] = light
    return im


def save(im, name):
    im.save(os.path.join(OUT, name + ".png"))


for state, act in (("active", True), ("inactive", False)):
    # title row
    save(band(CORNER, TITLE_H, act, outline_left=True, outline_top=True, round_tl=True), f"top-left-{state}")
    save(band(CORNER, TITLE_H, act, outline_right=True, outline_top=True, round_tr=True), f"top-right-{state}")
    for i in range(1, 6):
        save(band(4, TITLE_H, act, outline_top=True), f"title-{i}-{state}")
    # sides and bottom continue the lower (tinted) part of the glass
    save(band(BORDER, 4, act, outline_left=True, height_ref=TITLE_H, y0=TITLE_H - 4), f"left-{state}")
    save(band(BORDER, 4, act, outline_right=True, height_ref=TITLE_H, y0=TITLE_H - 4), f"right-{state}")
    save(band(4, BORDER, act, outline_bottom=True, height_ref=TITLE_H, y0=TITLE_H - BORDER), f"bottom-{state}")
    save(band(CORNER, BORDER, act, outline_left=True, outline_bottom=True, height_ref=TITLE_H, y0=TITLE_H - BORDER), f"bottom-left-{state}")
    save(band(CORNER, BORDER, act, outline_right=True, outline_bottom=True, height_ref=TITLE_H, y0=TITLE_H - BORDER), f"bottom-right-{state}")

# ---- caption buttons (Aero "caps" hanging from the top edge) ----
CAP_H = 20
PAL = {  # top, mid-upper, mid-lower, bottom
    "plain":    [(255, 255, 255, 140), (255, 255, 255, 40), (255, 255, 255, 0), (255, 255, 255, 60)],
    "plain_hl": [(191, 230, 255, 255), (95, 182, 238, 255), (42, 143, 216, 255), (102, 204, 255, 255)],
    "plain_pr": [(120, 190, 240, 255), (40, 120, 200, 255), (20, 90, 170, 255), (60, 160, 230, 255)],
    "close":    [(232, 164, 147, 255), (207, 106, 85, 255), (185, 58, 34, 255), (217, 122, 88, 255)],
    "close_hl": [(255, 182, 160, 255), (240, 106, 78, 255), (224, 48, 15, 255), (255, 141, 94, 255)],
    "close_pr": [(200, 90, 70, 255), (170, 40, 20, 255), (140, 20, 5, 255), (190, 70, 40, 255)],
}


def cap(width, pal, glyph, inactive=False):
    im = Image.new("RGBA", (width, TITLE_H))
    px = im.load()
    stops = PAL[pal]
    for y in range(CAP_H):
        t = y / (CAP_H - 1)
        if t < .5:
            c = mix(stops[0], stops[1], t * 2)
        else:
            c = mix(stops[2], stops[3], (t - .5) * 2)
        if inactive:
            c = c[:3] + (round(c[3] * .55),)
        for x in range(width):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, -6, width - 1, CAP_H - 1], radius=5, outline=(0, 30, 60, 200 if not inactive else 110))
    d.line([(1, CAP_H - 2), (width - 2, CAP_H - 2)], fill=(255, 255, 255, 110))
    # white glyph with dark halo
    cx, cy = width // 2, CAP_H // 2 - 1
    g = Image.new("RGBA", im.size)
    gd = ImageDraw.Draw(g)
    w = 3
    if glyph == "close":
        gd.line([(cx - 5, cy - 4), (cx + 5, cy + 4)], fill="white", width=w)
        gd.line([(cx - 5, cy + 4), (cx + 5, cy - 4)], fill="white", width=w)
    elif glyph == "hide":
        gd.rectangle([cx - 5, cy + 2, cx + 5, cy + 4], fill="white")
    elif glyph == "maximize":
        gd.rectangle([cx - 6, cy - 4, cx + 6, cy + 5], outline="white", width=2)
        gd.line([(cx - 6, cy - 3), (cx + 6, cy - 3)], fill="white", width=2)
    elif glyph == "maximize-toggled":
        gd.rectangle([cx - 3, cy - 6, cx + 6, cy + 1], outline="white", width=2)
        gd.rectangle([cx - 6, cy - 2, cx + 3, cy + 5], outline="white", width=2)
    elif glyph == "menu":
        gd.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill="white")
    elif glyph == "shade":
        gd.polygon([(cx - 5, cy + 3), (cx + 5, cy + 3), (cx, cy - 3)], fill="white")
    elif glyph == "stick":
        gd.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], outline="white", width=2)
    halo = g.split()[3].filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: min(255, v * 2))
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shadow.putalpha(halo)
    im = Image.alpha_composite(im, shadow)
    if inactive:
        g.putalpha(g.split()[3].point(lambda v: v * 0.6))
    return Image.alpha_composite(im, g)


for glyph in ("close", "hide", "maximize", "maximize-toggled", "menu", "shade", "stick",
              "shade-toggled", "stick-toggled"):
    base = glyph.replace("-toggled", "") if glyph in ("shade-toggled", "stick-toggled") else glyph
    width = 46 if glyph == "close" else 28
    red = glyph == "close"
    save(cap(width, "close" if red else "plain", base), f"{glyph}-active")
    save(cap(width, "close" if red else "plain", base, inactive=True), f"{glyph}-inactive")
    save(cap(width, "close_hl" if red else "plain_hl", base), f"{glyph}-prelight")
    save(cap(width, "close_pr" if red else "plain_pr", base), f"{glyph}-pressed")

print("xfwm4 assets written to", OUT)
