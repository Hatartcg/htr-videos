"""python3 build.py KIND spec.json script.txt take.mp3 take.json STYLE KEY out.mp4 [stills-only]
KIND: gameshow | fight | market | elevator | sealed"""
import sys, json, subprocess, numpy as np, os
from scipy.io import wavfile
kind, spec, scr, mp3, asr, style, key, out = sys.argv[1:9]
only_stills = len(sys.argv) > 9
SR = 48000
r = json.loads(subprocess.run(['python3', '/home/claude/v5/vsplit.py', mp3, asr, scr], capture_output=True, text=True, check=True).stdout)
L = r['lens']; segs = list(np.load('segs.npy', allow_pickle=True))
if os.environ.get('FIX'):
    cuts = r['cuts']
    for kv in os.environ['FIX'].split(','):
        k, v = kv.split(':'); cuts[int(k)] = float(v)
    au = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
    def trim(x):
        e = np.abs(x) > .008
        i = np.argmax(e); j = len(x) - np.argmax(e[::-1]); y = x[max(0, i - 240):j + 1200].copy(); f = 200; y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y
    segs = [trim(au[int(a * SR):int(b * SR)]) for a, b in zip(cuts, cuts[1:])]; L = [len(x) / SR for x in segs]
    W_ = json.load(open(asr)); r['text'] = [' '.join(w['w'].strip() for w in W_ if a - .05 <= (w['s'] + w['e']) / 2 < b) for a, b in zip(cuts, cuts[1:])]
    print('cuts', cuts)
if os.environ.get('SWAP'):
    alt_mp3, alt_json, idx = os.environ['SWAP'].split(':'); idxs = [int(x) for x in idx.split(',')]
    r2 = json.loads(subprocess.run(['python3', 'vsplit.py', alt_mp3, alt_json, scr], capture_output=True, text=True, check=True).stdout)
    segs2 = list(np.load('segs.npy', allow_pickle=True))
    for k in idxs: segs[k] = segs2[k]; L[k] = r2['lens'][k]; r['text'][k] = 'SWAP ' + r2['text'][k]
for i, t in enumerate(r['text']): print(i, round(L[i], 2), t)
fr = lambda x: round(x * 30) / 30
sp = json.load(open(spec))
if kind in ('gameshow', 'fight'):
    n = (len(L) - 2) // 2
    sp['timing'] = dict(intro=fr(max(3.0 if kind == 'fight' else 3.4, L[0] + .7)), ask=[fr(L[1 + 2 * i] + (.25 if kind == 'fight' else .35)) for i in range(n)],
                        rev=[fr(L[2 + 2 * i] + 1.1) for i in range(n)], outro=fr(max(4.0, L[-1] + 2.0)))
elif kind == 'market':
    sp['timing'] = dict(intro=fr(max(3.2, L[0] + .5)), dur=[fr(max(3.6, l + .9)) for l in L[1:-1]], outro=fr(max(4.0, L[-1] + 2.0)))
    sp['timing']['dur'][-1] = fr(sp['timing']['dur'][-1] + .8)
elif kind == 'elevator':
    sp['timing'] = dict(intro=fr(max(3.4, L[0] + .6)), dur=[fr(.85 + l + .55) for l in L[1:-1]], outro=fr(max(4.0, L[-1] + 2.0)))
    sp['timing']['dur'][-1] = fr(sp['timing']['dur'][-1] + 1.0)
elif kind == 'sealed':
    b = [fr(max(2.3, l + .5)) for l in L]; b[-1] = fr(b[-1] + 1.0); sp['timing'] = dict(beats=b)
json.dump(sp, open(spec, 'w'), ensure_ascii=False, indent=1)
tot = float(subprocess.run(['python3', f'{kind}.py', spec, 'cues'], capture_output=True, text=True, check=True).stdout.strip().split()[-1])
cu = json.load(open('cues.json')); offs = cu['offs']
assert len(offs) == len(segs), (len(offs), len(segs))
vo = np.zeros(int((tot + .5) * SR))
for o, s in zip(offs, segs):
    i = int(o * SR); vo[i:i + len(s)] += s[:len(vo) - i]
wavfile.write('vo.wav', SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
print('total', tot)
if only_stills: sys.exit()
env = dict(os.environ, STYLE=style, KEY=key)
subprocess.run(['python3', 'music2.py'], env=env, check=True)
cuts = [0, tot / 3, 2 * tot / 3, tot]; cuts = [round(c * 30) / 30 for c in cuts]
ps = [subprocess.Popen(['python3', f'{kind}.py', spec, str(cuts[k]), str(cuts[k + 1]), f'_p{k}.mp4']) for k in range(3)]
for p in ps: p.wait()
open('_l.txt', 'w').write(''.join(f'file _p{k}.mp4\n' for k in range(3)))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-i', '_l.txt', '-i', 'mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
print('done', out)
