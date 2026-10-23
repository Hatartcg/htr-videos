"""Split a multi-line TTS take into lines using Whisper word timestamps + RMS minima.
usage: python3 vsplit.py take.mp3 take.json script.txt  -> prints JSON {lens:[...], cuts:[...]} and writes segs.npy (object array)"""
import sys, json, re, subprocess, numpy as np, difflib
SR = 48000
mp3, asr, scr = sys.argv[1:4]
W = json.load(open(asr))
lines = [re.sub(r'\[[^\]]*\]', '', l).strip() for l in open(scr).read().split('[pause]')]
lines = [l for l in lines if l]
AR = str.maketrans('أإآىةؤئ', 'اااايوي')
def norm(s): return re.sub(r'[^\w]', '', re.sub(r'[ً-ْـ]', '', s)).translate(AR)
def words(l): return [norm(w) for w in l.split() if norm(w)]
v = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
aw = [norm(w['w']) for w in W]
# global alignment of script words to asr words
sw = []; owner = []
for li, l in enumerate(lines):
    for w in words(l): sw.append(w); owner.append(li)
sm = difflib.SequenceMatcher(None, sw, aw, autojunk=False)
map_ = {}
for a, b, n in sm.get_matching_blocks():
    for k in range(n): map_[a + k] = b + k
# fuzzy fill: for each line, first script word index -> asr index
starts = [0.0]
for li in range(1, len(lines)):
    idxs = [i for i, o in enumerate(owner) if o == li]
    cand = None
    # mapped asr index of first mapped word in this line
    first_m = next(((j, map_[si]) for j, si in enumerate(idxs) if si in map_), None)
    prev_m = max([map_[i] for i in range(idxs[0]) if i in map_] or [-1])
    if first_m is not None:
        j, ai = first_m
        if j == 0: cand = W[ai]['s']
        else:
            # fuzzy-match the unmatched leading words in the gap (prev_m, ai)
            best = None
            for k in range(prev_m + 1, ai + 1):
                r_ = difflib.SequenceMatcher(None, sw[idxs[0]], aw[k]).ratio()
                if best is None or r_ > best[0]: best = (r_, k)
            cand = W[best[1]]['s'] if best and best[0] >= .45 else W[ai]['s'] - .35 * j
    if cand is None:
        nxt = [map_[i] for i in range(idxs[-1] + 1, len(sw)) if i in map_]
        cand = (W[prev_m]['e'] + W[nxt[0]]['s']) / 2 if prev_m >= 0 and nxt else starts[-1] + 3
    starts.append(cand)
# refine each cut to the quietest 30ms window in [s-0.45, s+0.3]
cuts = [0.0]
w_ = int(.03 * SR)
for s in starts[1:]:
    a, b = int(max(0, s - .45) * SR), int(min(len(v) / SR, s + .3) * SR)
    r = [np.sqrt(np.mean(v[i:i + w_] ** 2)) for i in range(a, max(a + 1, b - w_), w_ // 2)]
    k = int(np.argmin(r)); cuts.append((a + k * w_ / 2 + w_ / 2) / SR)
cuts.append(len(v) / SR)
def trim(x):
    e = np.abs(x) > .008
    if not e.any(): return x[:SR // 10]
    i = np.argmax(e); j = len(x) - np.argmax(e[::-1]); y = x[max(0, i - 240):j + 1200].copy(); f = 200; y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y
segs = [trim(v[int(a * SR):int(b * SR)]) for a, b in zip(cuts, cuts[1:])]
np.save('segs.npy', np.array(segs, dtype=object), allow_pickle=True)
# per-line asr text for checking
chk = []
for a, b in zip(cuts, cuts[1:]):
    chk.append(' '.join(f"{w['w'].strip()}({w['p']:.2f})" for w in W if a - .05 <= w['s'] < b - .05))
print(json.dumps(dict(n=len(lines), lens=[round(len(s) / SR, 3) for s in segs], cuts=[round(c, 2) for c in cuts], text=chk), ensure_ascii=False, indent=0))
