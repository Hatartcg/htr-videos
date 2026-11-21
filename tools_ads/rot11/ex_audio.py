# rot11 OP-18 explainer — mix: voice-first (like the reference), new bed for this series: soft marimba-style plucks 100 BPM
# in D major pentatonic, very low; motivated SFX on every sticker (pop), stamps (thud), X marks (ticks), price drop (down-sweep).
import subprocess, json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
R = '/home/claude/htr-videos/'; SR = 48000
C = json.load(open(R + 'tools_ads/rot11/ex_cues.json')); O = C['off']; K = C['k']; TOT = C['total']; N = int(TOT * SR)
OUTW = '/home/claude/work/ex_mix.wav'; B = 60 / 100
rng = np.random.default_rng(18)
def rd(f, sp=1.0): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-af', f'atempo={sp}', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
def tt(d): return np.arange(int(d * SR)) / SR
def add(b, t, s, g=1.0):
    i = int(t * SR)
    if i >= len(b) or i < 0: return
    s = s[:len(b) - i] * g; b[i:i + len(s)] += s
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
mus = np.zeros(N); sfx = np.zeros(N)
def mar(m, d=.5):
    x = tt(d); f0 = mtof(m); return (np.sin(2 * np.pi * f0 * x) + .35 * np.sin(2 * np.pi * 4 * f0 * x) * np.exp(-x / .03)) * np.exp(-x / .18)
pent = [62, 64, 66, 69, 71, 74, 76]
patt = [0, 2, 4, 2, 5, 4, 2, 3, 1, 3, 5, 3, 6, 4, 3, 2]
t = 0.0; i = 0
while t < TOT - .6:
    m = pent[patt[i % 16]]; add(mus, t, mar(m), .5)
    if i % 4 == 0: x = tt(B * 4); add(mus, t, np.sin(2 * np.pi * mtof(pent[(i // 4) % 3] - 24) * x) * np.exp(-x / .9), .35)  # soft bass
    if i % 2 == 1: th = tt(.05); add(mus, t, hp(rng.standard_normal(len(th)), 6000) * np.exp(-th / .015), .12)  # shaker
    t += B / 2; i += 1
def popx(t, g=.35):
    x = tt(.09); add(sfx, t, np.sin(2 * np.pi * np.cumsum(900 + 1400 * np.exp(-x / .02)) / SR) * np.exp(-x / .025), g)
def thud(t, g=.9):
    x = tt(.6); add(sfx, t, np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-x / .04)) / SR) * np.exp(-x / .22)), g)
    n = tt(.15); add(sfx, t, bp(rng.standard_normal(len(n)), 300, 3000) * np.exp(-n / .04), .4)
def tick(t, g=.25):
    x = tt(.04); add(sfx, t, hp(rng.standard_normal(len(x)), 2500) * np.exp(-x / .008), g)
def whoosh(t, g=.25):
    x = tt(.3); add(sfx, t - .15, bp(rng.standard_normal(len(x)), 600, 5000) * np.sin(np.pi * x / .3) ** 2, g)
thud(K['dead'])
for j in range(12): tick(O['L2'] + .15 + j * .1, .15); tick(K['grid_x'] + j * .12, .3)
thud(K['grid_x'] + 12 * .12, .5)
for k in ['L2', 'L4', 'L5', 'L6', 'L7', 'L8', 'OL']: whoosh(O[k] - .05)
for c in C['cuts']: whoosh(c, .12)
for k in ['yes', 'no', 'good', 'loss', 'a', 'b', 'share', 'save', 'fol', 'onl', 'plus', 'olaya']: popx(K[k])
thud(K['unpub'], .55)
x = tt(.8); add(sfx, K['p200'] - .3, np.sin(2 * np.pi * np.cumsum(1200 * np.exp(-x / .3) + 120) / SR) * np.exp(-x / .5), .25)  # price drop sweep
thud(K['p200'], .5)
def fade(x, f=.012): k = int(f * SR); x = x.copy(); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k); return x
def lev(x): return x / (np.sqrt(np.mean(x[np.abs(x) > .02] ** 2)) + 1e-9) * .18
VO = np.zeros(N)
for k, fn in C['files'].items(): add(VO, O[k], fade(lev(rd(R + f'fetch/{fn}.mp3', C['speed']))))
ol = rd(R + 'audio/ref_htr_word.mp3'); ol = ol[int(.10 * SR):int(3.03 * SR)]; ke = int(.04 * SR); ol[-ke:] *= np.linspace(1, 0, ke); add(VO, O['OL'], fade(lev(ol)))
w = int(.12 * SR); env = np.convolve(np.abs(VO), np.ones(w) / w, 'same'); env = np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
bed = mus / np.abs(mus).max() * (1 - .55 * env)
out = bed * .16 + sfx / np.abs(sfx).max() * .32 + VO / np.abs(VO).max() * .95
fo = int(.3 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = np.tanh(out * 1.1) / np.tanh(1.1); out = out / np.abs(out).max() * .95
wavfile.write(OUTW, SR, (out * 32767).astype(np.int16)); print('ok', TOT)
