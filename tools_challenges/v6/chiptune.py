"""chiptune.py — procedural 8-bit chiptune bed (zero credits). New for HTR on 25 Nov 2026 (differs from lo-fi/phonk/darbuka/
afro-house/piano/cinematic/synth-pop). python3 chiptune.py out.wav dur bpm seed [ticks=t,..] [hits=t,..] [whoosh=t,..] [duck=t0:t1,..] [stop=t0:t1,..]
Square-wave lead + arpeggio, triangle bass, noise-channel drums (NES-style). stop = record-stop silences (comedy beats)."""
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
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def sq(m, d, duty=.5, dec=.25):
    t = tt(d); ph = (t * mtof(m)) % 1; s = np.where(ph < duty, 1.0, -1.0)
    return s * np.exp(-t / dec) * np.minimum(1, t / .003) * np.minimum(1, (d - t) / .01)
def tri(m, d):
    t = tt(d); ph = (t * mtof(m)) % 1; s = 4 * np.abs(ph - .5) - 1
    return s * np.minimum(1, (d - t) / .01)
def nkick(): t = tt(.12); f = 120 * np.exp(-t / .02) + 50; return np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / .05)
def nsnare(): t = tt(.15); return np.sign(rng.standard_normal(len(t))) * np.exp(-t / .05) * .6
def nhat(): t = tt(.03); return np.sign(rng.standard_normal(len(t))) * np.exp(-t / .008) * .35
PROG = [(60, [60, 64, 67, 72]), (57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (55, [55, 59, 62, 67])]   # C Am F G
MEL = [(0, 76), (.5, 79), (1, 84), (1.5, 79), (2, 81), (2.5, 79), (3, 76), (3.5, 74)]
duck = [tuple(map(float, s.split(':'))) for s in kw.get('duck', '').split(',') if s]
stops = [tuple(map(float, s.split(':'))) for s in kw.get('stop', '').split(',') if s]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; root, ch = PROG[b % 4]
    for q in range(4):
        add(mix, t0 + q * B, nkick() if q % 2 == 0 else nsnare(), .35)
        for e in range(2): add(mix, t0 + q * B + e * B / 2, nhat(), .5)
        add(mix, t0 + q * B, tri(root - 24, B * .9), .28); add(mix, t0 + q * B + B / 2, tri(root - 12, B * .4), .2)
    for s in range(16): add(mix, t0 + s * B / 4, sq(ch[s % 4], B / 4, .25, .06), .06)
    for pos, m in MEL: add(mix, t0 + pos * B, sq(m + (2 if b % 8 >= 4 and pos >= 2 else 0) - (12 if b % 2 else 0), B * .45, .5, .18), .1)
g = np.ones(N)
for a, b2 in duck: g[int(a * SR):int(b2 * SR)] = .35
for a, b2 in stops: g[int(a * SR):int(b2 * SR)] = 0
g = np.convolve(g, np.ones(480) / 480, mode='same'); mix *= g
for a, b2 in stops:   # tape-stop pitch-down blip before each stop
    s = tt(.35); f = 600 * (1 - s / .35) + 60; add(fx, a - .3, np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * (1 - s / .35) * .25)
for t in [float(x) for x in kw.get('ticks', '').split(',') if x]: add(fx, t, sq(96, .08, .5, .02), .35)
for t in [float(x) for x in kw.get('hits', '').split(',') if x]:
    s = tt(.6); add(fx, t, sum(sq(m, .6, .5, .2) for m in (72, 76, 79, 84)) * .25, .7)
for t in [float(x) for x in kw.get('whoosh', '').split(',') if x]:
    s = tt(.4); x = s / .4; add(fx, t - .35, bp(rng.standard_normal(len(s)), 600, 7000) * np.sin(np.pi * x) ** 2, .2)
fade = np.ones(N); fade[:int(.02 * SR)] = np.linspace(0, 1, int(.02 * SR))
y = mix * fade + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
