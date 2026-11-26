"""dnb.py — procedural drum & bass bed (zero credits). New for HTR on 26 Nov 2026 (differs from lo-fi/phonk/darbuka/
afro-house/piano/cinematic/synth-pop/chiptune). Two-step DnB at ~172 bpm: punchy kick, crisp snare on 2 and 4, rolling
16th hats, detuned reese bass, airy minor pad; meme FX for a fast-cut reaction reel.
python3 dnb.py out.wav dur bpm seed [hits=t,..] [whoosh=t,..] [horn=t,..] [scratch=t,..] [duck=t0:t1,..] [drop=t] [intro=t]
intro = drums filtered/quiet until t (calm 1–3 s), drop = full bass from t."""
import sys, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
SR = 48000
out, DUR, BPM, SEED = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
kw = {}
for a in sys.argv[5:]:
    k, v = a.split('=', 1); kw[k] = v
rng = np.random.default_rng(SEED); N = int(DUR * SR); B = 60 / BPM
drums = np.zeros(N); bass = np.zeros(N); pad = np.zeros(N); fx = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def lp(s, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, s)
def hp(s, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def add(buf, t, s, g=1.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i]; buf[i:i + len(s)] += s * g
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def kick():
    t = tt(.28); f = 150 * np.exp(-t / .03) + 48
    return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / .14)
def snare():
    t = tt(.22); n = bp(rng.standard_normal(len(t)), 1500, 9000) * np.exp(-t / .07)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / .05)
    return (n * .9 + body * .6)
def hat(o=False):
    t = tt(.12 if o else .035); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t / (.05 if o else .01))
def saw(f, d):
    t = tt(d); return 2 * ((t * f) % 1) - 1
def reese(m, d):
    f = mtof(m); s = saw(f * .996, d) + saw(f * 1.004, d) + .5 * saw(f / 2, d)
    t = tt(d); s = lp(s, 280 + 220 * (.5 + .5 * np.sin(2 * np.pi * t * 1.3)))
    return np.tanh(1.6 * s) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .03)
def padc(ms, d):
    t = tt(d); s = sum(np.sin(2 * np.pi * mtof(m) * t + .3 * np.sin(2 * np.pi * 5 * t)) for m in ms)
    return s * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .4) / len(ms)
PROG = [(45, [57, 60, 64, 67]), (41, [53, 57, 60, 64]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67])]  # Am9 Fmaj7 C G
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; root, ch = PROG[b % 4]
    # two-step: kick 1 and 3-and, snare 2 and 4
    add(drums, t0, kick(), .9); add(drums, t0 + 2.5 * B, kick(), .8)
    if b % 2: add(drums, t0 + 3.75 * B, kick(), .45)
    add(drums, t0 + B, snare(), .7); add(drums, t0 + 3 * B, snare(), .7)
    add(drums, t0 + 1.75 * B, snare(), .18)
    for s in range(16): add(drums, t0 + s * B / 4, hat(s % 8 == 6), .22 if s % 2 else .12)
    add(bass, t0, reese(root - 12, 1.5 * B), .5); add(bass, t0 + 2.5 * B, reese(root - 12 + (3 if b % 2 else 0), 1.4 * B), .45)
    add(pad, t0, padc(ch, bar), .22)
intro = float(kw.get('intro', 0)); drop = float(kw.get('drop', 0))
gi = np.ones(N); gi[:int(intro * SR)] = .25
gb = np.ones(N); gb[:int(drop * SR)] = 0
for s in kw.get('duck', '').split(','):
    if s: a, b2 = map(float, s.split(':')); gi[int(a * SR):int(b2 * SR)] *= .4; gb[int(a * SR):int(b2 * SR)] *= .4
sm = lambda g: np.convolve(g, np.ones(960) / 960, mode='same')
if intro: drums[:int(intro * SR)] = lp(drums[:int(intro * SR)], 900)
mix = drums * sm(gi) + bass * sm(gb) + pad * sm(gi)
for t in [float(x) for x in kw.get('hits', '').split(',') if x]:
    s = tt(1.2); add(fx, t, (np.sin(2 * np.pi * 55 * s) * np.exp(-s / .35) + lp(rng.standard_normal(len(s)), 2500) * np.exp(-s / .12) * .5), .6)
for t in [float(x) for x in kw.get('whoosh', '').split(',') if x]:
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 500, 8000) * np.sin(np.pi * x) ** 2, .25)
for t in [float(x) for x in kw.get('horn', '').split(',') if x]:   # meme air-horn (3 short blasts)
    for k in range(3):
        s = tt(.16 if k < 2 else .45); f = 466 * (1 + .01 * np.sin(2 * np.pi * 30 * s))
        h = sum(saw(f * r, len(s) / SR) for r in (1, 1.25, 1.5)) / 3
        add(fx, t + k * .2, np.tanh(2 * h) * np.minimum(1, s / .01) * np.minimum(1, (len(s) / SR - s) / .02), .22)
for t in [float(x) for x in kw.get('scratch', '').split(',') if x]:  # vinyl scratch
    s = tt(.3); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 6 * s))
    add(fx, t, bp(rng.standard_normal(len(s)), 300, 3000) * np.abs(np.sin(2 * np.pi * np.cumsum(f) / SR)), .35)
fade = np.ones(N); fade[:int(.02 * SR)] = np.linspace(0, 1, int(.02 * SR)); fade[-int(.6 * SR):] = np.linspace(1, .5, int(.6 * SR))
y = mix * fade + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
