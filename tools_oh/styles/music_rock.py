"""Anime-opening style rock bed: distorted power-chord guitars, bass, live-ish drums, lead hook, manga SFX. Ducked under the voice."""
import os, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
C = {
 # roots as midi (low E=40). prog = list of (root, bars) ; pattern: 'chug' 8ths, 'gallop' 8th+two16ths
 'op14': dict(DUR=13.9, T=(1.26, 2.18, 3.54, 5.26, 6.74, 8.78, 10.34), bpm=172, seed=12, prog=[40, 36, 38, 35], pat='chug',
              lead=[76, 74, 71, 74, 76, 79, 78, 74], cnt=[(5.26, 24), (6.74, 12)]),
 'st24': dict(DUR=14.6, T=(1.14, 2.75, 3.9, 5.1, 7.38, 8.95, 11.1), bpm=158, seed=24, prog=[45, 41, 43, 40], pat='gallop',
              lead=[81, 79, 76, 79, 81, 84, 83, 79], cnt=[(5.1, 51)]),
}[KEY]
SR = 48000; DUR = C['DUR']; N = int(SR * DUR); rng = np.random.default_rng(C['seed'])
VO = 0.5; T_GAME, T_PROD, T_NAME, T_F1, T_F2, T_PRICE, T_CTA = C['T']
B = 60 / C['bpm']
gtr = np.zeros((N, 2)); bas = np.zeros(N); drm = np.zeros((N, 2)); lead = np.zeros(N); sfx = np.zeros((N, 2)); kenv = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(s, fc, o=2): b, a = butter(o, min(fc, 23000) / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc, o=2): b, a = butter(o, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def add(buf, t, s, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf) or i < 0: return
    s = s[:len(buf) - i] * g
    if buf.ndim == 1: buf[i:i + len(s)] += s if s.ndim == 1 else s.mean(1)
    elif s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def saw(f, t, ph=0): return 2 * ((f * t + ph) % 1) - 1
def dist(x, g=9): return np.tanh(g * x) / np.tanh(g)
def cab(x): return lp(hp(x, 90), 4800, 4) + .35 * bp(x, 1500, 3200)
def power(root, d, mute=False):
    t = tt(d); s = np.zeros_like(t)
    for m, g in ((root, 1), (root + 7, .8), (root + 12, .6)):
        for dt in (-.004, .004): s += saw(mtof(m) * (1 + dt), t, rng.uniform()) * g
    s /= 4.8
    e = np.exp(-t / (.07 if mute else 1.2)) * np.minimum(1, t / .003) * np.minimum(1, (d - t) / .015)
    y = cab(dist(s * (1.0 if not mute else .8), 10)) * e
    if mute: y = lp(y, 1800)
    L = y; R = np.roll(y, int(.011 * SR))  # double-tracked width
    return np.stack([L, R], 1)
def bassn(m, d):
    t = tt(d); s = .8 * np.sin(2 * np.pi * mtof(m) * t) + .35 * dist(saw(mtof(m), t), 3)
    return lp(s, 900) * np.minimum(1, t / .004) * np.minimum(1, (d - t) / .02)
def kick():
    t = tt(.3); return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(50 + 140 * np.exp(-t / .02)) / SR) * np.exp(-t / .14)) + .3 * hp(nz(.3), 3000) * np.exp(-t / .004)
def snare():
    t = tt(.35); return .55 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / .05) + .8 * bp(nz(.35), 1500, 9000) * np.exp(-t / .13)
def hat(o=False): t = tt(.18 if o else .05); return hp(nz(len(t) / SR), 8000) * np.exp(-t / (.07 if o else .013))
def crash(): t = tt(2.0); return hp(nz(2.0), 4500) * np.exp(-t / .7) * .7
def tom(f): t = tt(.35); return np.sin(2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-t / .03))) / SR) * np.exp(-t / .2)
def leadn(m, d):
    t = tt(d); f = mtof(m) * (1 + .007 * np.sin(2 * np.pi * 6 * t) * np.minimum(1, t / .15))
    ph = np.cumsum(f) / SR; s = dist(.6 * np.sign(np.sin(2 * np.pi * ph)) * .5 + .5 * (2 * (ph % 1) - 1), 4)
    return lp(s, 3500) * np.minimum(1, t / .01) * np.minimum(1, (d - t) / .05) * .6
def whoosh(d=.35):
    t = tt(d); x = t / d; n = nz(d); out = np.zeros_like(t); seg = 480
    for i in range(0, len(t), seg): fc = 300 * (6000 / 300) ** x[i]; out[i:i + seg] = bp(n[max(0, i - 400):i + seg], max(80, fc * .6), min(20000, fc * 1.6))[-len(out[i:i + seg]):]
    return out * np.sin(np.pi * x) ** 1.5 * 1.3
def impact(d=1.4):
    t = tt(d); return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(32 + 120 * np.exp(-t / .04)) / SR)) * np.exp(-t / .45) + .6 * lp(nz(d), 300) * np.exp(-t / .2)
