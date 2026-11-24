"""Procedural music + sound effects (numpy synthesis), synced to the animation beats/steps/flash."""
from timing import remap
import numpy as np, scipy.signal as sg, scipy.io.wavfile as wf, os
from config import *
SR = SAMPLE_RATE; N = int(DURATION * SR); rng = np.random.default_rng(5)
def T(n): return np.arange(n) / SR
def lp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sg.sosfilt(sg.butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, f0, f1, o=2): return sg.sosfilt(sg.butter(o, [f0, f1], 'band', fs=SR, output='sos'), x)
def place(track, snd, t, gain=1.0):
    t = remap(t)
    i = int(t * SR); j = min(N, i + len(snd))
    if i < N: track[i:j] += snd[:j - i] * gain
def env(n, a=.005, d=.3): t = T(n); return np.minimum(1, t / a) * np.exp(-t / d)

def impact(dur=1.4):
    n = int(dur * SR); t = T(n); f = 28 + 90 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2); nz = lp(rng.normal(0, 1, n), 1800) * np.exp(-t * 14) * .8
    return (boom + nz) * .9
def whoosh(dur=1.1, up=True):
    n = int(dur * SR); x = rng.normal(0, 1, n); t = T(n) / dur
    f = 300 + 5000 * (t ** 2 if up else (1 - t) ** 2); out = np.zeros(n); b = 2048
    for i in range(0, n - b, b):
        fc = float(f[i]); out[i:i + b] = bp(x[i:i + b], max(80, fc * .7), min(SR / 2 - 100, fc * 1.4), 2)
    return out * np.sin(np.pi * np.minimum(1, t)) ** 1.5 * .7
def thump(gain=1.0):
    n = int(.5 * SR); t = T(n); f = 62 - 20 * t * 2
    a = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 12)
    b = np.zeros(n); k = int(.17 * SR); b[k:] = (np.sin(2 * np.pi * 52 * t[:n - k]) * np.exp(-t[:n - k] * 14))[:n - k] * .7
    return (a + b) * gain
def step(gain=1.0):
    n = int(.18 * SR); t = T(n); return (lp(rng.normal(0, 1, n), 700) * np.exp(-t * 35) + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * .8) * gain
def click():
    n = int(.12 * SR); t = T(n); return (hp(rng.normal(0, 1, n), 2500) * np.exp(-t * 90) * .9)
def chime(f0=880, dur=2.2):
    n = int(dur * SR); t = T(n); x = np.zeros(n)
    for k, (m, g) in enumerate([(1, 1), (2.01, .5), (3.02, .3), (4.2, .15)]): x += np.sin(2 * np.pi * f0 * m * t) * g * np.exp(-t * (2 + k))
    return x * .35
def applause(dur=2.2):
    n = int(dur * SR); x = np.zeros(n)
    for _ in range(int(dur * 70)):
        p = rng.integers(0, n - 800); x[p:p + 800] += bp(rng.normal(0, 1, 800), 1200, 6000) * np.exp(-T(800) * 500) * rng.uniform(.3, 1)
    return lp(x, 7000) * np.minimum(1, T(n) / .5) * np.minimum(1, (dur - T(n)) / .3) * .5

