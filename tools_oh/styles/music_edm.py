"""EDM / future-rave bed: four-on-floor, sidechain-pumped supersaw chords, offbeat sub bass, arp plucks, build + drop on price, UI blips."""
import os, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
C = {'sl': dict(DUR=14.4, T=(1.3, 2.62, 3.3, 4.98, 5.7, 6.46, 8.58, 10.82), bpm=128, seed=17,
                CH=[[59, 62, 66], [55, 59, 62], [62, 66, 69], [57, 61, 64]], BS=[35, 31, 38, 33])}[KEY]
SR = 48000; DUR = C['DUR']; N = int(SR * DUR); rng = np.random.default_rng(C['seed'])
VO = .5; T_GAME, T_PROD, T_NAME, T_F1, T_F1b, T_F2, T_PRICE, T_CTA = C['T']; B = 60 / C['bpm']
syn = np.zeros((N, 2)); sub = np.zeros(N); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2)); pump = np.ones(N)
def tt(d): return np.arange(int(d * SR)) / SR
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(s, fc): b, a = butter(2, min(fc, 23000) / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def add(buf, t, s, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= len(buf) or i < 0: return
    s = s[:len(buf) - i] * g
    if buf.ndim == 1: buf[i:i + len(s)] += s if s.ndim == 1 else s.mean(1)
    elif s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def saw(f, t): return 2 * ((f * t + rng.uniform()) % 1) - 1
def supersaw(ms, d, fc=7000):
    t = tt(d); L = np.zeros_like(t); R = np.zeros_like(t)
    for m in ms + [ms[0] + 12]:
        for i, dt in enumerate((-.015, -.007, 0, .007, .015)):
            s = saw(mtof(m) * (1 + dt), t); (L if i % 2 else R)[:] += s; (R if i % 2 else L)[:] += s * .5
    L, R = lp(L, fc), lp(R, fc); n = len(ms) * 7.5
    e = np.minimum(1, t / .01) * np.minimum(1, (d - t) / .03)
    return np.stack([L, R], 1) / n * e[:, None]
def pluck(m, d=.22): t = tt(d); return lp(saw(mtof(m), t) + saw(mtof(m) * 1.005, t), 5000) * np.exp(-t / .07) * .5
def subn(m, d): t = tt(d); return np.sin(2 * np.pi * mtof(m) * t) * np.minimum(1, t / .005) * np.minimum(1, (d - t) / .02)
def kick(): t = tt(.3); return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(48 + 180 * np.exp(-t / .015)) / SR) * np.exp(-t / .16))
def clap():
    t = tt(.3); n = bp(nz(.3), 1100, 8000); e = sum(np.exp(-np.clip(t - d, 0, None) / .01) * (t >= d) for d in (0, .01, .02)) * .5 + np.exp(-t / .12) * .7
    return n * e
def hat(o=False): t = tt(.12 if o else .04); return hp(nz(len(t) / SR), 9000) * np.exp(-t / (.05 if o else .01))
def riser(d): t = tt(d); x = t / d; return hp(nz(d), 2500) * x ** 2 * .6 + .3 * saw(200 + 1800 * x ** 2, t) * x ** 3 * .3
def blip(f=1600, d=.08): t = tt(d); return np.sign(np.sin(2 * np.pi * f * t)) * np.exp(-t / .02) * .4
def lvlup():
    out = np.zeros(int(1.0 * SR))
    for i, m in enumerate([71, 74, 78, 83, 86, 90]):
        s = pluck(m, .4); j = int(i * .06 * SR); out[j:j + len(s)] += s
    return out
