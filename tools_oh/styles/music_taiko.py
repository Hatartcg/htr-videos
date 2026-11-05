"""Cinematic Japanese bed: taiko ensemble, shime/rim, low string drone, breathy shakuhachi-like flute (in-scale), brass stabs on cues."""
import os, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
C = {'suk': dict(DUR=15.1, T=(0.58, 2.5, 2.82, 4.66, 6.18, 8.02, 9.94, 11.62), bpm=104, seed=31, root=38,
                 flute=[(74, 1), (75, .5), (79, 1.5), (81, 1), (79, .5), (75, 1.5), (74, 2)], flute2=[(81, 1), (82, .5), (81, .5), (79, 1), (75, 1), (74, 2)]),
     'akaza': dict(DUR=14.2, T=(0.64, 3.14, 3.46, 7.14, 7.6, 5.14, 8.98, 10.74), bpm=116, seed=41, root=41,
                 flute=[(77, .5), (78, .5), (82, 1), (84, 1.5), (85, .5), (84, 1), (82, 1), (77, 2)], flute2=[(84, .5), (85, .5), (89, 1), (85, 1), (84, .5), (82, .5), (77, 2)])}[KEY]
SR = 48000; DUR = C['DUR']; N = int(SR * DUR); rng = np.random.default_rng(C['seed'])
VO = .5; T_GAME, T_PROD, T_NAME, T_F1, T_F1b, T_F2, T_PRICE, T_CTA = C['T']; B = 60 / C['bpm']; R0 = C['root']
mus = np.zeros((N, 2)); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2)); kenv = np.zeros(N)
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
    if s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def taiko(f=62, d=1.3):
    t = tt(d); body = np.sin(2 * np.pi * np.cumsum(f * (1 + .5 * np.exp(-t / .03))) / SR) * np.exp(-t / .45)
    skin = lp(nz(d), 700) * np.exp(-t / .05) * .7
    return np.tanh(1.8 * (body + skin))
def shime(): t = tt(.15); return (np.sin(2 * np.pi * 820 * t) * .5 + bp(nz(.15), 1500, 5000)) * np.exp(-t / .03)
def rim(): t = tt(.06); return bp(nz(.06), 2500, 8000) * np.exp(-t / .01)
def drone(m, d):
    t = tt(d); s = sum(np.sin(2 * np.pi * mtof(mm) * (1 + dt) * t + rng.uniform(0, 6)) for mm in (m, m + 7, m + 12) for dt in (-.002, .002)) / 6
    s = lp(s + .2 * np.sign(s) * np.abs(s) ** .5, 1400)
    return s * np.minimum(1, t / .8) * np.minimum(1, (d - t) / .5)
def flute(m, d):
    t = tt(d); f = mtof(m) * (1 + .012 * np.sin(2 * np.pi * 5 * t) * np.clip((t - .25) / .3, 0, 1))
    f = f * (1 - .03 * np.exp(-t / .06))  # scoop up into the note
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + .25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    breath = bp(nz(d), mtof(m) * .8, mtof(m) * 3) * .35
    e = np.minimum(1, t / .08) * np.minimum(1, (d - t) / .12) * (1 + .3 * np.exp(-t / .1))
    return (tone + breath) * e * .5
def brass(ms, d=1.0):
    t = tt(d); s = sum(2 * ((mtof(m) * (1 + dt) * t) % 1) - 1 for m in ms for dt in (-.003, .003)) / (2 * len(ms))
    fc = 400 + 2600 * np.exp(-t / .15); out = np.zeros_like(s); seg = 480
    for i in range(0, len(s), seg): out[i:i + seg] = lp(s[max(0, i - 960):i + seg], fc[i])[-len(out[i:i + seg]):]
    return out * np.minimum(1, t / .02) * np.exp(-t / .5)
