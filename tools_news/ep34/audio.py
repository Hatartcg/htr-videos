import numpy as np, soundfile as sf, json, os
W='/tmp/claude-0/-home-claude-htr-videos/eedbad27-d74c-50cc-b0df-30754faca503/scratchpad/ep34/'; SR=44100
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
def cut(a,b,src):
    s=src[int(a*SR):int(b*SR)].copy(); f=int(.02*SR); s[:f]*=np.linspace(0,1,f); s[-f:]*=np.linspace(1,0,f); return s
HA,HB=0.0,3.55; RA,RB=4.15,38.3
hook=cut(HA,HB,v); rest=cut(RA,RB,v); intro=cut(0,3.0,intro)
out=np.concatenate([hook,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),rest,np.zeros(int(.15*SR))])
sf.write(W+'voice_full.wav',out,SR)
H=len(hook)/SR; R0=H+.15+len(intro)/SR+.3
if os.path.exists('../../fetch/asr/ep34_voice.mp3.json'):
    words=json.load(open('../../fetch/asr/ep34_voice.mp3.json')); vw=[]
    for w in words:
        if w['s']<HB: off=0
        elif w['s']>=RA-.1: off=R0-RA
        else: continue
        vw.append({'w':w['w'],'s':round(w['s']+off,2),'e':round(w['e']+off,2)})
    iw=[('وهذه',.05,.45),('أخبار',.45,.95),('وأسعار',.95,1.5),('TCG',1.5,2.2),('مع',2.2,2.45),('هتر',2.45,2.95)]
    vw+=[{'w':a,'s':round(H+.15+s,2),'e':round(H+.15+e,2)} for a,s,e in iw]
    vw.sort(key=lambda x:x['s']); json.dump(vw,open('words_video.json','w'),ensure_ascii=False)
res={'H':round(H,2),'intro_end':round(R0,2),'off_rest':round(R0-RA,2),'total':round(len(out)/SR,2)}
json.dump(res,open('map.json','w')); print(res)
