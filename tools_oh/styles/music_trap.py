"""Dark trap bed: 808 with glides, clap on 3, 16th hats with triplet rolls, bell/pluck melody in minor, pad; holo SFX."""
import os, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
KEY = os.environ['OH']; D = f'/home/claude/work/{KEY}/'
C = {'ygo': dict(DUR=15.3, T=(1.26, 2.48, 2.94, 4.77, 5.76, 7.66, 9.64, 11.85), bpm=142, seed=8,
                 roots=[45, 41, 43, 40], bell=[[81, 84, 88, 84], [77, 81, 84, 81], [79, 83, 86, 83], [76, 79, 83, 88]], cnt=(5.76, 15))}[KEY]
SR = 48000; DUR = C['DUR']; N = int(SR * DUR); rng = np.random.default_rng(C['seed'])
VO = .5; T_GAME, T_PROD, T_NAME, T_F1, T_F2, T_F2b, T_PRICE, T_CTA = C['T']; B = 60 / C['bpm']
mus = np.zeros((N, 2)); b808 = np.zeros(N); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2)); kenv = np.zeros(N)
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
def s808(m, d, glide_to=None):
    t = tt(d); f0 = mtof(m); f = f0 * np.ones_like(t)
    if glide_to is not None: f = f0 + (mtof(glide_to) - f0) * np.clip((t - d * .6) / (d * .25), 0, 1)
    f = f * (1 + 1.5 * np.exp(-t / .012))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR); s = np.tanh(2.2 * s)
    return s * np.minimum(1, t / .003) * np.exp(-t / (d * 1.4)) * np.minimum(1, (d - t) / .02)
def kick(): t = tt(.18); return np.sin(2 * np.pi * np.cumsum(60 + 200 * np.exp(-t / .01)) / SR) * np.exp(-t / .06)
def clap():
    t = tt(.35); n = bp(nz(.35), 1000, 7000); e = sum(np.exp(-np.clip(t - d, 0, None) / .01) * (t >= d) for d in (0, .012, .024)) * .5 + np.exp(-t / .15) * .7
    return n * e
def hat(): t = tt(.035); return hp(nz(.035), 9000) * np.exp(-t / .009)
def ohat(): t = tt(.2); return hp(nz(.2), 8000) * np.exp(-t / .08)
def bell(m, d=.9):
    t = tt(d); f = mtof(m); return (np.sin(2 * np.pi * f * t + 1.8 * np.sin(2 * np.pi * f * 3.5 * t) * np.exp(-t / .2)) * np.exp(-t / .35))
def pad(ms, d):
    t = tt(d); s = sum(np.sin(2 * np.pi * mtof(m) * (1 + dt) * t) for m in ms for dt in (-.003, .003)) / (2 * len(ms))
    return lp(s, 2000) * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .3)
def riser(d): t = tt(d); x = t / d; return hp(nz(d), 1500) * x ** 3 * .6 + .3 * np.sin(2 * np.pi * np.cumsum(200 + 3000 * x ** 2) / SR) * x ** 2
def sparkle():
    out = np.zeros(int(.9 * SR))
    for i, m in enumerate([96, 100, 103, 108, 112]):
        s = np.sin(2 * np.pi * mtof(m) * tt(.6)) * np.exp(-tt(.6) / .12); j = int(i * .045 * SR); out[j:j + len(s)] += s * .3
    return out
def swish(): t = tt(.25); return bp(nz(.25), 2000, 9000) * np.sin(np.pi * t / .25) ** 2
def drop(): t = tt(1.6); return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(30 + 220 * np.exp(-t / .08)) / SR)) * np.exp(-t / .6)
def tick(f): t = tt(.04); return np.sin(2 * np.pi * f * t) * np.exp(-t / .007)
def kk(t, g=1.0):
    add(drm, t, kick(), g); i = int(t * SR); L = min(int(.2 * SR), N - i)
    if L > 0: kenv[i:i + L] = np.maximum(kenv[i:i + L], np.exp(-tt(.2)[:L] / .07))
