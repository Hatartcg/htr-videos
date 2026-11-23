"""lofi.py — procedural lo-fi boom-bap bed (zero credits). python3 lofi.py out.wav dur bpm seed [hits=t1,t2,...] [ticks=t1,...] [whoosh=t1,...]
Swung hats, dusty kick/snare, Rhodes-like 7th chords, vinyl crackle. hits = cash-register/impact accents, ticks = countdown ticks."""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
SR = 48000
out, DUR, BPM, SEED = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
kw = {a.split('=')[0]: [float(x) for x in a.split('=')[1].split(',') if x] for a in sys.argv[5:]}
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
    t = tt(.4); f = 45 + 110 * np.exp(-t / .03); return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .22))
def snare():
    t = tt(.3); n = bp(rng.standard_normal(len(t)), 1200, 7000) * np.exp(-t / .07); b = np.sin(2 * np.pi * 190 * t) * np.exp(-t / .05)
    return lp(n * .7 + b * .5, 5500)
def hat(o=False):
    t = tt(.12 if o else .035); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / (.05 if o else .01))
def rhodes(ms, d):
    t = tt(d); s = np.zeros(len(t))
    for m in ms:
        f = mtof(m); s += (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .3)) * np.exp(-t / 1.6)
    s *= 1 + .15 * np.sin(2 * np.pi * 4.5 * t); a = np.minimum(1, t / .01); return lp(s * a / len(ms), 2600)
def bass(m, d):
    t = tt(d); return lp(np.tanh(1.5 * np.sin(2 * np.pi * mtof(m) * t)) * np.exp(-t / .5) * np.minimum(1, t / .005), 400)
# Dm9 – G13 – Cmaj9 – Am7 (no copied progression from earlier HTR beds: this one is jazz ii-V-I)
prog = [([62, 65, 69, 72, 76], 38), ([59, 65, 69, 71, 76], 43), ([60, 64, 67, 71, 74], 36), ([57, 60, 64, 67, 72], 33)]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; ch, bn = prog[b % 4]
    add(mix, t0, rhodes(ch, bar), .20)
    add(mix, t0, bass(bn, B * 1.5), .28); add(mix, t0 + B * 2.5, bass(bn + 7, B), .2)
    for s in range(8):
        sw = (B / 2) * (0.62 if s % 2 else 0)  # swing
        add(mix, t0 + (s // 2) * B + sw, hat(s == 7), .05 + .02 * rng.random())
    add(mix, t0, kick(), .55); add(mix, t0 + B * 1.75, kick(), .35); add(mix, t0 + B * 2.5, kick(), .45)
    add(mix, t0 + B, snare(), .32); add(mix, t0 + 3 * B, snare(), .32)
crack = np.zeros(N); idx = rng.integers(0, N, int(DUR * 40)); crack[idx] = rng.standard_normal(len(idx)) * .3
mix += hp(crack, 2000) * .25 + lp(rng.standard_normal(N), 900) * .004
for t in kw.get('ticks', []):
    s = tt(.06); add(fx, t, np.sin(2 * np.pi * 1900 * s) * np.exp(-s / .012), .35)
for t in kw.get('hits', []):
    s = tt(.9); bell = sum(np.sin(2 * np.pi * f * s) * np.exp(-s / d) for f, d in ((1568, .5), (2093, .35), (3136, .2)))
    add(fx, t, bell * .18 + kick()[:len(s)] * .4 if len(kick()) >= len(s) else bell * .18, .8)
for t in kw.get('whoosh', []):
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 500, 5000) * np.sin(np.pi * x) ** 2, .18)
fade = np.ones(N); f = int(.6 * SR); fade[-f:] = np.linspace(1, 0, f)
y = (mix + fx) * fade; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
print('ok', out, DUR, BPM)
