#!/usr/bin/env python3
"""Synthesize the original Frutiger OS sound theme (no samples, all maths).

Writes freedesktop-named sounds to
  config/includes.chroot/usr/share/sounds/Frutiger/stereo/<name>.oga
Needs numpy and ffmpeg (with libvorbis). Re-run to tweak.
"""
import os, subprocess, tempfile, wave
import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "config/includes.chroot/usr/share/sounds/Frutiger/stereo")
os.makedirs(OUT, exist_ok=True)


def t(dur):
    return np.arange(int(SR * dur)) / SR


def note(freq):                       # MIDI-ish helper: semitones from A4
    return 440.0 * 2 ** (freq / 12)


def bell(f, dur, decay=3.0, bright=1.0):
    """Glassy bell: inharmonic partials with fast-decaying highs."""
    x = t(dur)
    partials = [(1, 1.0, 1.0), (2.0, .45 * bright, 1.6), (3.01, .22 * bright, 2.4),
                (4.17, .12 * bright, 3.5), (5.43, .06 * bright, 5.0)]
    s = sum(a * np.sin(2 * np.pi * f * r * x) * np.exp(-decay * k * x) for r, a, k in partials)
    attack = np.minimum(1, x / .004)
    return s * attack


def drop(f0, f1, dur, decay=14):
    """Water drop: a sine gliding in pitch with a quick decay."""
    x = t(dur)
    f = f0 * (f1 / f0) ** (x / dur)
    phase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(phase) * np.exp(-decay * x) * np.minimum(1, x / .002)


def pop(dur=.09, f0=500, f1=1400):
    """Bubble pop: rising blip plus a puff of filtered noise."""
    x = t(dur)
    blip = drop(f0, f1, dur, decay=40)
    noise = np.random.default_rng(1).standard_normal(len(x))
    noise = np.convolve(noise, np.ones(12) / 12, mode="same") * np.exp(-70 * x) * .35
    return blip + noise


def mix(length, *parts):
    """parts: (start_seconds, signal, gain)"""
    out = np.zeros(int(SR * length))
    for start, sig, g in parts:
        i = int(SR * start)
        n = min(len(sig), len(out) - i)
        out[i:i + n] += sig[:n] * g
    return out


def shimmer(sig, delays=(.031, .047, .071, .113), fb=.32):
    """Cheap airy reverb: a few decaying delay taps."""
    out = sig.copy()
    for k, d in enumerate(delays):
        n = int(SR * d)
        tap = np.zeros_like(sig)
        tap[n:] = sig[:-n] * fb * (.8 ** k)
        out += tap
    return out


def save(name, sig, gain=.8):
    sig = shimmer(sig)
    sig = sig / (np.max(np.abs(sig)) + 1e-9) * gain
    fade = min(len(sig), int(SR * .02))
    sig[-fade:] *= np.linspace(1, 0, fade)
    stereo = np.stack([sig, np.roll(sig, int(SR * .0007))], axis=1)   # a touch of width
    pcm = (stereo * 32767).astype("<i2")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "5",
                        os.path.join(OUT, name + ".oga")], check=True)
        os.unlink(tmp.name)


C5, E5, G5, B5, C6, D6, E6, G6 = (note(n) for n in (3, 7, 10, 14, 15, 17, 19, 22))

# Startup: a rising glassy arpeggio over a soft pad
pad = sum(np.sin(2 * np.pi * f * t(3.2)) for f in (C5 / 2, G5 / 2, E5)) * np.exp(-.9 * t(3.2)) * np.minimum(1, t(3.2) / .5) * .25
save("desktop-login", mix(3.4, (0, pad, 1), (.05, bell(C5, 2.5, 1.6), .7), (.22, bell(G5, 2.4, 1.6), .6),
                          (.39, bell(E6, 2.4, 1.6), .55), (.56, bell(G6, 2.4, 1.8, .8), .45), (.9, drop(2400, 1600, .4, 8), .2)))
save("desktop-logout", mix(2.4, (0, bell(G6, 1.8, 2), .45), (.16, bell(E6, 1.8, 2), .5), (.32, bell(G5, 1.9, 2), .55), (.48, bell(C5, 2, 1.8), .65)))
save("dialog-information", mix(1.0, (0, drop(1300, 700, .35), 1), (.08, bell(E6, .8, 5, .6), .3)))
save("message-new-instant", mix(.9, (0, drop(1500, 820, .3), 1), (.13, drop(1900, 1100, .3), .7)))
save("message-new-email", mix(1.2, (0, bell(G5, 1, 4), .6), (.12, bell(D6, 1, 4), .6), (.1, drop(1600, 900, .3), .4)))
save("dialog-warning", mix(1.2, (0, bell(E5, 1.1, 3.5), .8), (.15, bell(E5, 1.1, 3.5), .5)))
save("dialog-error", mix(1.2, (0, bell(D6 / 2, 1, 4), .8), (.16, bell(B5 / 2, 1.1, 4), .8)))
save("bell", bell(C6, .7, 6), .6)
save("complete", mix(1.3, (0, bell(E6, 1.1, 3.5), .6), (.1, bell(G6, 1.2, 3.5), .6), (.05, drop(2200, 1300, .3), .3)))
save("window-close", pop(), .55)
save("window-new", mix(.4, (0, drop(700, 1400, .2, 22), 1), (.03, bell(G6, .3, 12, .4), .25)), .5)
save("button-pressed", mix(.08, (0, bell(note(31), .08, 60, .3), 1)), .35)       # glassy tick
save("menu-popup", mix(.15, (0, drop(1800, 2400, .12, 30), 1)), .3)
save("device-added", mix(.8, (0, bell(G5, .6, 6), .7), (.12, bell(C6, .7, 6), .7)))
save("device-removed", mix(.8, (0, bell(C6, .6, 6), .7), (.12, bell(G5, .7, 6), .7)))
save("trash-empty", mix(.7, *[(i * .07, pop(.08, 400 + 120 * i, 1200 + 150 * i), .8) for i in range(6)]))
save("screen-capture", mix(.6, (0, bell(note(27), .5, 8, .8), 1), (.05, drop(3000, 2000, .2, 20), .4)))
save("audio-volume-change", drop(1100, 900, .18, 25), .5)
save("power-plug", mix(.8, (0, drop(500, 1100, .3, 10), 1), (.12, bell(G5, .6, 6), .5)))
save("power-unplug", mix(.8, (0, drop(1100, 500, .3, 10), 1)))
save("system-ready", mix(1.6, (0, bell(C6, 1.2, 3), .6), (.15, bell(G6, 1.4, 3), .5)))
print("sounds written to", OUT)