def page():  # paper flip / ink swipe
    t = tt(.28); return bp(nz(.28), 900, 7000) * (np.exp(-((t - .06) / .04) ** 2) + .6 * np.exp(-((t - .17) / .05) ** 2))
def stamp(): t = tt(.25); return lp(nz(.25), 1200) * np.exp(-t / .03) + .8 * np.sin(2 * np.pi * 80 * t) * np.exp(-t / .06)
def tick(f=2600): t = tt(.04); return np.sin(2 * np.pi * f * t) * np.exp(-t / .007)
def kk(t, g=1.0):
    add(drm, t, kick(), g); i = int(t * SR); L = min(int(.25 * SR), N - i)
    if L > 0: kenv[i:i + L] = np.maximum(kenv[i:i + L], np.exp(-tt(.25)[:L] / .08))

PROG = C['prog']
# intro: ringing chord + tom fill into the hook
add(sfx, 0.04, stamp(), .9); add(gtr, 0.05, power(PROG[0], T_GAME - .1) * np.linspace(.15, .7, int((T_GAME - .1) * SR))[:, None], .7)
nf = 6
for i in range(nf): add(drm, T_GAME - nf * B / 2 + i * B / 2, tom(140 - i * 12), .55, pan=(-.4 + .16 * i))
def section(t0, t1, full=True, half=False):
    t = t0; k = 0
    while t < t1 - 1e-6:
        bar = (k // 8) % len(PROG); e8 = k % 8; root = PROG[bar]
        if e8 == 0 and full: add(drm, t, crash(), .45 if k % 16 == 0 else .0)
        if C['pat'] == 'chug' or e8 % 2 == 0:
            add(gtr, t, power(root, B / 2 * .95, mute=(e8 not in (0, 3, 6))), .55 if e8 in (0, 3, 6) else .42)
        add(bas, t, bassn(root - 12, B / 2 * .9), .55)
        if full:
            if half:
                if e8 == 0: kk(t)
                if e8 == 4: add(drm, t, snare(), .7)
            else:
                if e8 in (0, 3, 4 if False else 5): kk(t, .95)
                if e8 in (2, 6): add(drm, t, snare(), .7)
            add(drm, t, hat(e8 % 2 == 1), .12, pan=.3)
        t += B / 2; k += 1
section(T_GAME, T_PRICE - B * 2)
# build into price: snare roll + riser chord
for i in range(8): add(drm, T_PRICE - B * 2 + i * B / 4, snare(), .3 + .07 * i)
add(gtr, T_PRICE - B * 2, power(PROG[1], B * 2), .5)
section(T_PRICE, DUR - 1.3)
add(gtr, DUR - 1.3, power(PROG[0], 1.3), .7); add(drm, DUR - 1.3, crash(), .6); kk(DUR - 1.3)
# lead hook over hook section and price section
for t0 in (T_GAME + 8 * B / 2 * 0, T_PRICE):
    for i, m in enumerate(C['lead']):
        add(lead, t0 + i * B, leadn(m, B * .95), 1.0)
# SFX on cues
add(sfx, T_GAME, impact(), 1.0); add(drm, T_GAME, crash(), .7)
for tw in (T_PROD, T_F1, T_F2, T_PRICE, T_CTA): add(sfx, tw - .14, page(), .7); add(sfx, tw - .2, whoosh(.3), .4)
add(sfx, T_NAME, stamp(), .6); add(sfx, T_NAME + .15, stamp(), .4)
for t0, NN in C['cnt']:
    last = 0
    for i in range(45):
        t = t0 + i / 30; lt = t - t0; n = max(1, min(NN, int(1 + (NN - 1) * (1 - (1 - min(lt / .5, 1)) ** 3))))
        if n != last: add(sfx, t, tick(2000 + n * 40), .3); last = n
    add(sfx, t0 + .5, stamp(), .7)
add(sfx, T_PRICE + .02, impact(1.6), 1.0); add(sfx, T_PRICE + .2, stamp(), .6); add(sfx, T_PRICE + .95, stamp(), .4)
add(sfx, T_CTA + .15, stamp(), .5); add(sfx, T_CTA + .4, stamp(), .4)
# voice
sr, v = wavfile.read(D + 'voice.wav'); v = v.astype(np.float32) / 32768
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)
ir = rng.standard_normal(int(.8 * SR)) * np.exp(-np.arange(int(.8 * SR)) / SR / .25) * .01
for c in range(2): drm[:, c] += fftconvolve(drm[:, c], ir)[:N] * .4
leadst = np.stack([lead, np.roll(lead, int(.02 * SR))], 1); leadst += np.stack([fftconvolve(lead, ir)[:N]] * 2, 1) * .8
g = norm(gtr) * (1 - .25 * kenv[:, None])
bed = g * .42 + norm(bas)[:, None] * .38 + norm(drm) * .62 + norm(leadst) * .22
bed *= (1 - .55 * venv[:, None])
out = bed + norm(sfx) * .5 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.3
fo = int(.4 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.15) / np.tanh(1.15); out = out / np.abs(out).max() * .95
wavfile.write(D + 'mix_rock.wav', SR, (out * 32767).astype(np.int16)); print('ok')
