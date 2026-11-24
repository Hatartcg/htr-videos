"""darbuka.py — procedural Arabic darbuka-trap bed (zero credits). New for HTR on 24 Nov 2026 (differs from lo-fi/phonk/house/synth-pop beds).
python3 darbuka.py out.wav dur bpm seed [riser=t0:t1] [hits=t,...] [ticks=t,...] [whoosh=t,...] [drop=t] [duck=t0:t1,...]
Maqsum darbuka (doum/tek/ka), 808 sub, trap hats with rolls, hijaz-flavoured pluck riff, riser + impacts. duck = sections at low level."""
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
def doum():
    t = tt(.35); f = 95 + 60 * np.exp(-t / .02); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .16) + .2 * bp(rng.standard_normal(len(t)), 200, 900) * np.exp(-t / .02)
def tek():
    t = tt(.12); return bp(rng.standard_normal(len(t)), 2500, 9000) * np.exp(-t / .018) + .5 * np.sin(2 * np.pi * 620 * t) * np.exp(-t / .03)
def ka():
    t = tt(.08); return bp(rng.standard_normal(len(t)), 1500, 6000) * np.exp(-t / .012) * .6
def sub(m, d):
    t = tt(d); f = mtof(m) * (1 + .6 * np.exp(-t / .03)); return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-t / .9) * np.minimum(1, t / .004)
def clap():
    t = tt(.25); n = bp(rng.standard_normal(len(t)), 900, 6000)
    env = sum(np.exp(-np.maximum(0, t - o) / .012) * (t >= o) for o in (0, .011, .022)) * .5 + np.exp(-t / .09) * (t > .03)
    return n * env * .7
def hat(): t = tt(.03); return hp(rng.standard_normal(len(t)), 8000) * np.exp(-t / .008)
def pluck(m, d=.5):
    t = tt(d); f = mtof(m); s = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.3 for h in (1, 2, 3, 4, 5)) * np.exp(-t / .22)
    return lp(s * np.minimum(1, t / .002), 3800)
# hijaz on D: D Eb F# G A Bb C
HJ = [62, 63, 66, 67, 69, 70, 72, 74]
riff = [(0, 7), (.5, 6), (.75, 5), (1, 3), (1.5, 2), (2, 3), (2.5, 1), (3, 0), (3.5, 1)]
duck = []
for seg in kw.get('duck', '').split(','):
    if seg: a, b = seg.split(':'); duck.append((float(a), float(b)))
drop = float(kw.get('drop', 0))
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar
    # maqsum: D T - T D - T -  (8 eighths)
    for pos, kind in ((0, 'D'), (.5, 'T'), (1.5, 'T'), (2, 'D'), (3, 'T'), (3.75, 'k'), (2.75, 'k')):
        add(mix, t0 + pos * B, {'D': doum, 'T': tek, 'k': ka}[kind](), {'D': .55, 'T': .30, 'k': .22}[kind])
    if t0 >= drop:
        add(mix, t0, sub(38, B * 1.5), .45); add(mix, t0 + B * 2.5, sub(38, B), .35); add(mix, t0 + B * 3.25, sub(41, B * .7), .3)
        add(mix, t0 + B, clap(), .32); add(mix, t0 + 3 * B, clap(), .32)
        for s in range(16):
            if b % 2 == 1 and s >= 12:
                for r in range(3): add(mix, t0 + s * B / 4 + r * B / 12, hat(), .07)
            else:
                add(mix, t0 + s * B / 4, hat(), .06 + .02 * (s % 2 == 0))
    for pos, i in riff:
        add(mix, t0 + pos * B, pluck(HJ[i] + (12 if b % 4 == 3 else 0)), .16 if t0 >= drop else .11)
g = np.ones(N)
for a, b2 in duck:
    i0, i1 = int(a * SR), int(b2 * SR); g[i0:i1] = .45
g = np.convolve(g, np.ones(2400) / 2400, mode='same')
mix *= g
if 'riser' in kw:
    a, b2 = [float(x) for x in kw['riser'].split(':')]; d = b2 - a; s = tt(d); x = s / d
    r = bp(rng.standard_normal(len(s)), 400, 9000) * x ** 2 * .5 + np.sin(2 * np.pi * np.cumsum(200 + 1400 * x ** 2) / SR) * x ** 2 * .25
    add(fx, a, r, .5)
for t in [float(x) for x in kw.get('ticks', '').split(',') if x]:
    s = tt(.07); add(fx, t, np.sin(2 * np.pi * 1400 * s) * np.exp(-s / .015) + .5 * tek()[:len(s)], .4)
for t in [float(x) for x in kw.get('hits', '').split(',') if x]:
    s = tt(1.2); f = 50 + 120 * np.exp(-s / .04); boom = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-s / .5)
    add(fx, t, boom * .8 + bp(rng.standard_normal(len(s)), 300, 6000) * np.exp(-s / .15) * .3, .9)
for t in [float(x) for x in kw.get('whoosh', '').split(',') if x]:
    s = tt(.45); x = s / .45; add(fx, t - .4, bp(rng.standard_normal(len(s)), 500, 6000) * np.sin(np.pi * x) ** 2, .22)
fade = np.ones(N); f = int(.3 * SR); fade[:int(.02 * SR)] = np.linspace(0, 1, int(.02 * SR))
y = mix * fade + fx; y /= max(1e-6, np.abs(y).max()) / .9
wavfile.write(out, SR, np.stack([y, y], 1).astype(np.float32))
print('ok', out, DUR, BPM)
