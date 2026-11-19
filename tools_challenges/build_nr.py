"""No-reveal challenge build (owner 16-18 Nov 2026): script = intro, ask x N, CTA (N+2 lines, no reveal lines).
python3 build_nr.py gp|vs spec.json script.txt take.mp3 take.json STYLE BPM KEY out.mp4 [stills]
Writes vo.wav, words_final.json (word times on the final timeline for reel_score --words), renders + mixes."""
import sys, json, subprocess, numpy as np, os
from scipy.io import wavfile
kind, spec, scr, mp3, asr, style, bpm, key, out = sys.argv[1:10]
SR = 48000; G = '/home/claude/gp'
r = json.loads(subprocess.run(['python3', '/home/claude/v5/vsplit.py', mp3, asr, scr], capture_output=True, text=True, check=True).stdout)
cuts = r['cuts']
if os.environ.get('FIX'):
    for kv in os.environ['FIX'].split(','):
        k, v = kv.split(':'); cuts[int(k)] = float(v)
au = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', mp3, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
cuts = list(cuts[:-1]) + [len(au) / SR] if len(cuts) else cuts
def trim(x, a):
    e = np.abs(x) > .008; i = np.argmax(e); j = len(x) - np.argmax(e[::-1]); s0 = max(0, i - 240)
    y = x[s0:j + 1200].copy(); f = 200; y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f); return y, a + s0 / SR
segs, starts = zip(*[trim(au[int(a * SR):int(b * SR)], a) for a, b in zip(cuts, cuts[1:])]); L = [len(x) / SR for x in segs]
W_ = json.load(open(asr)); txt = [' '.join(w['w'].strip() for w in W_ if a - .05 <= (w['s'] + w['e']) / 2 < b) for a, b in zip(cuts, cuts[1:])]
print('cuts', [round(c, 2) for c in cuts])
for i, t in enumerate(txt): print(i, round(L[i], 2), t)
n = len(L) - 2; fr = lambda x: round(x * 30) / 30
sp = json.load(open(spec)); sp['no_reveal'] = True; sp['static_intro'] = True
INTRO = fr(max(3.3, L[0] + .45))  # hook still until >= 2.75 s (the intro exit animation starts 0.3 s before INTRO)
if kind == 'gp':
    think = [fr(L[1 + i] + .5) for i in range(n)]
    rlen = [fr(think[i] + 3.0 + .9) for i in range(n)]
    sp['timing'] = dict(intro=INTRO, think=think, rlen=rlen, outro=fr(max(4.4, L[-1] + 1.4)), end=2.0)
    offs = [0.1] + [INTRO + sum(rlen[:i]) + .25 for i in range(n)] + [INTRO + sum(rlen) + .2]
    args = ['python3', f'{G}/gp.py', spec]
else:
    ask = [fr(L[1 + i] + .45) for i in range(n)]
    sp['timing'] = dict(intro=INTRO, ask=ask, rev=[.9] * n, outro=fr(max(4.4, L[-1] + 1.4)))
    rl = [ask[i] + 2.6 + .9 for i in range(n)]
    offs = [0.1] + [INTRO + sum(rl[:i]) + .2 for i in range(n)] + [INTRO + sum(rl) + .2]
    args = ['python3', f'{G}/vs.py', spec]
json.dump(sp, open(spec, 'w'), ensure_ascii=False, indent=1)
st = subprocess.run(args + ['stills', '0.0', '1.5', '2.7'], capture_output=True, text=True, check=True).stdout.strip().split()
tot = float(st[-1])
vo = np.zeros(int((tot + .5) * SR))
for o, s in zip(offs, segs):
    i = int(o * SR); vo[i:i + len(s)] += s[:len(vo) - i]
wavfile.write('vo.wav', SR, (np.clip(vo, -1, 1) * 32767).astype(np.int16))
fw = []
for k, (a, b) in enumerate(zip(cuts, cuts[1:])):
    for w in W_:
        if a - .05 <= (w['s'] + w['e']) / 2 < b: fw.append(dict(w=w['w'], s=round(w['s'] - starts[k] + offs[k], 2), e=round(w['e'] - starts[k] + offs[k], 2)))
json.dump(fw, open('words_final.json', 'w'), ensure_ascii=False)
json.dump(dict(offs=offs, total=tot), open('offs.json', 'w'))
print('total', tot, 'offs', [round(o, 2) for o in offs])
if len(sys.argv) > 10: sys.exit()
subprocess.run(['python3', f'{G}/music.py'], env=dict(os.environ, STYLE=style, BPM=bpm, KEY=key), check=True)
cs = [round(c * 30) / 30 for c in (0, tot / 3, 2 * tot / 3, tot)]
for k in range(3): subprocess.run(args + [str(cs[k]), str(cs[k + 1]), f'_p{k}.mp4'], check=True)  # one at a time (2 cores)
open('_l.txt', 'w').write(''.join(f'file _p{k}.mp4\n' for k in range(3)))
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-i', '_l.txt', '-i', 'mix.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], check=True)
print('done', out)
