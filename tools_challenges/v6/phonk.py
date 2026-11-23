"""phonk.py — procedural drift-phonk bed (zero credits): cowbell riff, distorted 808, rolling hats, VHS tape wobble.
python3 phonk.py out.wav dur bpm seed [hits=..] [whoosh=..] [stops=t1,..]   (stops = 0.25 s tape-stop dips on reveals)"""
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
    if 0 <= i < N: s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def cowbell(m, d=.22):
    t = tt(d); f = mtof(m); s = np.sign(np.sin(2 * np.pi * f * t)) + .6 * np.sign(np.sin(2 * np.pi * f * 1.48 * t))
    return bp(s, 500, 4000) * np.exp(-t / .07) * .5
def b808(m, d):
    t = tt(d); f = mtof(m) * (1 + .8 * np.exp(-t / .02)); return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / .6)
def snare():
    t = tt(.25); return lp(bp(rng.standard_normal(len(t)), 900, 8000) * np.exp(-t / .06) + .5 * np.sin(2 * np.pi * 200 * t) * np.exp(-t / .04), 7000)
def hat(): t = tt(.03); return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t / .008)
riff = [(0, 70), (.75, 70), (1.5, 73), (2, 72), (2.5, 70), (3, 68), (3.5, 67)]  # F#m-ish phonk riff (new, not reused)
bass = [(0, 30), (1.5, 30), (2, 33), (3, 28)]
bar = 4 * B
for b in range(int(DUR / bar) + 1):
    t0 = b * bar
    for st, m in riff: add(mix, t0 + st * B, cowbell(m + (12 if b % 4 == 3 and st > 2 else 0)), .34)
    for st, m in bass: add(mix, t0 + st * B, b808(m, B * 1.4), .42)
    for s in range(16):
        add(mix, t0 + s * B / 4, hat(), .07 if s % 2 else .11)
        if s in (6, 14) and b % 2: add(mix, t0 + s * B / 4 + B / 8, hat(), .06)
    add(mix, t0 + B, snare(), .35); add(mix, t0 + 3 * B, snare(), .35)
# tape wobble
mix = np.interp(np.arange(N) + 30 * np.sin(2 * np.pi * .6 * np.arange(N) / SR), np.arange(N), mix)
for t in kw.get('stops', []):
    i, n = int(t * SR), int(.25 * SR)
    if i + n < N: mix[i:i + n] *= np.linspace(1, 0, n) ** 2
for t in kw.get('hits', []):
    s = tt(1.2); add(fx, t, np.tanh(2 * np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-s / .05)) / SR)) * np.exp(-s / .5) + bp(rng.standard_normal(len(s)), 200, 3000) * np.exp(-s / .15) * .4, .7)
for t in kw.get('whoosh', []):
    s = tt(.35); add(fx, t - .1, hp(rng.standard_normal(len(s)), 1500) * np.exp(-s / .08), .25)
fade = np.ones(N); f = int(.4 * SR); fade[-f:] = np.linspace(1, 0, f)
y = (mix + fx) * fade; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32)); print('ok', out)
