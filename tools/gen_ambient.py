#!/usr/bin/env python3
"""Ambient sounds for Frutiger OS ("Ambient sounds" in Personalize → Desktop).

  water.oga   a soft, seamless 40-second loop of lapping water
  bird1-6.oga short bird calls, played now and then over it

Writes to config/includes.chroot/usr/share/sounds/frutiger/ambient/.
Needs numpy and ffmpeg (with libvorbis). Re-run to tweak.
"""
import os, subprocess, tempfile, wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "config/includes.chroot/usr/share/sounds/frutiger/ambient")
rng = np.random.default_rng(42)


def save(name, x):
    os.makedirs(OUT, exist_ok=True)
    x = np.clip(x, -1, 1)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        with wave.open(tmp.name, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes((x * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp.name, "-c:a", "libvorbis", "-q:a", "4",
                        os.path.join(OUT, name)], check=True)
    os.unlink(tmp.name)


def bandpass(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    shape = np.exp(-((np.log(np.maximum(f, 1)) - np.log(np.sqrt(lo * hi))) ** 2) / (2 * (np.log(hi / lo) / 2.5) ** 2))
    return np.fft.irfft(X * shape, len(x))


def water(seconds=40):
    n = SR * seconds
    noise = rng.standard_normal(n)
    body = bandpass(noise, 180, 900)              # FFT filtering wraps around, so the loop is seamless
    sparkle = bandpass(rng.standard_normal(n), 1200, 3200)
    t = np.arange(n) / SR
    # waves: slow swells whose periods divide the loop length exactly (seamless)
    swell = .55 + .25 * np.sin(2 * np.pi * t * 4 / seconds) + .2 * np.sin(2 * np.pi * t * 11 / seconds + 1.3)
    lap = np.clip(np.sin(2 * np.pi * t * 9 / seconds + .4), 0, 1) ** 3
    x = body / np.abs(body).max() * swell * .55 + sparkle / np.abs(sparkle).max() * (.08 + .22 * lap)
    return x / np.abs(x).max() * .5


def bird(seed):
    r = np.random.default_rng(seed)
    notes, f0 = 2 + r.integers(0, 4), 2600 + r.random() * 1600
    gap = .11 + r.random() * .06
    n = int(SR * (notes * gap + .2))
    x = np.zeros(n)
    for i in range(notes):
        st, dur = int(i * gap * SR), int(.1 * SR)
        tt = np.arange(dur) / SR
        f1 = f0 * (1 + (r.random() - .5) * .2)
        f2 = f0 * (.75 + r.random() * .5)
        freq = f1 * (f2 / f1) ** (tt / .09) + 90 * np.sin(2 * np.pi * 32 * tt)
        ph = 2 * np.pi * np.cumsum(freq) / SR
        env = np.minimum(1, tt / .015) * np.exp(-np.maximum(0, tt - .015) * 45)
        x[st:st + dur] += np.sin(ph) * env
    return x / np.abs(x).max() * .35


if __name__ == "__main__":
    save("water.oga", water())
    for k in range(1, 7):
        save(f"bird{k}.oga", bird(k * 17))
    print("wrote", sorted(os.listdir(OUT)))
