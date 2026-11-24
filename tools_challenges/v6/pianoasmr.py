"""pianoasmr.py — procedural soft felt-piano + light kick/shaker bed for ASMR-style pack openings (zero credits). New 24 Nov 2026.
python3 pianoasmr.py out.wav dur bpm seed [hits=t,...] [ticks=t,...] [whoosh=t,...] [stop=t0:t1,...]
stop = sections where the bed drops out completely (silence-before-the-reveal moments; keep them short)."""
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
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def piano(m, d=1.6):
    t = tt(d); f = mtof(m); s = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (1.2 + h * .9)) / h ** 1.6 for h in (1, 2, 3, 4))
    return lp(s * np.minimum(1, t / .004), 2400)
def kick(): t = tt(.25); f = 50 + 70 * np.exp(-t / .02); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .12)
def shaker(): t = tt(.06); return hp(rng.standard_normal(len(t)), 6000) * np.exp(-t / .015)
# Fmaj7 – Em7 – Dm9 – Cadd9, arpeggiated
prog = [[53, 57, 60, 64, 69], [52, 55, 59, 62, 67], [50, 53, 57, 60, 64], [48, 52, 55, 62, 67]]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; ch = prog[b % 4]
    add(mix, t0, piano(ch[0] - 12, bar), .35)
    for k, m in enumerate([ch[1], ch[2], ch[3], ch[4], ch[3], ch[2], ch[4], ch[3]]):
        add(mix, t0 + k * B / 2, piano(m + 12, 1.2), .16 + .04 * (k == 0))
    add(mix, t0, kick(), .35); add(mix, t0 + 2 * B, kick(), .3)
    for s in range(8): add(mix, t0 + s * B / 2 + B / 4, shaker(), .05)
g = np.ones(N)
for seg in kw.get('stop', '').split(','):
    if seg: a, b2 = [float(x) for x in seg.split(':')]; g[int(a * SR):int(b2 * SR)] = 0.0
mix *= np.convolve(g, np.ones(1200) / 1200, mode='same')
for t in L('hits'):
    s = tt(1.5); add(fx, t, sum(piano(m, 1.5) for m in (60, 64, 67, 72, 76)) * .4 + kick()[:len(s)] if False else sum(piano(m, 1.5) for m in (60, 64, 67, 72, 76)) * .45, 1)
    add(fx, t, kick(), .6)
for t in L('ticks'):
    s = tt(.08); add(fx, t, np.sin(2 * np.pi * 2000 * s) * np.exp(-s / .01), .3)
for t in L('whoosh'):
    s = tt(.4); x = s / .4; add(fx, t - .35, bp(rng.standard_normal(len(s)), 600, 7000) * np.sin(np.pi * x) ** 2, .18)
y = mix + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32)); print('ok', out)
