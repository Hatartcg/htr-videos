import json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
C = json.load(open('/home/claude/dr850/cues.json')); T = C['t']
SR = 48000; DUR = C['TOTAL']; N = int(SR * DUR); rng = np.random.default_rng(21)
out = np.zeros((N, 2))
def tt(d): return np.arange(int(d * SR)) / SR
def add(t, s, g=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= N: return
    s = s[:N - i] * g
    out[i:i + len(s), 0] += s * (1 - max(0, pan)); out[i:i + len(s), 1] += s * (1 + min(0, pan))
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def lp(s, fc): b, a = butter(2, fc / (SR / 2)); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
BPM = 140; B = 60 / BPM
def kick():
    t = tt(.4); return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(45 + 140 * np.exp(-t / .03)) / SR) * np.exp(-t / .22))
def snare():
    t = tt(.25); return (bp(nz(.25), 1500, 7000) * .7 + np.sin(2 * np.pi * 190 * t) * .5) * np.exp(-t / .07)
def hat(): t = tt(.03); return hp(nz(.03), 8000) * np.exp(-t / .01)
def b808(m, d):
    t = tt(d); f = mtof(m); return np.tanh(1.8 * np.sin(2 * np.pi * f * t)) * np.exp(-t / (d * .8))
def pluck(m, d=.3):
    t = tt(d); f = mtof(m); s = sum(np.sin(2 * np.pi * f * k * t) / k for k in (1, 2, 3)) * np.exp(-t / .12); return s
# chord prog in F minor: Fm Db Ab Eb
prog = [(53, [65, 68, 72]), (49, [61, 65, 68]), (56, [63, 68, 72]), (51, [63, 67, 70])]
bar = 4 * B; nb = int(DUR / bar) + 1
for b in range(nb):
    t0 = b * bar; root, ch = prog[b % 4]
    for s in range(16):
        ts = t0 + s * B / 4
        if s in (0, 7, 10) or (b % 2 and s == 14): add(ts, kick(), .9)
        if s in (4, 12): add(ts, snare(), .45)
        add(ts, hat(), .16 if s % 2 else .24, .3 if s % 4 else -.3)
        if b % 2 and s >= 13: add(ts + B / 8, hat(), .15)
    add(t0, b808(root - 12, bar * .55), .5); add(t0 + 2.5 * B, b808(root - 12, bar * .3), .4)
    for k, s in enumerate((0, 3, 6, 8, 11, 14)):
        add(t0 + s * B / 4, pluck(ch[k % 3] + 12), .11, (-.4, .4)[k % 2])
# impacts and whooshes on cues
def impact():
    t = tt(1.0); return (np.sin(2 * np.pi * np.cumsum(30 + 60 * np.exp(-t / .05)) / SR) * np.exp(-t / .35) + lp(nz(1.0), 400) * np.exp(-t / .2) * .5)
def whoosh(d=.5):
    t = tt(d); n = nz(d); e = np.sin(np.pi * t / d) ** 2
    return bp(n, 600, 5000) * e
def chime():
    t = tt(1.2); return sum(np.sin(2 * np.pi * mtof(m) * t) for m in (84, 88, 91)) * np.exp(-t / .4) / 3
add(0, impact(), .8)
for k in ('box', 'hr', 'sir', 'case', 'cta'):
    add(T[k] - .45, whoosh(), .35); add(T[k], impact(), .55)
for k in ('packs', 'save', 'door'): add(T[k], chime(), .25)
# fade end
fo = int(1.2 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out /= np.max(np.abs(out)) + 1e-9
wavfile.write('/home/claude/dr850/music.wav', SR, (out * .9 * 32767).astype(np.int16))
