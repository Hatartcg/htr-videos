import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
SR = 48000; DUR = 14.6; N = int(SR * DUR); rng = np.random.default_rng(11)
VO = 0.5; T_YGO, T_BOX, T_RC, T_24, T_CARDS, T_PRICE, T_CTA = 1.3, 2.4, 3.7, 5.04, 6.4, 8.37, 10.63
B = 60 / 150
mus = np.zeros((N, 2)); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2)); kenv = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def add(buf, t, s, g=1, pan=0):
    i = int(round(t * SR))
    if i >= N or i < 0: return
    s = s[:N - i] * g
    if s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(s, fc): b, a = butter(2, min(fc, 23000) / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def saw(f, t): return 2 * ((f * t + rng.uniform()) % 1) - 1
def kick():
    t = tt(.35); return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(48 + 160 * np.exp(-t / .025)) / SR) * np.exp(-t / .18))
def clap():
    t = tt(.3); n = bp(nz(.3), 900, 6000); e = sum(np.exp(-np.clip(t - d, 0, None) / .012) * (t >= d) for d in (0, .01, .02)) * .5 + np.exp(-t / .12) * .6
    return n * e
def hat(o=False): t = tt(.15 if o else .04); return hp(nz(len(t) / SR), 9000) * np.exp(-t / (.06 if o else .012))
def supersaw(ms, d, fc=6000):
    t = tt(d); s = np.zeros_like(t)
    for m in ms:
        for dt in (-.012, -.005, 0, .006, .013): s += saw(mtof(m) * (1 + dt), t)
    s /= (len(ms) * 5); s = lp(s, fc)
    stereo = np.stack([s, np.roll(s, 240)], 1)
    return stereo * np.minimum(1, t / .01)[:, None] * np.minimum(1, (d - t) / .05)[:, None]
def pluck(m, d=.3):
    t = tt(d); s = saw(mtof(m), t) * .6 + np.sin(2 * np.pi * mtof(m + 12) * t) * .4
    return lp(s, 3500) * np.exp(-t / .09)
def bass(m, d):
    t = tt(d); s = np.sin(2 * np.pi * mtof(m) * t) + .3 * np.tanh(3 * np.sin(2 * np.pi * mtof(m) * t))
    return s * np.minimum(1, t / .005) * np.minimum(1, (d - t) / .02)
def whoosh(d=.4):
    t = tt(d); x = t / d; n = nz(d); out = np.zeros_like(t); seg = 480
    for i in range(0, len(t), seg): fc = 400 * (7000 / 400) ** x[i]; out[i:i + seg] = bp(n[max(0, i - 400):i + seg], max(80, fc * .6), min(20000, fc * 1.6))[-len(out[i:i + seg]):]
    return out * np.sin(np.pi * x) ** 1.5 * 1.4
def riser(d): t = tt(d); x = t / d; return hp(nz(d), 2000) * x ** 2.5 * .5 + .25 * np.sin(2 * np.pi * np.cumsum(300 + 2500 * x ** 2) / SR) * x ** 2
def impact(d=1.6):
    t = tt(d); return (np.tanh(2 * np.sin(2 * np.pi * np.cumsum(35 + 110 * np.exp(-t / .05)) / SR)) * np.exp(-t / .5) + .5 * lp(nz(d), 400) * np.exp(-t / .25) + .35 * hp(nz(d), 5000) * np.exp(-t / .5))
def chime(base=84):
    out = np.zeros(int(1.2 * SR))
    for i, m in enumerate([base, base + 4, base + 7, base + 12, base + 16, base + 19]):
        t = tt(1.2 - i * .05); s = np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t / .35) + .3 * np.sin(2 * np.pi * mtof(m) * 3 * t) * np.exp(-t / .1)
        j = int(i * .05 * SR); out[j:j + len(s)] += s * .25
    return out
def pop(): t = tt(.12); return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t / .03) + 300) / SR) * np.exp(-t / .03)
def tick(f=2400): t = tt(.04); return np.sin(2 * np.pi * f * t) * np.exp(-t / .008)
def ding():
    t = tt(1.4); return sum(np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t / .5) * g for m, g in ((93, .5), (100, .35), (105, .2)))
def kk(t, g=1):
    add(drm, t, kick(), g); i = int(t * SR); L = min(int(.3 * SR), N - i)
    if L > 0: kenv[i:i + L] = np.maximum(kenv[i:i + L], np.exp(-tt(.3)[:L] / .09))

