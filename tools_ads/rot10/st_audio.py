# rot10 store tour — mix: bright future-house 124 BPM (new style for this series): 4-on-floor, offbeat hats, plucky chord stabs,
# sidechained bass; whooshes on every page swipe; voice lines + approved bank clips (هتر-safe, «معتمدين رسمياً», «العليا سكوير»)
import subprocess, json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
R = '/home/claude/htr-videos/'; SR = 48000
C = json.load(open(R + 'tools_ads/rot8/st_cues.json')); T = C['t']; O = C['off']; TOT = C['total']; N = int(TOT * SR)
OUTW = '/home/claude/work/st_mix.wav'; B = 60 / 124
def rd(f): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
rng = np.random.default_rng(124)
def tt(d): return np.arange(int(d * SR)) / SR
def add(b, t, s, g=1.0):
    i = int(t * SR)
    if i >= len(b) or i < 0: return
    s = s[:len(b) - i] * g; b[i:i + len(s)] += s
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def saw(m, d, det=1.0): ph = np.cumsum(np.full(int(d * SR), mtof(m) * det / SR)) % 1.0; return 2 * ph - 1
mus = np.zeros(N); drm = np.zeros(N); sfx = np.zeros(N); side = np.ones(N)
prog = [(57, 60, 64, 67), (53, 57, 60, 64), (55, 59, 62, 65), (52, 55, 59, 62)]  # Am7 Fmaj7 G7-ish Em7 — bright
DROP = T['deals']; END = TOT - .5
# hook: filtered pad only (calm 0–3 s)
for k in range(int(DROP / (B * 4)) + 1):
    ch = prog[k % 4]; d = tt(B * 4); x = sum(saw(m, B * 4) + saw(m, B * 4, 1.005) for m in ch)
    add(mus, k * B * 4, lp(x, 700 + 300 * k) * np.minimum(1, d / .5) * np.minimum(1, (B * 4 - d) / .2), .03)
# riser into the drop
tr = tt(1.2); add(sfx, DROP - 1.2, hp(rng.standard_normal(len(tr)), 1500) * (tr / tr[-1]) ** 2.5, .2)
t = DROP; i = 0
while t < END:
    bar = int((t - DROP) / (B * 4)); ch = prog[bar % 4]; q = i % 4
    tk = tt(.35); kick = np.sin(2 * np.pi * np.cumsum(48 + 110 * np.exp(-tk / .025)) / SR) * np.exp(-tk / .16); add(drm, t, np.tanh(2.2 * kick), 1.0)
    n = int(.22 * SR); a = int(t * SR); side[a:a + n] = np.minimum(side[a:a + n], .25 + .75 * (np.arange(min(n, N - a)) / n) ** .6)
    th = tt(.09); add(drm, t + B / 2, hp(rng.standard_normal(len(th)), 7000) * np.exp(-th / .03), .22)  # offbeat open hat
    if q in (1, 3): tc = tt(.25); add(drm, t, bp(rng.standard_normal(len(tc)), 900, 4000) * np.exp(-tc / .07), .4)  # clap
    # plucky chord stab on the "and" of 2 and 4
    if q in (1, 3):
        d = tt(.28); x = sum(saw(m + 12, .28) + saw(m + 12, .28, 1.007) for m in ch) * np.exp(-d / .09); add(mus, t + B / 2, lp(x, 3200), .05)
    # offbeat bass
    d = tt(B / 2 * .9); bs = np.sin(2 * np.pi * mtof(ch[0] - 24) * d) + .3 * saw(ch[0] - 12, B / 2 * .9); add(mus, t + B / 2, lp(bs, 500) * np.exp(-d / .2), .22)
    t += B; i += 1
for k in ['games', 'grid', 'grade', 'sell', 'member', 'bridge', 'tour', 'end']:  # swipe whooshes
    tw = tt(.32); add(sfx, T[k] - .16, bp(rng.standard_normal(len(tw)), 500, 6000) * np.sin(np.pi * tw / .32) ** 2, .4)
for c in [T['tour'] + .9 * j for j in range(1, 6)]:  # shutter clicks on footage cuts
    tc = tt(.06); add(sfx, c, hp(rng.standard_normal(len(tc)), 3000) * np.exp(-tc / .012), .3)
tb = tt(1.0); add(sfx, T['tour'], np.tanh(2 * np.sin(2 * np.pi * np.cumsum(40 + 90 * np.exp(-tb / .05)) / SR) * np.exp(-tb / .35)), .8)  # impact into the showroom
ts = tt(1.2); add(sfx, T['cgc'], sum(np.sin(2 * np.pi * f * ts) * np.exp(-ts / (.25 + j * .12)) for j, f in enumerate([1568, 2093, 2637])) * .4, .3)
# tension: duck music in the bridge before the impact
a, b = int((T['tour'] - .5) * SR), int(T['tour'] * SR); mus[a:b] *= np.linspace(1, .1, b - a); drm[a:b] *= np.linspace(1, 0, b - a)
mus *= side
# --- voice
def fade(x, f=.012): k = int(f * SR); x = x.copy(); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k); return x
def lev(x): return x / (np.sqrt(np.mean(x[np.abs(x) > .02] ** 2)) + 1e-9) * .18
VO = np.zeros(N)
for k in ['W1', 'W2', 'W3', 'W4', 'W5', 'W6', 'W7', 'W8']: add(VO, O[k], fade(lev(rd(R + f'fetch/st_{k}' + ('b' if k == 'W8' else '') + '.mp3'))))
add(VO, O['MT'], fade(lev(rd(R + 'voice_bank/mutamadeen.mp3'))))
ol = rd(R + 'audio/ref_htr_word.mp3'); ol = ol[int(.10 * SR):int(3.03 * SR)]; ke = int(.04 * SR); ol[-ke:] *= np.linspace(1, 0, ke); add(VO, O['OL'], fade(lev(ol)))
w = int(.12 * SR); env = np.convolve(np.abs(VO), np.ones(w) / w, 'same'); env = np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
bed = (mus / np.abs(mus).max() * .55 + drm / np.abs(drm).max() * .6) * (1 - .6 * env)
out = bed * .42 + sfx / np.abs(sfx).max() * .3 + VO / np.abs(VO).max() * .95
fo = int(.05 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = np.tanh(out * 1.15) / np.tanh(1.15); out = out / np.abs(out).max() * .95
wavfile.write(OUTW, SR, (out * 32767).astype(np.int16)); print('ok', TOT)
