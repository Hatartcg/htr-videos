"""dembow.py — procedural dembow / reggaeton bed (zero credits). New for HTR on 26 Nov 2026 (differs from lo-fi/phonk/darbuka/
afro-house/piano/cinematic/synth-pop/chiptune/dnb/swing). ~96 bpm: four-on-the-floor kick, the dembow snare figure
(3-3-2 feel), shaker 16ths, plucky minor synth riff, sub bass; slot-machine ticks for a fast card-flash reel.
python3 dembow.py out.wav dur bpm seed [ticks=t0:t1:rate,..] [hits=t,..] [whoosh=t,..] [duck=t0:t1,..] [intro=t]"""
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
def hp(s, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def kick(): t = tt(.25); f = 110 * np.exp(-t / .04) + 45; return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .16)
def snare(): t = tt(.16); return (bp(rng.standard_normal(len(t)), 1200, 7000) * .8 + np.sin(2 * np.pi * 220 * t) * .5) * np.exp(-t / .05)
def shaker(): t = tt(.05); return hp(rng.standard_normal(len(t)), 6000) * np.exp(-t / .015)
def pluck(m, d):
    t = tt(d); f = mtof(m); s = 2 * ((t * f) % 1) - 1 + .5 * np.sin(2 * np.pi * f * 2 * t)
    return s * np.exp(-t / .12) * np.minimum(1, t / .003)
def sub(m, d): t = tt(d); return np.sin(2 * np.pi * mtof(m) * t) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .02)
PROG = [57, 53, 55, 52]  # Am F G Em
RIFF = [(0, 0), (.75, 3), (1.5, 7), (2, 12), (2.75, 7), (3.5, 3)]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; r = PROG[b % 4]
    for q in range(4):
        add(mix, t0 + q * B, kick(), .8)
        add(mix, t0 + q * B + .75 * B, snare(), .45)               # dembow figure: snare on the "a" of each beat
        if q % 2: add(mix, t0 + q * B + .5 * B, snare(), .35)      # and on the "and" of beats 2 and 4
        for s in range(4): add(mix, t0 + q * B + s * B / 4, shaker(), .18 if s % 2 else .1)
    add(mix, t0, sub(r - 24, bar * .95), .35)
    for pos, iv in RIFF: add(mix, t0 + pos * B, pluck(r + iv, B * .5), .1)
intro = float(kw.get('intro', 0)); g = np.ones(N); g[:int(intro * SR)] = .3
for s in kw.get('duck', '').split(','):
    if s: a, b2 = map(float, s.split(':')); g[int(a * SR):int(b2 * SR)] *= .45
mix *= np.convolve(g, np.ones(960) / 960, mode='same')
for s in kw.get('ticks', '').split(','):  # slot-machine ticks: t0:t1:rate (per second)
    if not s: continue
    a, b2, rate = map(float, s.split(':')); t = a
    while t < b2:
        add(fx, t, np.sin(2 * np.pi * 2400 * tt(.018)) * np.exp(-tt(.018) / .005), .18); t += 1 / rate
for t in [float(x) for x in kw.get('hits', '').split(',') if x]:
    s = tt(.9); add(fx, t, sum(np.sin(2 * np.pi * mtof(m) * s) for m in (72, 76, 79, 84)) / 4 * np.exp(-s / .3) + np.sin(2 * np.pi * 50 * s) * np.exp(-s / .2), .55)
for t in [float(x) for x in kw.get('whoosh', '').split(',') if x]:
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 500, 8000) * np.sin(np.pi * x) ** 2, .22)
fade = np.ones(N); fade[:int(.02 * SR)] = np.linspace(0, 1, int(.02 * SR)); fade[-int(.6 * SR):] = np.linspace(1, .4, int(.6 * SR))
y = mix * fade + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
