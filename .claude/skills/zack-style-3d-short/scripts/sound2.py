"""Sound design for the reference-style cut: soft cinematic music bed under dense narration,
a whoosh on most cuts, foley synced to shot events. Writes output/music.wav + output/sfx.wav (length = timeline)."""
import json, os, numpy as np, scipy.io.wavfile as wf
import sound_design as sd
from config import DIRS, SAMPLE_RATE as SR

DUR = json.load(open(os.path.join(DIRS["output"], "timeline.json")))["duration"]
N = int(DUR * SR); rng = np.random.default_rng(11)
CUTS = [1.75, 2.90, 4.20, 5.60, 6.95, 8.80, 10.90, 12.95, 15.00, 16.05, 17.60, 19.00, 20.35, 21.50, 23.45, 24.95, 26.40]
T = sd.T


def place(tr, x, t, g=1.):
    i = int(t * SR); j = min(N, i + len(x))
    if 0 <= i < N: tr[i:j] += x[:j - i] * g


def make_sfx():
    s = np.zeros(N)
    for k, c in enumerate(CUTS): place(s, sd.whoosh(.55, k % 2 == 0), c - .28, .28)
    place(s, sd.lp(rng.normal(0, 1, int(1.2 * SR)), 2500) * sd.env(int(1.2 * SR), .3, .5) * .25, .2)     # tube rustle (hook)
    place(s, sd.impact(.8), 4.45, .45)                                                                   # boss slam-point
    place(s, sd.click(), 6.05, .7); place(s, np.sin(2 * np.pi * 2800 * T(int(.08 * SR))) * sd.env(int(.08 * SR), .002, .03) * .4, 6.1, .5)
    for k in range(9): place(s, sd.lp(rng.normal(0, 1, int(.25 * SR)), 1400) * sd.env(int(.25 * SR), .04, .12) * .3, 7.0 + k * .42, .45)  # tube slide
    for tb in np.arange(11.0, 16.1, .82): place(s, sd.thump(1.), tb, .7)                                 # heartbeat
    for tb in np.arange(15.0, 16.05, .55): place(s, sd.thump(1.), tb, .9)
    for i in range(14): place(s, sd.step(1.), 16.15 + i * .45, .55)                                      # footsteps
    place(s, sd.click(), 19.75, .8); place(s, sd.lp(rng.normal(0, 1, int(.7 * SR)), 900) * sd.env(int(.7 * SR), .05, .3) * .4, 19.8)  # door
    hum = np.sin(2 * np.pi * 120 * T(int(3.1 * SR))) * .06 + np.sin(2 * np.pi * 60 * T(int(3.1 * SR))) * .08
    place(s, hum * np.minimum(1, T(len(hum)) / .4), 20.35)
    place(s, sd.click(), 21.38, 1.); place(s, sd.impact(1.2), 21.4, .75)                                 # flash
    for tb in np.arange(21.6, 23.4, .82): place(s, sd.thump(1.), tb, .35)
    place(s, sd.impact(1.2), 23.5, .8)                                                                   # boss
    place(s, sd.chime(880), 25.0, .7); place(s, sd.chime(1320, 2.), 25.15, .45)
    for i in range(18): place(s, sd.chime(rng.choice([1760, 2093, 2637]), .5), 25.2 + rng.uniform(0, 3.6), .1)
    place(s, sd.applause(2.8), 26.4, .9)
    return s / (np.abs(s).max() + 1e-9) * .8


def make_music():
    t = T(N); m = np.zeros(N)
    import scipy.signal as sg

    def pad(freqs, t0, t1, g=1.):
        i, j = int(t0 * SR), min(N, int(t1 * SR)); tt = t[i:j] - t0
        e = np.minimum(1, tt / .6) * np.minimum(1, (t1 - t[i:j]) / .8); x = np.zeros(j - i)
        for f in freqs:
            for d in (-.3, 0, .4): x += sg.sawtooth(2 * np.pi * (f + d) * tt) * .06 + np.sin(2 * np.pi * (f + d) * tt) * .1
        m[i:j] += sd.lp(x, 1600) * e * g
    pad([55, 110, 130.8, 164.8], 0, 8.9); pad([49, 98, 123.5, 146.8], 8.8, 16.1, 1.1); pad([55, 110, 130.8, 196], 16, 23.5, .9)
    pad([43.65, 87.3, 130.8, 174.6], 23.4, 25.0, 1.); pad([55, 110, 138.6, 164.8, 220, 277.2], 24.9, DUR, 1.2)
    for k in range(int(DUR / .41)):
        tb = k * .41
        if 1.7 < tb < 24.9: place(m, np.sin(2 * np.pi * 55 * T(int(.25 * SR))) * sd.env(int(.25 * SR), .003, .08) * .45, tb)
    for i, f in enumerate([440, 554.4, 659.3, 880] * 6):
        tb = 25.0 + i * .17
        if tb < DUR - .4: place(m, np.sin(2 * np.pi * f * T(int(.8 * SR))) * sd.env(int(.8 * SR), .004, .3) * .16, tb)
    m *= np.minimum(1, t / .5) * np.minimum(1, (DUR - t) / 1.)
    return m / (np.abs(m).max() + 1e-9) * .5


def build():
    for name, x in (("sfx", make_sfx()), ("music", make_music())):
        wf.write(os.path.join(DIRS["output"], f"{name}.wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))


if __name__ == "__main__":
    build(); print("sfx+music", DUR, "s")