def boom(d=2.2): t = tt(d); return np.tanh(2 * np.sin(2 * np.pi * np.cumsum(28 + 60 * np.exp(-t / .1)) / SR)) * np.exp(-t / .8) + .4 * lp(nz(d), 200) * np.exp(-t / .4)
def whoosh(d=.6):
    t = tt(d); x = t / d; n = nz(d); out = np.zeros_like(t); seg = 480
    for i in range(0, len(t), seg): fc = 200 * (4000 / 200) ** x[i]; out[i:i + seg] = bp(n[max(0, i - 400):i + seg], max(60, fc * .6), min(20000, fc * 1.6))[-len(out[i:i + seg]):]
    return out * np.sin(np.pi * x) ** 2
def kk(t, f=62, g=1.0, pan=0):
    add(drm, t, taiko(f), g, pan); i = int(t * SR); L = min(int(.4 * SR), N - i)
    if L > 0: kenv[i:i + L] = np.maximum(kenv[i:i + L], np.exp(-tt(.4)[:L] / .15))
# drone whole piece
add(mus, 0, drone(R0, DUR), .5)
# intro: sparse taiko + rim
kk(0.05, 55, .9); add(drm, .55, rim(), .4); add(drm, .8, rim(), .3)
for i in range(4): kk(T_GAME - .5 + i * .12, 70 + i * 4, .35 + .1 * i, pan=(-.3 if i % 2 else .3))
# main pattern (taiko in 8ths: don . don don | . don . don-don)
PAT = [(0, 60, 1), (2, 72, .6), (3, 72, .6), (5, 60, .8), (6, 80, .5), (7, 80, .55)]
def pattern(t0, t1, dense=False):
    t = t0
    while t < t1 - 1e-6:
        for s8, f, g in PAT:
            tt0 = t + s8 * B / 2
            if tt0 < t1: kk(tt0, f, g, pan=(.25 if f > 70 else -.15))
        for s in range(16 if dense else 8):
            tt0 = t + s * (B / 4 if dense else B / 2)
            if tt0 < t1: add(drm, tt0, shime() if s % 2 else rim(), .18 if s % 2 else .14, pan=.4)
        t += 4 * B
pattern(T_GAME, T_PRICE - .1)
pattern(T_PRICE, DUR - 1.3, dense=True)
kk(DUR - 1.3, 50, 1.0); add(sfx, DUR - 1.3, boom(1.3), .6)
# flute lines
t = T_GAME + .1
for m, d in C['flute']:
    add(mus, t, flute(m, d * B * .98), .55, pan=-.15); t += d * B
t = T_F2
for m, d in C['flute2']:
    if t < T_PRICE + 1.5: add(mus, t, flute(m, d * B * .98), .5, pan=.15)
    t += d * B
# brass stabs + cue SFX
add(sfx, T_GAME, boom(), 1.0); add(mus, T_GAME, brass([R0 + 12, R0 + 19, R0 + 24, R0 + 27]), .6)
for tw in (T_PROD, T_F1, T_F2, T_CTA): add(sfx, tw - .4, whoosh(.6), .45)
add(mus, T_NAME, brass([R0 + 12, R0 + 19, R0 + 24]), .35)
add(sfx, T_PRICE, boom(), 1.0); add(mus, T_PRICE, brass([R0 + 12, R0 + 17, R0 + 24, R0 + 29]), .65)
add(mus, T_CTA, brass([R0 + 12, R0 + 19, R0 + 24, R0 + 27], 1.4), .4)
# voice + mix
sr, v = wavfile.read(D + 'voice.wav'); v = v.astype(np.float32) / 32768
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)
ir = rng.standard_normal(int(2.0 * SR)) * np.exp(-np.arange(int(2.0 * SR)) / SR / .7) * .01
for c in range(2): mus[:, c] += fftconvolve(mus[:, c], ir)[:N] * .8; drm[:, c] += fftconvolve(drm[:, c], ir)[:N] * .5
bed = norm(mus) * .45 * (1 - .25 * kenv[:, None]) + norm(drm) * .62
bed *= (1 - .5 * venv[:, None])
out = bed + norm(sfx) * .45 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.3
fo = int(.6 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / np.abs(out).max() * .95
wavfile.write(D + 'mix_taiko.wav', SR, (out * 32767).astype(np.int16)); print('ok')
