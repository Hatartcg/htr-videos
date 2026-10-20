import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
import json
CU=json.load(open('/home/claude/ad1/cues.json'))
SR = 48000; DUR = CU['TOTAL']; N = int(SR * DUR); rng = np.random.default_rng(11)
VO = CU['VO']; T = {k: v + VO for k, v in CU['t'].items()}
B = 60 / 124
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


# D minor: Dm Bb F C
CH = [[62, 65, 69, 74], [58, 62, 65, 70], [60, 65, 69, 72], [60, 64, 67, 72]]
BS = [38, 34, 41, 36]
ARP = [[74, 77, 81, 86], [70, 74, 77, 82], [72, 77, 81, 84], [72, 76, 79, 84]]
add(sfx, 0.02, impact(1.2), .6); add(sfx, 0.02, pop(), .4)
add(mus, 0.05, supersaw(CH[0], T['hook'] + .4, fc=1000), .4)
def groove(t0, t1, drums=True, half=False):
    t = t0; k = 0
    while t < t1 - 1e-6:
        bar = (k // 4) % 4; beat = k % 4
        if beat == 0:
            d = min(4 * B, t1 - t); add(mus, t, supersaw(CH[bar], d, fc=3500 if half else 6000), .5)
        if drums:
            if not half or beat in (0, 2): kk(t)
            if beat in (1, 3): add(drm, t, clap(), .5)
            add(drm, t + B / 2, hat(True), .1, pan=.25)
            add(drm, t + B / 4, hat(), .05, pan=-.3); add(drm, t + 3 * B / 4, hat(), .05, pan=-.3)
        for h in range(2):
            add(mus, t + h * B / 2, bass(BS[bar], B / 2 * .9), .5)
            if (beat + h) % 2 == 0: add(mus, t + h * B / 2, pluck(ARP[bar][(beat * 2 + h) % 4]), .14, pan=(.4 if h else -.4))
        t += B; k += 1
groove(T['hook'], T['ship'], half=False)
groove(T['ship'], T['cta'] - 2 * B, half=True)
add(sfx, T['cta'] - 2 * B, riser(2 * B), .55)
for i in range(4): add(drm, T['cta'] - 2 * B + i * B / 2, clap(), .25 + .1 * i)
groove(T['cta'], DUR - 1.3)
add(mus, DUR - 1.3, supersaw([50, 57, 62, 65, 69], 1.2, fc=4000), .55); kk(DUR - 1.3)
add(sfx, T['hook'], impact(), .8)
for k_ in ['s%d' % i for i in range(5)] + ['rel', 'ship']: add(sfx, T[k_] - .12, whoosh(.25), .35)
for i in range(5): add(sfx, T['s%d' % i], pop(), .35)
for k_ in ('boxq', 'all', 'box', 'pack'): add(sfx, T[k_], impact(.8), .55)
add(sfx, T['all'] + .2, chime(86), .3); add(sfx, T['rel'] + .35, pop(), .3); add(sfx, T['rel'] + .45, pop(), .3)
add(sfx, T['ship'] + .45, pop(), .3)
add(sfx, T['cta'], impact(1.6), .9); add(sfx, T['btn'], pop(), .4); add(sfx, T['btn'] + .55, tick(1800), .5); add(sfx, T['btn'] + .6, ding(), .3)
add(sfx, T['bookw'] + .6, chime(88), .35)
sr, v = wavfile.read('voice.wav'); v = v.astype(np.float32) / 32768
if v.ndim > 1: v = v.mean(1)
voice = np.zeros(N); i0 = int(VO * SR); voice[i0:i0 + len(v)] = v[:N - i0]
venv = np.convolve(np.abs(voice), np.ones(int(.08 * SR)) / int(.08 * SR), 'same'); venv = np.clip(venv / (venv.max() + 1e-9) * 4, 0, 1)
mus *= (1 - .45 * kenv[:, None])
ir = rng.standard_normal(int(1.0 * SR)) * np.exp(-np.arange(int(1.0 * SR)) / SR / .3) * .01
for c in range(2): mus[:, c] += fftconvolve(mus[:, c], ir)[:N] * .6; sfx[:, c] += fftconvolve(sfx[:, c], ir)[:N] * .3
def norm(x): return x / (np.abs(x).max() + 1e-9)
bed = norm(mus) * .45 + norm(drm) * .55
bed *= (1 - .6 * venv[:, None])
out = bed * .8 + norm(sfx) * .5 * (1 - .4 * venv[:, None]) + norm(voice)[:, None] * 1.0
fo = int(.5 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.2) / np.tanh(1.2); out = out / np.abs(out).max() * .95
wavfile.write('mix.wav', SR, (out * 32767).astype(np.int16)); print('ok')