def make_sfx():
    s = np.zeros(N)
    place(s, lp(rng.normal(0, 1, int(4.0 * SR)), 140) * np.minimum(1, T(int(4.0 * SR)) / 1.5) * .35, 0.0)           # S1 room rumble
    place(s, impact(), 2.2, .9); place(s, whoosh(.6, True), 1.9, .6)                                                # sign slam
    for t in (4.0, 9.0, 14.0, 18.5, 26.0): place(s, whoosh(1.0, True), t - .35, .5)                                  # scene transitions
    place(s, impact(.8), 4.0, .4)
    place(s, click(), 6.0, .8); place(s, np.sin(2 * np.pi * 2800 * T(int(.08 * SR))) * env(int(.08 * SR), .002, .03) * .4, 6.2, .5)  # needle
    for k in range(5): place(s, lp(rng.normal(0, 1, int(.3 * SR)), 1500) * env(int(.3 * SR), .05, .15) * .35, 7.5 + k * .3, .5)         # tube slide
    k = 0
    while True:                                                                                                       # heart beat (matches animation beat())
        tb = k * .86; k += 1
        if tb < 9.2: continue
        if tb > 23.0: break
        g = 1.0 if tb < 14.2 else (.35 if tb > 18.4 else 0)
        if g: place(s, thump(1.0), tb, .8 * g)
    for i in range(12): place(s, step(1.0), 14.0 + i * .40625 + .1, .55)                                             # footsteps (walk cycle)
    place(s, hp(rng.normal(0, 1, int(4.5 * SR)), 4000) * 0.0, 18.5)
    ham = np.sin(2 * np.pi * 120 * T(int(4.5 * SR))) * .06 + np.sin(2 * np.pi * 60 * T(int(4.5 * SR))) * .08; place(s, ham, 18.5)    # X-ray hum
    place(s, click(), 21.0, 1.0); place(s, impact(1.2), 21.0, .7)                                                      # photo flash
    place(s, np.sin(2 * np.pi * (4000 * np.exp(-T(int(.8 * SR)) * 3)) * T(int(.8 * SR))) * env(int(.8 * SR), .01, .25) * .12, 21.0)
    place(s, impact(1.2), 23.0, .9)                                                                                     # boss slam
    for i in range(4): place(s, step(1.0), 25.25 + i * .4, .5)                                                          # walking away
    place(s, chime(880), 26.1, .8); place(s, chime(1320, 2.0), 26.25, .5)
    for i in range(24): place(s, chime(rng.choice([1760, 2093, 2637]), .5), 26.4 + rng.uniform(0, 3.4), .12)           # sparkles
    place(s, applause(2.4), 27.7, .8)
    return s

def make_music():
    t = T(N); m = np.zeros(N)
    def pad(freqs, t0, t1, g=1.0):
        t0, t1 = remap(t0), remap(t1)
        i, j = int(t0 * SR), int(t1 * SR); tt = t[i:j] - t0; e = np.minimum(1, tt / 1.0) * np.minimum(1, (t1 - t[i:j]) / 1.2); x = np.zeros(j - i)
        for f in freqs:
            for d in (-.4, 0, .5): x += sg.sawtooth(2 * np.pi * (f + d) * tt) * .08 + np.sin(2 * np.pi * (f + d) * tt) * .1
        m[i:j] += lp(x, 1800) * e * g
    A1, E2, A2, C3, E3, G3, B2 = 55, 82.4, 110, 130.8, 164.8, 196, 123.5
    pad([A1, A2, C3, E3], 0, 9, .9); pad([A1, E2, A2, B2 * 2.0], 9, 14, 1.1); pad([A1 * 1.0, E2, A2, C3], 14, 18.6, .8)
    pad([A1, 220, 233.1 * 1.0], 18.4, 23.1, .9); pad([A1 * .98, 130.8, 138.6, 196], 22.9, 26.1, 1.0); pad([110, 138.6, 164.8, 220, 277.2], 26, 30, 1.2)  # major lift
    # pulse
    for k in range(int(30 / .43)):
        tb = k * .43
        if 4 <= tb < 26: place(m, np.sin(2 * np.pi * 55 * T(int(.3 * SR))) * env(int(.3 * SR), .003, .09) * .5, tb, .5 if tb < 14 else .6)
    # riser into S3 and S7 + high shimmer in X-ray room
    for a, b in ((7.5, 9.0), (24.5, 26.0)):
        n = int((b - a) * SR); x = hp(rng.normal(0, 1, n), 2500) * (T(n) / (b - a)) ** 2 * .35; place(m, x, a)
    n = int(4.4 * SR); place(m, (np.sin(2 * np.pi * 1760 * T(n)) + np.sin(2 * np.pi * 1864 * T(n))) * .03 * np.minimum(1, T(n)), 18.6)
    # S7 arpeggio bells
    for i, f in enumerate([440, 554.4, 659.3, 880, 659.3, 554.4, 880, 1108.7] * 3):
        tb = 26.2 + i * .16
        if tb < 29.6: place(m, np.sin(2 * np.pi * f * T(int(.9 * SR))) * env(int(.9 * SR), .004, .35) * .18, tb)
    m *= np.minimum(1, t / 1.0) * np.minimum(1, (DURATION - t) / 1.2)
    return m / (np.abs(m).max() + 1e-9) * .5

def build():
    s, m = make_sfx(), make_music(); s = s / (np.abs(s).max() + 1e-9) * .8
    for name, x in (("sfx", s), ("music", m)):
        wf.write(os.path.join(DIRS["output"], f"{name}.wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    return s, m
if __name__ == "__main__": build(); print("sfx+music written")
