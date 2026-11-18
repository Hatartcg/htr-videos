"""python3 build_t10.py spec.json script.txt take.mp3 take.json STYLE KEY out.mp4 [stills]   (FIX=idx:time,... like v5/build.py)"""
import sys, json, subprocess, numpy as np, os
from scipy.io import wavfile
spec, scr, mp3, asr, style, key, out = sys.argv[1:8]
only = len(sys.argv) > 8
SR = 48000
r = json.loads(subprocess.run(['python3', '/home/claude/v5/vsplit.py', mp3, asr, scr], capture_output=True, text=True, check=True).stdout)
L = r['lens']; segs = list(np.load('segs.npy', allow_pickle=True))
au = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
cuts = r['cuts']
if os.environ.get('FIX'):
    for kv in os.environ['FIX'].split(','):
        k, v = kv.split(':'); cuts[int(k)] = float(v)
def trim(x):
    e = np.abs(x) > .008
    i = np.argmax(e); j = len(x) - np.argmax(e[::-1]); y = x[max(0, i - 240):j + 1200].copy(); f = 200; y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y, max(0, i - 240) / SR
cuts = list(cuts) + ([len(au) / SR] if len(cuts) == len(L) else [])
segs, leads = [], []
for a, b in zip(cuts, cuts[1:]):
    y, ld = trim(au[int(a * SR):int(b * SR)]); segs.append(y); leads.append(a + ld)
L = [len(x) / SR for x in segs]
W_ = json.load(open(asr))
txt = [' '.join(w['w'].strip() for w in W_ if a - .05 <= (w['s'] + w['e']) / 2 < b) for a, b in zip(cuts, cuts[1:])]
for i, t in enumerate(txt): print(i, round(cuts[i], 2), round(L[i], 2), t)
fr = lambda x: round(x * 30) / 30
sp = json.load(open(spec)); n = len(L)
sp['timing'] = dict(intro=fr(max(3.0, L[0] + .35)), dur=[fr(max(2.5, l + .55)) for l in L[1:-2]], mystery=fr(L[-2] + .3 + 3.0), cta=fr(L[-1] + .9), end=2.8, ib=float(os.environ.get('IB', '2.85')))
json.dump(sp, open(spec, 'w'), ensure_ascii=False, indent=1)
tot = float(subprocess.run(['python3', 't10q.py', spec, 'cues'], capture_output=True, text=True, check=True).stdout.strip().split()[-1])
cu = json.load(open('cues.json')); offs = cu['offs']; offs[0] = 0.05
assert len(offs) == len(segs), (len(offs), len(segs))
vo = np.zeros(int((tot + .5) * SR))
for o, s in zip(offs, segs):
    i = int(o * SR); vo[i:i + len(s)] += s[:len(vo) - i]
wavfile.write('vo.wav', SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
# words on the FINAL timeline (for reel_score --words)
fw = []
for li, (a, b) in enumerate(zip(cuts, cuts[1:])):
    sh = offs[li] - leads[li]
    fw += [dict(w=w['w'], s=round(w['s'] + sh, 2), e=round(w['e'] + sh, 2)) for w in W_ if a - .05 <= (w['s'] + w['e']) / 2 < b]
json.dump(fw, open('words_final.json', 'w'), ensure_ascii=False)
print('total', tot, 'cuts', cuts)
if only: sys.exit()
subprocess.run(['python3', 'music2.py'], env=dict(os.environ, STYLE=style, KEY=key), check=True)
c3 = [round(c * 30) / 30 for c in (0, tot / 2, tot)]
for k in range(2): subprocess.run(['python3', 't10q.py', spec, str(c3[k]), str(c3[k + 1]), f'_p{k}.mp4'], check=True)
open('_l.txt', 'w').write(''.join(f'file _p{k}.mp4\n' for k in range(2)))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-i', '_l.txt', '-i', 'mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
print('done', out)
