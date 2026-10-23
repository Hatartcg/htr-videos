"""Per-format music + SFX + voice mix.  STYLE=swing|news|chip|lounge|cine  KEY=semitones  python3 music2.py
reads cues.json {total, events:[[name,t]], offs:[...]} and vo.wav (already placed); writes mix.wav"""
import numpy as np, json, os
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
CU = json.load(open('cues.json')); SR = 48000; DUR = CU['total']; N = int(SR * DUR) + SR
rng = np.random.default_rng(int(os.environ.get('SEED', '7')))
STYLE = os.environ.get('STYLE', 'swing'); KEY = int(os.environ.get('KEY', '0'))
mus = np.zeros((N, 2)); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2))
def tt(d): return np.arange(int(d * SR)) / SR
def add(buf, t, s, g=1, pan=0):
    i = int(round(t * SR))
    if i >= N or i < 0 or len(s) == 0: return
    s = s[:N - i] * g
    if s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(s, fc): b, a = butter(2, min(fc, 23000) / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def saw(f, t): return 2 * ((f * t + rng.uniform()) % 1) - 1
def sq(f, t, duty=.5): return np.where(((f * t) % 1) < duty, 1.0, -1.0)
def tri(f, t): return 2 * np.abs(2 * ((f * t) % 1) - 1) - 1
def adsr(t, a, d_, s_, r_, D):
    e = np.where(t < a, t / max(a, 1e-4), s_ + (1 - s_) * np.exp(-(t - a) / max(d_, 1e-4)))
    return e * np.clip((D - t) / max(r_, 1e-4), 0, 1)
def kick(g=1):
    t = tt(.4); return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(45 + 150 * np.exp(-t / .03)) / SR) * np.exp(-t / .2)) * g
def snare(): t = tt(.25); return bp(nz(.25), 1500, 8000) * np.exp(-t / .07) * .8 + np.sin(2 * np.pi * 185 * t) * np.exp(-t / .05) * .6
def hat(o=False): t = tt(.18 if o else .05); return hp(nz(len(t) / SR), 8000) * np.exp(-t / (.07 if o else .014))
def ride():
    t = tt(.5); return hp(nz(.5), 5000) * np.exp(-t / .2) * .5 + sum(np.sin(2 * np.pi * f * t) for f in (3200, 4570, 5900)) * np.exp(-t / .3) * .05
def whoosh(d=.45):
    t = tt(d); x = t / d; n = nz(d); out = np.zeros_like(t); seg = 480
    for i in range(0, len(t), seg): fc = 300 * (7000 / 300) ** x[i]; out[i:i + seg] = bp(n[max(0, i - 400):i + seg], max(80, fc * .6), min(20000, fc * 1.6))[-len(out[i:i + seg]):]
    return out * np.sin(np.pi * x) ** 1.5 * 1.4
def impact(d=1.6, f0=35):
    t = tt(d); return (np.tanh(2 * np.sin(2 * np.pi * np.cumsum(f0 + 110 * np.exp(-t / .05)) / SR)) * np.exp(-t / .5) + .5 * lp(nz(d), 400) * np.exp(-t / .25) + .3 * hp(nz(d), 5000) * np.exp(-t / .4))
def bell(m, d=1.5, g=1):
    t = tt(d); f = mtof(m); return g * (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / .2) + .3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / .08)) * np.exp(-t / .6)
def reverb(x, sec=1.6, wet=.25):
    ir = rng.standard_normal(int(sec * SR)) * np.exp(-np.arange(int(sec * SR)) / SR / (sec / 5)); ir /= np.abs(ir).sum() ** .5 * 6
    out = x.copy()
    for c in range(2): out[:, c] = x[:, c] + wet * fftconvolve(x[:, c], ir)[:len(x)]
    return out
