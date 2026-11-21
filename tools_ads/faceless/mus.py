import sys, json, numpy as np, subprocess
from scipy.io import wavfile
from scipy.signal import butter, lfilter
VID = sys.argv[1]; D = '/home/claude/htr-videos/tools_ads/faceless/'
import importlib.util
M = json.load(open(D + f'meta_{VID}.json')); TOT = M['total']; OFF = M['off']
SR = 48000; N = int(TOT * SR); rng = np.random.default_rng({'v1': 1, 'v2': 2, 'v3': 3}[VID])
def tt(d): return np.arange(int(d * SR)) / SR
def add(b, t, s, g=1.0):
    i = int(t * SR)
    if 0 <= i < len(b): s = s[:len(b) - i] * g; b[i:i + len(s)] += s
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
# playful marimba/bounce — key and tempo differ per episode
BPM, ROOT = {'v1': (104, 60), 'v2': (96, 62), 'v3': (112, 57)}[VID]; B = 60 / BPM
mus = np.zeros(N)
scale = [0, 2, 4, 7, 9, 12, 14]
pat = [0, 2, 4, 2, 5, 4, 2, 1]
def mar(m, d=.35):
    t = tt(d); f = mtof(m); return (np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / .02)) * np.exp(-t / .12)
def kick():
    t = tt(.3); return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-t / .03)) / SR) * np.exp(-t / .15)
def clap():
    t = tt(.2); return bp(rng.standard_normal(len(t)), 900, 4000) * np.exp(-t / .05)
def shaker():
    t = tt(.06); return bp(rng.standard_normal(len(t)), 5000, 11000) * np.exp(-t / .015)
prog = [0, 5, 3, 4]
k = 0; t0 = 0
while t0 < TOT - .5:
    bar = int(t0 / (4 * B)); r = ROOT + [0, 5, -3, -5][bar % 4]
    step = k % 8
    add(mus, t0, mar(r + 12 + scale[pat[step] % len(scale)]), .32)
    if step in (0, 4): add(mus, t0, kick(), .55)
    if step in (2, 6): add(mus, t0, clap(), .22)
    add(mus, t0, shaker(), .08)
    if step == 0: add(mus, t0, lp(sum(np.sin(2 * np.pi * mtof(r + i) * tt(4 * B)) for i in (0, 4, 7)), 900) * np.exp(-tt(4 * B) / 1.5), .06)
    t0 += B / 2; k += 1
mus /= np.abs(mus).max() + 1e-9
# voice + ducking + whoosh on cuts + pop on end
v = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f'/home/claude/htr-videos/fetch/fl_{VID}.mp3', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
V = np.zeros(N); add(V, OFF, v / (np.abs(v).max() + 1e-9) * .95)
sfx = np.zeros(N)
sys.argv = ['x', VID]; spec = importlib.util.spec_from_file_location('fl', D + 'fl.py')
cuts = json.load(open(D + f'cuts_{VID}.json'))
for c in cuts:
    t = tt(.35); n = bp(rng.standard_normal(len(t)), 500, 4500) * np.sin(np.pi * t / .35) ** 2; add(sfx, c - .2, n, .25)
end = OFF + json.load(open(D + f'meta_{VID}.json'))['vdur']
t = tt(.25); add(sfx, end, np.sin(2 * np.pi * 1200 * t) * np.exp(-t / .05), .3)
w = int(.1 * SR); env = np.convolve(np.abs(V), np.ones(w) / w, 'same'); env = np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
out = mus * .30 * (1 - .55 * env) + V + sfx
fo = int(.5 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out /= max(1, np.abs(out).max() / .97)
wavfile.write(D + f'mix_{VID}.wav', SR, (out * 32767).astype(np.int16)); print('mix ok', VID)
