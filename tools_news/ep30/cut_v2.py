# v2 (18 Nov): drop repeated items (OP-18 English date Nov 20 + Saint Gunko/Shamrock debut were already in news_log 2026-11-03).
# Edit only, no new credits: splice voice_full.wav [A,B) out.
import soundfile as sf, numpy as np, json
W='/tmp/claude-0/ep30/'; SR=44100; A,B=12.78,18.68; D=B-A
v,_=sf.read(W+'voice_full.wav'); f=int(.01*SR)
x=v[:int(A*SR)].copy(); y=v[int(B*SR):].copy(); x[-f:]*=np.linspace(1,0,f); y[:f]*=np.linspace(0,1,f)
out=np.concatenate([x,y]); sf.write(W+'voice_full.wav',out,SR)
wv=json.load(open('words_video.json')); nw=[]
for w in wv:
    if w['s']<A-.05: nw.append(w)
    elif w['s']>=B-.3: nw.append({'w':w['w'],'s':round(max(A,w['s']-D),2),'e':round(w['e']-D,2)})
json.dump(nw,open('words_video_v2.json','w'),ensure_ascii=False)
ep=json.load(open('episode.json')); segs=[]
for s in ep['segs']:
    if s['s']>=12.9 and s['e']<=18.7: continue
    s=dict(s)
    if s['s']>=18.6: s['s']=round(s['s']-D,2); s['e']=round(s['e']-D,2)
    elif s['e']>A and s['e']<13: s['e']=A
    segs.append(s)
ep['segs']=segs; ep['total']=round(len(out)/SR,2); segs[-1]['e']=ep['total']
ep['beats']=[2.5,4.2,7.3,10.8]+[round(b-D,2) for b in ep['beats'] if b>20]
json.dump(ep,open('episode_v2.json','w'),ensure_ascii=False,indent=1); print(ep['total'],[(s['s'],s['e'],s['title']) for s in segs],ep['beats'])