K = KEY
# ------------------------------------------------------------------ styles
def style_swing():
    B = 60 / 148; sw = .66
    prog = [(50, [62, 65, 69, 72]), (55, [62, 65, 67, 71]), (48, [60, 64, 67, 71]), (57, [61, 64, 67, 70])]
    t = 0; k = 0
    while t < DUR:
        bar = (k // 4) % 4; beat = k % 4; root, ch = prog[bar]
        walk = [root, root + 4, root + 7, root + 9][beat] + K - 12
        tb = tt(B * .95); add(mus, t, (np.sin(2 * np.pi * mtof(walk) * tb) + .4 * np.sin(4 * np.pi * mtof(walk) * tb)) * np.exp(-tb / .35), .32)
        add(drm, t, ride(), .22, .3); add(drm, t + B * sw, ride(), .12, .3)
        if beat in (1, 3): add(drm, t, bp(nz(.2), 900, 6000) * np.exp(-tt(.2) / .06), .18)   # brush
        if beat == 0: add(drm, t, kick(.6), 1)
        if beat in (1, 3) and k % 8 in (1, 3, 5):
            d = .22; tb = tt(d); st = sum(lp(saw(mtof(m + K), tb), 2600) for m in ch) / 4 * adsr(tb, .01, .06, .4, .05, d)
            add(mus, t + B * sw, st, .2, -.2)
        t += B; k += 1
def style_news():
    B = 60 / 122; ch = [[57, 60, 64], [53, 57, 60], [55, 58, 62], [52, 55, 59]]
    t = 0; k = 0
    while t < DUR:
        bar = (k // 4) % 4; beat = k % 4
        for j in range(4):
            m = ch[bar][(j + beat) % 3] + 12 + K; tb = tt(B / 4 * .8)
            add(mus, t + j * B / 4, lp(saw(mtof(m), tb), 2200) * np.exp(-tb / .05), .1, .25 if j % 2 else -.25)
            add(drm, t + j * B / 4, hat(), .07 if j % 2 else .04)
        tb = tt(B * .9); add(mus, t, np.sin(2 * np.pi * mtof(ch[bar][0] - 24 + K) * tb) * np.exp(-tb / .3), .45)
        if beat in (0, 2): add(drm, t, kick(.8), 1)
        if beat == 3: add(drm, t, snare(), .2)
        t += B; k += 1
def style_chip():
    B = 60 / 160; prog = [57, 53, 55, 52]; arp = [0, 3, 7, 12, 7, 3]
    t = 0; k = 0
    while t < DUR:
        bar = (k // 4) % 4; beat = k % 4; r = prog[bar] + K
        for j in range(2):
            m = r + 12 + arp[(k * 2 + j) % 6]; tb = tt(B / 2 * .9); add(mus, t + j * B / 2, sq(mtof(m), tb, .25) * np.exp(-tb / .12), .07, -.2 + .4 * j)
        tb = tt(B * .9); add(mus, t, tri(mtof(r - 12), tb) * np.minimum(1, (B * .9 - tb) / .02), .28)
        if k % 8 == 0:
            tb = tt(B * 4); mel = [r + 24, r + 27, r + 31, r + 29]
            for j, m in enumerate(mel): tq = tt(B * .9); add(mus, t + j * B, sq(mtof(m), tq, .5) * adsr(tq, .005, .1, .5, .05, B * .9), .05, .2)
        if beat in (0, 2): add(drm, t, kick(.7), 1)
        if beat in (1, 3): add(drm, t, hp(nz(.12), 2000) * np.exp(-tt(.12) / .04), .25)
        add(drm, t + B / 2, hp(nz(.03), 7000) * np.exp(-tt(.03) / .01), .1)
        t += B; k += 1
def style_lounge():
    B = 60 / 100; prog = [[62, 65, 69, 72], [55, 59, 62, 65], [60, 64, 67, 71], [57, 60, 64, 67]]; roots = [38, 43, 36, 45]
    t = 0; k = 0
    while t < DUR:
        bar = (k // 4) % 4; beat = k % 4
        if beat in (0, 2):
            d = B * 1.8; tb = tt(d); s = sum(np.sin(2 * np.pi * mtof(m + K) * tb) + .3 * np.sin(4 * np.pi * mtof(m + K) * tb) * np.exp(-tb / .3) for m in prog[bar]) / 4
            add(mus, t + (B * .5 if beat == 2 else 0), s * (1 + .25 * np.sin(2 * np.pi * 5 * tb)) * adsr(tb, .01, .5, .5, .3, d), .16, .15)
        r = roots[bar] + K; pat = [(0, r), (1.5, r + 7), (2, r + 12), (3.5, r + 7)]
        if beat == 0:
            for off, m in pat: tb = tt(B * .6); add(mus, t + off * B, np.sin(2 * np.pi * mtof(m) * tb) * np.exp(-tb / .25), .3)
        add(drm, t, hp(nz(.06), 6000) * np.exp(-tt(.06) / .02), .06); add(drm, t + B / 2, hp(nz(.06), 6000) * np.exp(-tt(.06) / .02), .09)
        if beat in (1, 3): add(drm, t + (B * .5 if beat == 3 else 0), bp(nz(.05), 1500, 4000) * np.exp(-tt(.05) / .01), .2)
        if beat == 0: add(drm, t, kick(.45), 1)
        t += B; k += 1
def style_cine():
    d = DUR; tb = tt(d)
    for m, g in ((38, .25), (45, .18), (50, .12), (57, .06)):
        s = sum(saw(mtof(m + K) * (1 + dt), tb) for dt in (-.004, 0, .005)) / 3
        add(mus, 0, lp(s, 650) * (.75 + .25 * np.sin(tb * .3 + m)) * np.minimum(1, tb / 2) * g)
    notes = [74, 72, 69, 67, 69, 72, 76, 74]; t = 1.0; j = 0
    while t < DUR - 2:
        m = notes[j % len(notes)] + K; tq = tt(2.5); s = (np.sin(2 * np.pi * mtof(m) * tq) + .4 * np.sin(4 * np.pi * mtof(m) * tq) * np.exp(-tq / .4)) * np.exp(-tq / .9)
        add(mus, t, s, .12, .2 if j % 2 else -.2); t += 1.6 if j % 4 != 3 else 2.4; j += 1
    t = 0.5
    while t < DUR:      # heartbeat
        add(drm, t, kick(.5), 1); add(drm, t + .22, kick(.35), 1); t += 1.05
STYLES = dict(swing=style_swing, news=style_news, chip=style_chip, lounge=style_lounge, cine=style_cine)
STYLES[STYLE]()
# ------------------------------------------------------------------ SFX by event
def ev(name, t):
    if name in ('swipe', 'spin', 'ride', 'slam_pre'): add(sfx, t, whoosh(.45), .45)
    elif name == 'fanfare':
        for j, m in enumerate([67, 72, 76, 79, 84]):
            tb = tt(.5 if j < 4 else 1.4); add(sfx, t + j * .11, lp(sum(saw(mtof(m + K + o), tb) for o in (0, .1)), 3000) * adsr(tb, .01, .2, .6, .2, len(tb) / SR), .12)
    elif name == 'count':
        for j in range(3): add(sfx, t + j, bell(93 if j < 2 else 98, .4), .25); add(drm, t + j, kick(.4), 1)
    elif name == 'correct':
        add(sfx, t, bell(88, 1.2), .35); add(sfx, t + .12, bell(95, 1.2), .35)
        tb = tt(2.4); add(sfx, t + .1, bp(nz(2.4), 800, 5000) * adsr(tb, .15, .5, .6, .8, 2.4) * (1 + .5 * np.sin(2 * np.pi * 11 * tb)), .22)   # applause
    elif name == 'news':
        add(sfx, t, impact(1.6), .7)
        for j, m in enumerate([57, 64, 69]): tb = tt(1.2); add(sfx, t + .02, lp(saw(mtof(m + K), tb), 2500) * np.exp(-tb / .5), .14)
    elif name == 'tick':
        tb = tt(.5); add(sfx, t, (np.sin(2 * np.pi * 1800 * tb) + np.sin(2 * np.pi * 2400 * tb)) * np.exp(-tb / .08) * .5 + hp(nz(.5), 5000) * np.exp(-tb / .05) * .4, .35)
    elif name == 'bell':
        for j in range(4): add(sfx, t + j * .18, bell(84, 1.0), .3)
    elif name == 'roundbell': add(sfx, t, bell(79, 1.4), .45)
    elif name == 'fight': add(sfx, t, impact(1.0, 50), .6)
    elif name == 'slam': add(sfx, t, impact(.8, 60), .5); add(sfx, t - .25, whoosh(.25), .4)
    elif name == 'ko':
        add(sfx, t, impact(2.0, 30), .95)
        tb = tt(.9); add(sfx, t + .05, sq(mtof(84) * np.exp(-tb * 2.2), tb, .5) * np.exp(-tb / .4), .08)
    elif name == 'ding': add(sfx, t, bell(88, 1.2), .3); add(sfx, t + .35, bell(84, 1.4), .3)
    elif name == 'doors':
        tb = tt(.5); add(sfx, t, bp(nz(.5), 300, 2500) * np.sin(np.pi * tb / .5), .18)
    elif name == 'big':
        add(sfx, t, impact(2.0), .9)
        tb = tt(3.0); s = sum(saw(mtof(m + K) * (1 + dt), tb) for m in (50, 57, 62, 66, 69) for dt in (-.006, .006)) / 10
        add(sfx, t, lp(s, 3000) * adsr(tb, .05, 1, .5, 1, 3.0), .35)
    elif name == 'braam':
        tb = tt(2.6); s = np.tanh(3 * sum(saw(mtof(m + K) * (1 + dt), tb) for m in (26, 33, 38) for dt in (-.01, 0, .01)) / 9)
        add(sfx, t, lp(s, 900) * adsr(tb, .03, .8, .4, 1.2, 2.6), .55); add(sfx, t, impact(1.6, 30), .5)
    elif name == 'hit':
        tb = tt(.7); add(sfx, t, impact(1.0, 40), .45); add(sfx, t - .45, whoosh(.45)[::-1] if False else whoosh(.45), .25)
    elif name == 'cash':
        for j, m in enumerate([96, 100, 103]): add(sfx, t + j * .07, bell(m, .6), .18)
for name, t in CU.get('events', []): ev(name, t)
add(sfx, CU['end'], impact(1.5), .6)
# ------------------------------------------------------------------ mix
mus = reverb(mus, 1.8 if STYLE == 'cine' else 1.0, .35 if STYLE in ('cine', 'lounge') else .15)
sfx = reverb(sfx, 1.2, .15)
vs, vv = wavfile.read('vo.wav'); vv = vv.astype(np.float32) / 32768
if vv.ndim > 1: vv = vv.mean(1)
voice = np.zeros(N); voice[:min(N, len(vv))] = vv[:N]
venv = np.convolve(np.abs(voice), np.ones(int(.1 * SR)) / int(.1 * SR), 'same'); venv = np.clip(venv / (np.percentile(venv, 95) + 1e-9) * 2, 0, 1)
def norm(x): return x / (np.abs(x).max() + 1e-9)
out = (norm(mus) * .5 + norm(drm) * .45) * (1 - .62 * venv[:, None]) * .55 + norm(sfx) * .5 * (1 - .3 * venv[:, None]) + voice[:, None] * 1.0
out = out[:int(DUR * SR)]
fo = int(.5 * SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
out = np.tanh(out * 1.3) / np.tanh(1.3); out = out / np.abs(out).max() * .95
wavfile.write('mix.wav', SR, (out * 32767).astype(np.int16)); print('mix ok', STYLE)
