# rot8 Delta Reign — mix: dark trap 140 BPM (new for this series), silence before the price hit, drop on the hit
import subprocess, json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter
R = '/home/claude/htr-videos/'; SR = 48000
import os
C = json.load(open(R + 'tools_ads/rot8/' + os.environ.get('CUES', 'dr_cues.json')))
OUTW = os.environ.get('OUTW', '/home/claude/work/dr_mix.wav'); T = C['t']; TOT = C['total']; N = int(TOT * SR); B = C['beat']
def rd(f): return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
rng = np.random.default_rng(140)
def tt(d): return np.arange(int(d * SR)) / SR
def add(b, t, s, g=1.0):
    i = int(t * SR)
    if i >= len(b) or i < 0: return
    s = s[:len(b) - i] * g; b[i:i + len(s)] += s
def lp(x, f): b, a = butter(2, f / (SR / 2)); return lfilter(b, a, x)
def hp(x, f): b, a = butter(2, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, x)
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
mus = np.zeros(N); drm = np.zeros(N); sfx = np.zeros(N)
# pad (calm hook 0 → hit): dark minor chords, slow swell
prog = [(45, 48, 52), (41, 45, 48), (43, 47, 50), (40, 43, 47)]
for k in range(int(TOT / (B * 8)) + 1):
    t0 = k * B * 8; ch = prog[k % 4]; d = tt(B * 8)
    s = sum(np.sin(2 * np.pi * mtof(m + 12) * d) + .4 * np.sin(2 * np.pi * mtof(m + 24) * d * 1.003) for m in ch)
    add(mus, t0, lp(s, 1800) * np.minimum(1, d / .8) * np.minimum(1, (B * 8 - d) / .3), .07)
# drums: start on the hit (drop)
hit = T.get('drop', T['hit']); end_d = TOT - .6; RS = T.get('riser_from', T['s2'])
t = hit - int(hit / B) * B; k = 0
while t < end_d:
    if t >= hit - 1e-6:
        bar = int(round((t - hit) / B))
        if bar % 8 in (0, 3, 6):  # 808 kick + sub
            tk = tt(.6); f = 45 + 100 * np.exp(-tk / .03); x = np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.exp(-tk / .35); add(drm, t, x, .9)
        if bar % 4 == 2:  # clap
            tc = tt(.25); add(drm, t, bp(rng.standard_normal(len(tc)), 900, 4000) * np.exp(-tc / .06), .55)
        for j in range(2 if bar % 8 != 7 else 4):  # hats (rolls on bar end)
            th = tt(.05); add(drm, t + j * B / (2 if bar % 8 != 7 else 4), hp(rng.standard_normal(len(th)), 7000) * np.exp(-th / .012), .16)
    t += B
# bell lead after the hit (sparse)
for i, m in enumerate([69, 72, 76, 74, 72, 69, 67, 69]):
    tb = hit + i * B * 2
    if tb < end_d: d = tt(.6); add(mus, tb, (np.sin(2 * np.pi * mtof(m) * d) + .3 * np.sin(2 * np.pi * mtof(m) * 3.01 * d)) * np.exp(-d / .25), .05)
