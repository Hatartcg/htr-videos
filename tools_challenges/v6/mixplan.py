"""mixplan.py — mixes a stream reel's audio from a JSON plan (zero credits). New 26 Nov 2026.
python3 mixplan.py DUR plan.json out.wav [music.wav] [music_gain]
plan: [{src, s0?, s1?, cuts?:[[a,b],..] (keep-ranges, squeezes pauses), at, db (target RMS of the piece)}]"""
import numpy as np, subprocess, json, sys
import scipy.io.wavfile as w
SR = 48000
def load(path, s0=None, s1=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', str(s0), '-t', str(s1 - s0)] if s0 is not None else []) + ['-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).copy()
def fade(a, fi=.02, fo=.04):
    n1, n2 = min(len(a), int(fi * SR)), min(len(a), int(fo * SR)); a[:n1] *= np.linspace(0, 1, n1); a[len(a) - n2:] *= np.linspace(1, 0, n2); return a
def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
DUR = float(sys.argv[1]); plan = json.load(open(sys.argv[2])); out = sys.argv[3]
N = int(DUR * SR); voice = np.zeros(N)
for p in plan:
    a = load(p['src'], p.get('s0'), p.get('s1'))
    if 'cuts' in p: a = np.concatenate([fade(a[int(x * SR):int(y * SR)].copy(), .01, .03) for x, y in p['cuts']])
    a = fade(a); loud = np.abs(a) > .01
    if loud.any(): a *= 10 ** ((p.get('db', -20) - rms_db(a[loud])) / 20)
    i = int(p['at'] * SR); a = a[:N - i]; voice[i:i + len(a)] += a
mus = load(sys.argv[4]) if len(sys.argv) > 4 else np.zeros(N); mus = np.pad(mus, (0, max(0, N - len(mus))))[:N]
mus *= 10 ** ((-26 - rms_db(mus)) / 20)
y = voice + mus * float(sys.argv[5] if len(sys.argv) > 5 else 1); y /= max(1, np.abs(y).max() / .95)
w.write(out, SR, np.stack([y, y], 1).astype(np.float32))
