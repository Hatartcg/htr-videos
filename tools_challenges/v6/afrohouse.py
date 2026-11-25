"""afrohouse.py — procedural afro-house bed (zero credits). New for HTR on 25 Nov 2026 (differs from lo-fi/phonk/darbuka/
synth-pop/cinematic/piano beds). python3 afrohouse.py out.wav dur bpm seed [ticks=t,...] [hits=t,...] [whoosh=t,...] [duck=t0:t1,...] [drop=t]
Four-on-the-floor kick, offbeat open hats, 16th shaker, log-drum bass (amapiano-style pitch glide), marimba riff in A minor pentatonic."""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
SR = 48000
out, DUR, BPM, SEED = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
kw = {}
for a in sys.argv[5:]:
    k, v = a.split('=', 1); kw[k] = v
rng = np.random.default_rng(SEED); N = int(DUR * SR); B = 60 / BPM
mix = np.zeros(N); fx = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def lp(s, fc): b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def kick():
    t = tt(.4); f = 48 + 110 * np.exp(-t / .03); return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / .22)
def ohat(): t = tt(.18); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / .06)
def shaker(): t = tt(.05); return bp(rng.standard_normal(len(t)), 4000, 11000) * np.sin(np.pi * np.minimum(1, t / .05)) ** 2
def rim(): t = tt(.06); return bp(rng.standard_normal(len(t)), 1800, 5000) * np.exp(-t / .01) + .6 * np.sin(2 * np.pi * 1700 * t) * np.exp(-t / .012)
def logdrum(m, d):
    t = tt(d); f = mtof(m) * (1 + .35 * np.exp(-t / .05)) * (1 - .06 * np.minimum(1, t / d))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) + .35 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return np.tanh(1.6 * s) * np.exp(-t / (d * .7)) * np.minimum(1, t / .003)
def marimba(m, d=.45):
    t = tt(d); f = mtof(m); s = np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / .03)
    return s * np.exp(-t / .16) * np.minimum(1, t / .002)
AM = [57, 60, 62, 64, 67, 69, 72, 74]           # A minor pentatonic
riff = [(0, 5), (.75, 4), (1.5, 6), (2, 5), (2.75, 3), (3.25, 4), (3.5, 2)]
bass = [(0, 45, 1.2), (1.5, 45, .5), (2.25, 48, .6), (3, 43, .9)]
duck = []
for seg in kw.get('duck', '').split(','):
    if seg: a, b = seg.split(':'); duck.append((float(a), float(b)))
drop = float(kw.get('drop', 0))
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; full = t0 >= drop
    for q in range(4):
        add(mix, t0 + q * B, kick(), .55 if full else .3)
        add(mix, t0 + q * B + B / 2, ohat(), .09)
    for s in range(16): add(mix, t0 + s * B / 4, shaker(), .05 + .03 * (s % 4 == 2))
    for pos in (1.75, 3.5): add(mix, t0 + pos * B, rim(), .16)
    if full:
        for pos, m, d in bass: add(mix, t0 + pos * B, logdrum(m, d * B), .34)
    for pos, i in riff:
        add(mix, t0 + pos * B, marimba(AM[i] + (12 if b % 4 == 3 else 0)), .2)
g = np.ones(N)
for a, b2 in duck:
    i0, i1 = int(a * SR), int(b2 * SR); g[i0:i1] = .45
g = np.convolve(g, np.ones(2400) / 2400, mode='same'); mix *= g
for t in [float(x) for x in kw.get('ticks', '').split(',') if x]:
    s = tt(.08); add(fx, t, np.sin(2 * np.pi * 1200 * s) * np.exp(-s / .015) + .6 * rim()[:len(s)], .45)
for t in [float(x) for x in kw.get('hits', '').split(',') if x]:
    s = tt(1.0); f = 46 + 130 * np.exp(-s / .04); boom = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-s / .45)
    add(fx, t, boom * .8 + bp(rng.standard_normal(len(s)), 300, 6000) * np.exp(-s / .12) * .3, .85)
for t in [float(x) for x in kw.get('whoosh', '').split(',') if x]:
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 500, 7000) * np.sin(np.pi * x) ** 2, .22)
fade = np.ones(N); fade[:int(.02 * SR)] = np.linspace(0, 1, int(.02 * SR)); fo = int(.25 * SR); fade[-fo:] = np.linspace(1, .6, fo)
y = mix * fade + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