if C.get('music') == 'taiko':  # One Piece: taiko + shime + shamisen (miyako-bushi scale), 120 BPM — different family from the trap
    mus = np.zeros(N); drm = np.zeros(N); hit = T['drop']
    scale = [52, 53, 57, 59, 60, 64, 65, 69]  # E F A B C (miyako-bushi)
    def taiko(g):
        tk = tt(.9); f0 = 70 + 60 * np.exp(-tk / .04); x = np.sin(2 * np.pi * np.cumsum(f0) / SR) * np.exp(-tk / .45) + .3 * lp(rng.standard_normal(len(tk)), 400) * np.exp(-tk / .05); return x * g
    def shime():
        ts = tt(.12); return bp(rng.standard_normal(len(ts)), 1500, 5000) * np.exp(-ts / .02)
    def pluck(m, d=.7):
        n = int(SR / mtof(m)); buf = rng.uniform(-1, 1, n); out = np.zeros(int(d * SR))
        for i in range(len(out)): out[i] = buf[i % n]; buf[i % n] = .5 * (buf[i % n] + buf[(i + 1) % n]) * .996
        return hp(out, 200) * np.exp(-np.arange(len(out)) / SR / .5)
    # calm hook: low drone only
    dd = tt(hit); add(mus, 0, lp(np.sin(2 * np.pi * 82.4 * dd) + .5 * np.sin(2 * np.pi * 123.5 * dd), 600) * np.minimum(1, dd / .6), .25)
    t = hit; i = 0; mel = [0, 2, 3, 4, 3, 2, 1, 0, 2, 4, 5, 4, 3, 2, 3, 1]
    while t < end_d:
        bar = i % 8
        if bar in (0, 3, 5): add(drm, t, taiko(1.0))
        if bar == 6: add(drm, t, taiko(.6)); add(drm, t + B / 2, taiko(.7))
        add(drm, t, shime(), .35); add(drm, t + B / 2, shime(), .2)
        if i % 2 == 0: add(mus, t, pluck(scale[mel[(i // 2) % 16]]), .35)
        t += B; i += 1
    for w in [T[k] for k in C.get('whoosh', [])]: add(drm, w, taiko(1.2))  # big hit on each reveal cut
if C.get('music') == 'epic':  # cinematic hybrid trailer: string ostinato + braams + booms + choir pad, 120 BPM, D minor
    mus = np.zeros(N); drm = np.zeros(N); hit = T['drop']; Be = .5
    def saw(m, d, det=1.0):
        ph = np.cumsum(np.full(int(d * SR), mtof(m) * det / SR)) % 1.0; return 2 * ph - 1
    def boom(g=1.0):
        tk = tt(1.6); f0 = 38 + 70 * np.exp(-tk / .06); x = np.sin(2 * np.pi * np.cumsum(f0) / SR) * np.exp(-tk / .7) + .5 * lp(rng.standard_normal(len(tk)), 300) * np.exp(-tk / .12); return np.tanh(1.8 * x) * g
    def braam(ch, d=1.6):
        x = sum(saw(m, d) + saw(m, d, 1.006) for m in ch); env = np.minimum(1, tt(d) / .03) * np.exp(-tt(d) / .9); return lp(x, 900) * env
    prog = [(38, 45, 50, 53), (34, 41, 46, 50), (36, 43, 48, 52), (33, 40, 45, 49)]  # Dm Bb C A
    # hook: choir-like pad (vowel-filtered saws) swelling, no drums
    for k in range(int(TOT / (Be * 8)) + 1):
        t0 = k * Be * 8; ch = prog[k % 4]; d = tt(Be * 8)
        x = sum(saw(m + 12, Be * 8) + saw(m + 12, Be * 8, 1.004) for m in ch[1:])
        x = bp(x, 500, 1100) + .6 * bp(x, 1300, 2600)
        add(mus, t0, x * np.minimum(1, d / 1.0) * np.minimum(1, (Be * 8 - d) / .4), .05)
    # after the drop: low string ostinato in 16ths + booms + braams on reveals
    t = hit; i = 0
    while t < end_d:
        ch = prog[int((t - hit) / (Be * 8)) % 4]; pat = [0, 0, 2, 0, 1, 0, 2, 3][i % 8]
        m = ch[0] + 12 if pat in (0, 1) else ch[pat] + (0 if pat == 2 else -12)
        d = tt(Be / 2 * .9); x = (saw(m, Be / 2 * .9) + saw(m, Be / 2 * .9, 1.005)) * np.exp(-d / .09)
        add(mus, t, lp(x, 2200), .09)
        if i % 8 == 0: add(drm, t, boom(1.0))
        if i % 8 == 4: tc = tt(.3); add(drm, t, bp(rng.standard_normal(len(tc)), 200, 1200) * np.exp(-tc / .08), .45)
        if i % 2 == 1: th = tt(.06); add(drm, t, hp(rng.standard_normal(len(th)), 6000) * np.exp(-th / .015), .09)
        t += Be / 2; i += 1
    for w in [T[k] for k in C.get('whoosh', [])]: add(drm, w, boom(1.2)); add(mus, w, braam(prog[0]), .12)
# --- sfx: riser into the hit, silence 0.45 s before it, glass shatter, whooshes on whips, shimmer on the gold card, stamp thud
tr = tt(max(.3, hit - RS - .45)); add(sfx, RS, hp(rng.standard_normal(len(tr)), 600) * (tr / tr[-1]) ** 2, .25)
tg = tt(1.0); g = hp(rng.standard_normal(len(tg)), 2500) * np.exp(-tg / .18)
for f0 in (2300, 3100, 4700, 6200): g += .3 * np.sin(2 * np.pi * f0 * tg) * np.exp(-tg / .25)
add(sfx, hit, g, .6); ti = tt(.8); add(sfx, hit, np.tanh(2 * np.sin(2 * np.pi * np.cumsum(35 + 80 * np.exp(-ti / .05)) / SR) * np.exp(-ti / .3)), .8)
for w in [T[k] for k in C.get('whoosh', ['s4', 's5', 's6'])]:
    tw = tt(.35); add(sfx, w - .17, bp(rng.standard_normal(len(tw)), 400, 5000) * np.sin(np.pi * tw / .35) ** 2, .45)
ts = tt(1.6); add(sfx, T['mega'], sum(np.sin(2 * np.pi * f * ts) * np.exp(-ts / (.3 + i * .15)) for i, f in enumerate([1568, 2093, 2637, 3136])) * .4, .35)
td = tt(.4); add(sfx, T.get('thud', T['save']), np.tanh(3 * np.sin(2 * np.pi * np.cumsum(60 + 120 * np.exp(-td / .02)) / SR) * np.exp(-td / .12)), .6)
tp = tt(.3); add(sfx, T.get('olaya', T.get('olaya2', 0)), np.sin(2 * np.pi * 880 * tp) * np.exp(-tp / .08), .25)
# kill music 0.45 s before the hit (tension gap)
g0, g1 = int((hit - .45) * SR), int(hit * SR); mus[g0:g1] *= np.linspace(1, 0, g1 - g0) ** 3
# --- voice
def fade(x, f=.01): k = int(f * SR); x = x.copy(); x[:k] *= np.linspace(0, 1, k); x[-k:] *= np.linspace(1, 0, k); return x
def lev(x): return x / (np.sqrt(np.mean(x[np.abs(x) > .02] ** 2)) + 1e-9) * .18
V = np.zeros(N)
for k, fn in C.get('lines', {'L1': 'r8v4_L1', 'L2': 'r8v4_L2', 'L3': 'r8v4_L3', 'L4': 'r8v4_L4', 'L5': 'r8v4_L5', 'L7': 'r8v4_L7b'}).items():
    if isinstance(fn, dict):
        x = rd(R + 'fetch/' + fn['fn'] + '.mp3'); x = lev(x)[int(fn['a'] * SR):int(fn['b'] * SR)]; add(V, C['off'][k] + fn['a'], fade(x, .02))
    else: add(V, C['off'][k], fade(lev(rd(R + 'fetch/' + fn + '.mp3'))))
sp = C['L6_splice']; xa = fade(rd(R + sp['a'])[int(sp.get('a_start', 0) * SR):int(sp['a_end'] * SR)]); k = int(sp.get('tail_fade', .01) * SR); xa[-k:] *= np.linspace(1, 0, k); xb = rd(R + sp['b']); xb = xb[int(sp.get('b_start', 0) * SR):int(sp.get('b_end', len(xb) / SR) * SR)]; xb[:k] *= np.linspace(0, 1, k); ke = int(.04 * SR); xb[-ke:] *= np.linspace(1, 0, ke); xb = fade(xb)
xa, xb = lev(xa), lev(xb); add(V, C['off']['L6'] + sp.get('a_start', 0), xa); add(V, C['off']['L6'] + sp['a_end'] + sp['gap'], xb)  # ref trimmed by b_start; timeline shifts by -b_start
w = int(.12 * SR); env = np.convolve(np.abs(V), np.ones(w) / w, 'same'); env = np.clip(env / (np.percentile(env[env > 1e-4], 70) + 1e-9), 0, 1)
bed = (mus / np.abs(mus).max() * .55 + drm / np.abs(drm).max() * .6) * (1 - .62 * env)
out = bed * .42 + sfx / np.abs(sfx).max() * .3 + V / np.abs(V).max() * .95
fo = int(.04 * SR); out[-fo:] *= np.linspace(1, 0, fo)
out = np.tanh(out * 1.15) / np.tanh(1.15); out = out / np.abs(out).max() * .95
wavfile.write(OUTW, SR, (out * 32767).astype(np.int16)); print('ok', TOT)
