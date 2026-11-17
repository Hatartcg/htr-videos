import numpy as np, soundfile as sf, json
W='/tmp/claude-0/ep30/'; SR=44100
v,_=sf.read(W+'v.wav'); fx,_=sf.read(W+'fix1.wav'); intro,_=sf.read(W+'intro.wav')
def cut(a,b,src=None):
    src=v if src is None else src
    s=src[int(a*SR):int(b*SR)].copy(); f=int(.02*SR); s[:f]*=np.linspace(0,1,f); s[-f:]*=np.linspace(1,0,f); return s
hook=cut(0,5.5)
L=[(6.18,11.9),(12.42,17.42),(17.86,22.22),(22.8,29.14),(29.58,32.72)]
G=np.zeros(int(.3*SR)); parts=[]; starts=[]; acc=0; LD=[]
for i,(a,b) in enumerate(L):
    seg=cut(a,b) if i else cut(0.0,6.3,fx); starts.append(acc); parts.append(seg); acc+=len(seg)/SR; LD.append(len(seg)/SR)
    if i<len(L)-1: parts.append(G); acc+=.3
rest=np.concatenate(parts)
out=np.concatenate([hook,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),rest,np.zeros(int(.15*SR))])
sf.write(W+'voice_full.wav',out,SR)
H=len(hook)/SR; R0=H+.15+len(intro)/SR+.3
# word timings shifted to video time (source words from fetch/asr/ep30_voice.mp3.json)
words=json.load(open('../../fetch/asr/ep30_voice.mp3.json')); vw=[]
for w in words:
    if w['s']<5.5: off=0
    else:
        k=next((i for i,(a,b) in enumerate(L) if a-.1<=w['s']<b),None)
        if k is None or k==0: continue
        off=R0+starts[k]-L[k][0]
    vw.append({'w':w['w'],'s':round(w['s']+off,2),'e':round(w['e']+off,2)})
vw+=[{'w':w['w'],'s':round(w['s']+R0,2),'e':round(w['e']+R0,2)} for w in json.load(open('../../fetch/asr/ep30_fix1.mp3.json'))]
iw=[('وهذه',.05,.45),('أخبار',.45,.95),('وأسعار',.95,1.5),('TCG',1.5,2.2),('مع',2.2,2.45),('هتر',2.45,2.95)]
vw+= [{'w':a,'s':round(H+.15+s,2),'e':round(H+.15+e,2)} for a,s,e in iw]
vw.sort(key=lambda x:x['s']); json.dump(vw,open(W+'words_video.json','w'),ensure_ascii=False)
res={'H':round(H,2),'intro_end':round(R0,2),'line_starts':[round(R0+s,2) for s in starts],'line_ends':[round(R0+s+d,2) for s,d in zip(starts,LD)],'total':round(len(out)/SR,2)}
json.dump(res,open('map.json','w')); print(res)
