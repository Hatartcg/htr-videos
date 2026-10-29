"""python3 build_gp.py spec.json script.txt take.mp3 take.json STYLE BPM KEY out.mp4 [stills]"""
import sys, json, subprocess, numpy as np, os
from scipy.io import wavfile
spec, scr, mp3, asr, style, bpm, key, out = sys.argv[1:9]
SR = 48000; G = '/home/claude/gp'
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
for i, t in enumerate(r['text']): print(i, round(L[i], 2), t)
fr = lambda x: round(x * 30) / 30
n = (len(L) - 2) // 2
sp = json.load(open(spec))
think = [fr(L[1 + 2 * i] + .5) for i in range(n)]
rlen = [fr(think[i] + 3.0 + .15 + L[2 + 2 * i] + 1.0) for i in range(n)]
sp['timing'] = dict(intro=fr(max(2.2, L[0] + .5)), think=think, rlen=rlen, outro=fr(max(4.2, L[-1] + 2.2)), end=2.8)
json.dump(sp, open(spec, 'w'), ensure_ascii=False, indent=1)
tot = float(subprocess.run(['python3', f'{G}/gp.py', spec, 'stills', '0.5', '1.2'], capture_output=True, text=True, check=True).stdout.strip().split()[-1])
tm = sp['timing']; offs = [0.1]; t0 = tm['intro']
for i in range(n):
    offs += [t0 + .25, t0 + think[i] + 3.0 + .15]; t0 += rlen[i]
offs.append(t0 + .2)
vo = np.zeros(int((tot + .5) * SR))
for o, s in zip(offs, segs):
    i = int(o * SR); vo[i:i + len(s)] += s[:len(vo) - i]
wavfile.write('vo.wav', SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
print('total', tot)
if len(sys.argv) > 9: sys.exit()
subprocess.run(['python3', f'{G}/music.py'], env=dict(os.environ, STYLE=style, BPM=bpm, KEY=key), check=True)
cuts = [round(c * 30) / 30 for c in (0, tot / 3, 2 * tot / 3, tot)]
ps = [subprocess.Popen(['python3', f'{G}/gp.py', spec, str(cuts[k]), str(cuts[k + 1]), f'_p{k}.mp4']) for k in range(3)]
for p in ps: p.wait()
open('_l.txt', 'w').write(''.join(f'file _p{k}.mp4\n' for k in range(3)))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-i', '_l.txt', '-i', 'mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
print('done', out)