# A major royal road: D E C#m F#m
CH = [[62, 66, 69, 74], [64, 68, 71, 76], [61, 64, 68, 73], [66, 69, 73, 78]]
BS = [38, 40, 37, 42]
ARP = [[74, 78, 81, 86], [76, 80, 83, 88], [73, 76, 80, 85], [78, 81, 85, 90]]
# intro (0 - T_YGO): filtered chord swell + riser
add(sfx, 0.05, pop(), .6); add(sfx, 0.05, impact(1.0), .45)
add(mus, 0.1, supersaw(CH[0], T_YGO - .1, fc=1200), .5)
add(sfx, T_YGO - 0.8, riser(.8), .6)
# main groove from T_YGO to end, bar = 4 beats
def groove(t0, t1, drums=True):
    t = t0; k = 0
    while t < t1 - 1e-6:
        bar = (k // 4) % 4; beat = k % 4
        if beat == 0:
            d = min(4 * B, t1 - t); add(mus, t, supersaw(CH[bar], d), .55)
        if drums:
            kk(t)
            if beat in (1, 3): add(drm, t, clap(), .55)
            add(drm, t + B / 2, hat(True), .12, pan=.25)
            add(drm, t + B / 4, hat(), .06, pan=-.3); add(drm, t + 3 * B / 4, hat(), .06, pan=-.3)
        for h in range(2):
            add(mus, t + h * B / 2, bass(BS[bar], B / 2 * .9), .5)
            add(mus, t + h * B / 2, pluck(ARP[bar][(beat * 2 + h) % 4]), .16, pan=(.4 if h else -.4))
        t += B; k += 1
    return k
groove(T_YGO, T_PRICE - 2 * B)
add(sfx, T_PRICE - 2 * B, riser(2 * B), .55)
add(mus, T_PRICE - 2 * B, supersaw(CH[1], 2 * B, fc=2500), .45)
for i in range(4): add(drm, T_PRICE - 2 * B + i * B / 2, clap(), .25 + .1 * i)
groove(T_PRICE, 13.4)
# outro chord ring
add(mus, 13.4, supersaw([57, 64, 69, 73, 76], 1.2, fc=4000), .55); kk(13.4)
# SFX hits
add(sfx, T_YGO, impact(), 1.0)
for tw in (T_BOX, T_24, T_CARDS, T_CTA): add(sfx, tw - .2, whoosh(.4), .55)
add(sfx, T_BOX + .35, pop(), .35); add(sfx, T_RC, whoosh(.3), .35); add(sfx, T_RC + .12, whoosh(.3), .3, pan=.5)
last = 0
for i in range(0, 45):
    t = T_24 + i / 30; lt = t - T_24; n = max(1, min(24, int(1 + 23 * (1 - (1 - min(lt / .5, 1)) ** 3))))
    if n != last: add(sfx, t, tick(2000 + n * 40), .3); last = n
add(sfx, T_24 + .5, impact(.8), .5)
add(sfx, T_CARDS + .1, chime(84), .55); add(sfx, T_CARDS + .6, chime(91), .35)
add(sfx, T_PRICE + .03, impact(1.8), 1.0); add(sfx, T_PRICE + .05, ding(), .35)
add(sfx, T_PRICE + 1.1, pop(), .3); add(sfx, T_CTA + .45, pop(), .3); add(sfx, T_CTA + .2, chime(88), .3)
# voice
sr, v = wavfile.read('voice.wav'); v = v.astype(np.float32) / 32768
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
# mix
mus *= (1 - .45 * kenv[:, None])
ir = rng.standard_normal(int(1.0 * SR)) * np.exp(-np.arange(int(1.0 * SR)) / SR / .3) * .01
for c in range(2): mus[:, c] += fftconvolve(mus[:, c], ir)[:N] * .6; sfx[:, c] += fftconvolve(sfx[:, c], ir)[:N] * .3
def norm(x): return x / (np.abs(x).max() + 1e-9)
bed = norm(mus) * .5 + norm(drm) * .6
bed *= (1 - .5 * venv[:, None])
out = bed + norm(sfx) * .55 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.25
fo = int(.5 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.2) / np.tanh(1.2); out = out / np.abs(out).max() * .95
wavfile.write('mix.wav', SR, (out * 32767).astype(np.int16)); print('ok')
