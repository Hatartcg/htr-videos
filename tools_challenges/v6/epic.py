"""epic.py — procedural cinematic trailer bed (taiko + low strings + brass stabs), zero credits. New 24 Nov 2026.
python3 epic.py out.wav dur bpm seed [hits=t,...] [ticks=t,...] [whoosh=t,...] [duck=t0:t1,...]"""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
SR = 48000
out, DUR, BPM, SEED = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
kw = dict(a.split('=', 1) for a in sys.argv[5:])
L = lambda k: [float(x) for x in kw.get(k, '').split(',') if x]
rng = np.random.default_rng(SEED); N = int(DUR * SR); B = 60 / BPM
mix = np.zeros(N); fx = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def lp(s, fc): b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def taiko(f0=70):
    t = tt(.9); f = f0 + 50 * np.exp(-t / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .35) + .35 * lp(rng.standard_normal(len(t)), 1200) * np.exp(-t / .05)
def rim(): t = tt(.1); return bp(rng.standard_normal(len(t)), 2000, 7000) * np.exp(-t / .02)
def saw(f, t): return 2 * ((f * t) % 1) - 1
def strings(ms, d):
    t = tt(d); s = sum(saw(mtof(m) * (1 + .003 * k), t) for m in ms for k in (-1, 1))
    env = np.minimum(1, t / .25) * np.minimum(1, (d - t) / .2); return lp(s * env / (2 * len(ms)), 1400)
def brass(ms, d=.35):
    t = tt(d); s = sum(np.tanh(2 * saw(mtof(m), t)) for m in ms); env = np.minimum(1, t / .015) * np.exp(-t / .18)
    return lp(s * env / len(ms), 2500)
# A minor: Am – F – C – G (i–VI–III–VII)
prog = [[45, 57, 60, 64], [41, 53, 57, 60], [48, 55, 60, 64], [43, 55, 59, 62]]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; ch = prog[b % 4]
    add(mix, t0, strings(ch, bar), .30)
    for pos, g in ((0, .7), (1.5, .45), (2, .6), (3, .5), (3.5, .35)):
        add(mix, t0 + pos * B, taiko(65 if pos in (0, 2) else 95), g)
    for s in range(8): add(mix, t0 + s * B / 2, rim(), .06)
    if b % 2 == 1:
        add(mix, t0 + 3 * B, brass([m + 12 for m in ch[1:]]), .25); add(mix, t0 + 3.5 * B, brass([m + 12 for m in ch[1:]]), .2)
g = np.ones(N)
for seg in kw.get('duck', '').split(','):
    if seg: a, b2 = [float(x) for x in seg.split(':')]; g[int(a * SR):int(b2 * SR)] = .5
mix *= np.convolve(g, np.ones(2400) / 2400, mode='same')
for t in L('hits'):
    a, b2 = taiko(48), brass([45, 52, 57, 64], 1.0); n = min(len(a), len(b2)); add(fx, t, a[:n] + b2[:n] * .5, .8)
for t in L('ticks'):
    s = tt(.1); add(fx, t, np.sin(2 * np.pi * 1200 * s) * np.exp(-s / .02) + .6 * rim()[:len(s)], .45)
for t in L('whoosh'):
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 400, 6000) * np.sin(np.pi * x) ** 2, .22)
y = mix + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32)); print('ok', out)