R = C['roots']
# intro: pad + bell, no drums
add(mus, 0, pad([R[0] + 24, R[0] + 27, R[0] + 31], T_GAME), .6)
for i, m in enumerate(C['bell'][0]): add(mus, .1 + i * B / 2, bell(m), .25, pan=(-.3 if i % 2 else .3))
add(sfx, T_GAME - .9, riser(.9), .5)
def groove(t0, t1, full=True):
    t = t0; k = 0
    while t < t1 - 1e-6:
        bar = (k // 16) % 4; s16 = k % 16; root = R[bar]
        if s16 == 0: add(mus, t, pad([root + 24, root + 27, root + 31], 16 * B / 4), .45)
        if s16 % 4 == 0 or s16 % 4 == 2: add(mus, t, bell(C['bell'][bar][(s16 // 2) % 4]), .18, pan=(-.35 if s16 % 4 else .35))
        if full:
            if s16 in (0, 10): kk(t); add(b808, t, s808(root - 12, 6 * B / 4 if s16 == 0 else 6 * B / 4, glide_to=(root - 10 if s16 == 10 else None)), 1)
            if s16 == 7: kk(t, .7)
            if s16 == 8: add(drm, t, clap(), .7)
            if s16 in (12, 13) and bar % 2 == 1:  # triplet roll
                for r in range(3): add(drm, t + r * B / 6, hat(), .13, pan=.3)
            elif s16 % 2 == 0 or (bar == 3 and s16 > 11): add(drm, t, hat(), .14, pan=.3)
            if s16 == 14: add(drm, t, ohat(), .08, pan=-.3)
        t += B / 4; k += 1
groove(T_GAME, T_PRICE - 2 * B)
add(sfx, T_PRICE - 2 * B, riser(2 * B), .55)
for i in range(8): add(drm, T_PRICE - 2 * B + i * B / 4, hat(), .1 + .02 * i)
groove(T_PRICE, DUR - 1.2)
add(mus, DUR - 1.2, pad([R[0] + 24, R[0] + 28, R[0] + 31], 1.2), .6); add(b808, DUR - 1.2, s808(R[0] - 12, 1.2), 1)
# SFX
add(sfx, 0.05, sparkle(), .5); add(sfx, T_GAME, drop(), .9); add(sfx, T_GAME + .2, sparkle(), .5)
for tw in (T_PROD, T_F1, T_F2, T_CTA): add(sfx, tw - .1, swish(), .5)
add(sfx, T_PROD + .6, sparkle(), .35)
for i in range(3): add(sfx, T_F1 + .12 + i * .1, swish(), .35, pan=(i - 1) * .5)
t0, NN = C['cnt']; last = 0
for i in range(50):
    t = t0 + i / 30; lt = t - t0; n = max(1, min(NN, int(1 + (NN - 1) * (1 - (1 - min(lt / .55, 1)) ** 3))))
    if n != last: add(sfx, t, tick(1800 + n * 50), .28); last = n
for i in range(5): add(sfx, T_F2 + .15 + i * .06, swish(), .25, pan=(i - 2) * .3)
add(sfx, T_F2b, sparkle(), .6)
add(sfx, T_PRICE + .02, drop(), 1.0); add(sfx, T_PRICE + .1, sparkle(), .5); add(sfx, T_CTA + .2, sparkle(), .4)
# voice + mix
sr, v = wavfile.read(D + 'voice.wav'); v = v.astype(np.float32) / 32768
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)
ir = rng.standard_normal(int(1.2 * SR)) * np.exp(-np.arange(int(1.2 * SR)) / SR / .4) * .01
for c in range(2): mus[:, c] += fftconvolve(mus[:, c], ir)[:N] * .7; sfx[:, c] += fftconvolve(sfx[:, c], ir)[:N] * .3
bed = norm(mus) * .40 * (1 - .3 * kenv[:, None]) + norm(b808)[:, None] * .55 + norm(drm) * .5
bed *= (1 - .5 * venv[:, None])
out = bed + norm(sfx) * .5 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.3
fo = int(.4 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.15) / np.tanh(1.15); out = out / np.abs(out).max() * .95
wavfile.write(D + 'mix_trap.wav', SR, (out * 32767).astype(np.int16)); print('ok')
