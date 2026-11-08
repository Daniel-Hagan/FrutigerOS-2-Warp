#!/usr/bin/env python3
"""Build the "Frutiger-Gloss" icon theme: every app icon inside a glass bubble.

    make_gloss_icons.py [--src DIR ...] [--dest DIR]

Default sources: Papirus 64x64 app icons, then hicolor (scalable + 256/128/64 PNGs).
Default dest:    /usr/share/icons/Frutiger-Gloss/scalable/apps
Existing outputs are kept (so re-runs after apt installs are quick). SVG sources
are embedded as a nested <svg>; PNG sources as a base64 <image>.
"""
import argparse, base64, hashlib, os, re, sys

WRAP = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="64" height="64" viewBox="0 0 64 64">
<defs>
<radialGradient id="fglB{u}" cx=".5" cy=".42" r=".55"><stop offset="0" stop-color="#ffffff" stop-opacity=".92"/><stop offset=".72" stop-color="#d6efff" stop-opacity=".85"/><stop offset="1" stop-color="#7cc4f2" stop-opacity=".9"/></radialGradient>
<linearGradient id="fglG{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="fglS{u}" cx=".5" cy=".5" r=".5"><stop offset=".75" stop-color="#002244" stop-opacity=".28"/><stop offset="1" stop-color="#002244" stop-opacity="0"/></radialGradient>
</defs>
<circle cx="32" cy="34" r="31" fill="url(#fglS{u})"/>
<circle cx="32" cy="32" r="29.5" fill="url(#fglB{u})"/>
{icon}
<ellipse cx="29" cy="15" rx="20" ry="10.5" fill="url(#fglG{u})"/>
<circle cx="32" cy="32" r="29.5" fill="none" stroke="#ffffff" stroke-opacity=".95" stroke-width="1.4"/>
<circle cx="32" cy="32" r="30.4" fill="none" stroke="#0a3a66" stroke-opacity=".35" stroke-width=".8"/>
</svg>
"""
INNER = 'x="13" y="13" width="38" height="38"'


def wrap_svg(text, uid):
    text = re.sub(r"<\?xml[^>]*\?>", "", text)
    text = re.sub(r"<!DOCTYPE[^>]*>", "", text)
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>", text, re.S)
    if not m:
        return None
    attrs, body = m.group(1), m.group(2)
    vb = re.search(r'viewBox\s*=\s*"([^"]+)"', attrs)
    if vb:
        viewbox = vb.group(1)
    else:
        w = re.search(r'\bwidth\s*=\s*"([\d.]+)', attrs)
        h = re.search(r'\bheight\s*=\s*"([\d.]+)', attrs)
        viewbox = "0 0 %s %s" % (w.group(1) if w else 64, h.group(1) if h else 64)
    # keep ids unique when GTK caches several icons in one document? (not needed, but harmless)
    body = re.sub(r'id="([^"]+)"', lambda k: 'id="%s_%s"' % (uid, k.group(1)), body)
    body = re.sub(r'url\(#([^)]+)\)', lambda k: "url(#%s_%s)" % (uid, k.group(1)), body)
    body = re.sub(r'(xlink:)?href="#([^"]+)"', lambda k: '%shref="#%s_%s"' % (k.group(1) or "", uid, k.group(2)), body)
    return '<svg %s viewBox="%s" preserveAspectRatio="xMidYMid meet">%s</svg>' % (INNER, viewbox, body)


def wrap_png(path):
    data = base64.b64encode(open(path, "rb").read()).decode()
    return '<image %s preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,%s"/>' % (INNER, data)


def build(sources, dest):
    os.makedirs(dest, exist_ok=True)
    done = set(os.listdir(dest))
    made = 0
    for src in sources:
        if not os.path.isdir(src):
            continue
        for fn in sorted(os.listdir(src)):
            name, ext = os.path.splitext(fn)
            if ext not in (".svg", ".png") or name.endswith("-symbolic"):
                continue
            out = name + ".svg"
            if out in done:
                continue
            path = os.path.realpath(os.path.join(src, fn))
            if not os.path.isfile(path):
                continue
            uid = "i" + hashlib.md5(name.encode()).hexdigest()[:6]
            try:
                icon = wrap_svg(open(path, encoding="utf-8", errors="replace").read(), uid) if ext == ".svg" else wrap_png(path)
            except Exception:
                icon = None
            if not icon:
                continue
            with open(os.path.join(dest, out), "w") as f:
                f.write(WRAP.replace("{u}", uid).replace("{icon}", icon))
            done.add(out)
            made += 1
    return made


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", action="append")
    ap.add_argument("--dest", default="/usr/share/icons/Frutiger-Gloss/scalable/apps")
    a = ap.parse_args()
    srcs = a.src or ["/usr/share/icons/Papirus/64x64/apps",
                     "/usr/share/icons/hicolor/scalable/apps", "/usr/share/icons/hicolor/256x256/apps",
                     "/usr/share/icons/hicolor/128x128/apps", "/usr/share/icons/hicolor/64x64/apps",
                     "/usr/share/icons/hicolor/48x48/apps", "/usr/share/pixmaps"]
    n = build(srcs, a.dest)
    print("Frutiger-Gloss: %d new icons in %s" % (n, a.dest), file=sys.stderr)