def glitchn(): t = tt(.18); return (np.sign(np.sin(2 * np.pi * 220 * t * (1 + 6 * t))) * .4 + bp(nz(.18), 2000, 8000) * .6) * np.exp(-t / .07)
def impact(d=1.4): t = tt(d); return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(30 + 140 * np.exp(-t / .04)) / SR)) * np.exp(-t / .5) + .5 * hp(nz(d), 4000) * np.exp(-t / .4)
def kk(t):
    add(drm, t, kick(), 1); i = int(t * SR); L = min(int(B * SR), N - i)
    if L > 0: pump[i:i + L] = np.minimum(pump[i:i + L], 1 - .75 * np.exp(-tt(L / SR) / (B * .28)))
CH, BS = C['CH'], C['BS']
# intro: filtered chords + arp, no kick
add(syn, 0, supersaw(CH[0], T_GAME, fc=900), .5)
for i in range(int(T_GAME / (B / 2))): add(syn, i * B / 2, pluck(CH[0][i % 3] + 12), .3, pan=(.3 if i % 2 else -.3))
add(sfx, T_GAME - .8, riser(.8), .5)
def groove(t0, t1, fc=7000, drop=False):
    t = t0; k = 0
    while t < t1 - 1e-6:
        bar = (k // 4) % 4; beat = k % 4
        if beat == 0: add(syn, t, supersaw(CH[bar], min(4 * B, t1 - t), fc=fc), .55)
        kk(t)
        if beat in (1, 3): add(drm, t, clap(), .55)
        add(drm, t + B / 2, hat(True), .14, pan=.25); add(drm, t + B / 4, hat(), .07, pan=-.3); add(drm, t + 3 * B / 4, hat(), .07, pan=-.3)
        add(sub, t + B / 2, subn(BS[bar], B / 2 * .9), 1.0)
        for h in range(4 if drop else 2):
            add(syn, t + h * B / (4 if drop else 2), pluck(CH[bar][(beat + h) % 3] + 24), .22, pan=(.4 if h % 2 else -.4))
        t += B; k += 1
groove(T_GAME, T_PRICE - 2 * B, fc=4500)
add(sfx, T_PRICE - 2 * B, riser(2 * B), .7)
for i in range(8): add(drm, T_PRICE - 2 * B + i * B / 4, clap(), .2 + .06 * i)
groove(T_PRICE, DUR - 1.1, fc=9000, drop=True)
add(syn, DUR - 1.1, supersaw(CH[0], 1.1, fc=5000), .6); kk(DUR - 1.1)
# SFX
add(sfx, .05, blip(1200), .5); add(sfx, .15, blip(1800), .4)
for tc in (VO, T_PROD, T_F1, T_PRICE): add(sfx, tc, blip(1500), .45); add(sfx, tc + .06, blip(2200), .35)
for tc in (T_GAME, T_PROD, T_F1, T_PRICE, T_CTA): add(sfx, tc - .06, glitchn(), .55)
add(sfx, T_PROD + .3, lvlup(), .7); add(sfx, T_GAME, impact(), .9); add(sfx, T_PRICE, impact(1.6), 1.0)
for tc in (T_F1, T_F1b): add(sfx, tc + .15, blip(900, .3), .25)
for i in range(2): add(sfx, T_F2 + i * .55 + .25, blip(2600), .4)
add(sfx, T_CTA + .2, lvlup(), .5)
# voice + mix
sr, v = wavfile.read(D + 'voice.wav'); v = v.astype(np.float32) / 32768
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)
ir = rng.standard_normal(int(1.0 * SR)) * np.exp(-np.arange(int(1.0 * SR)) / SR / .3) * .01
for c in range(2): syn[:, c] += fftconvolve(syn[:, c], ir)[:N] * .6
bed = norm(syn) * .45 * pump[:, None] + norm(sub * pump)[:, None] * .45 + norm(drm) * .55
bed *= (1 - .5 * venv[:, None])
out = bed + norm(sfx) * .5 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.3
fo = int(.4 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.15) / np.tanh(1.15); out = out / np.abs(out).max() * .95
wavfile.write(D + 'mix_edm.wav', SR, (out * 32767).astype(np.int16)); print('ok')
