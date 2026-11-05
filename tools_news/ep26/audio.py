import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep26/'; SR=44100; TEMPO=1.12
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
hook=v[:int(3.52*SR)]
gaps=[(9.35,9.83),(18.12,18.63),(29.97,30.45),(30.94,31.32),(39.43,39.89)]  # silences >0.4 s -> 0.3 s
keep=[]; cur=4.02
for a,b in gaps:
    keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,len(v)/SR))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep])
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
f=int(.03*SR); h[-f:]*=np.linspace(1,0,f)
out=np.concatenate([h,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),r])
sf.write(W+'voice_full.wav',out,SR)
H=len(h)/SR; R0=H+.15+len(intro)/SR+.3
def m(t):
    acc=0
    for a,b in keep:
        if t<a: return R0+acc/TEMPO
        if t<=b: return R0+(acc+t-a)/TEMPO
        acc+=b-a
    return R0+acc/TEMPO
pts=[4.02,9.7,18.48,27.1,30.3,39.8,44.96]
res={'H':H,'intro_end':R0,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in pts}}
json.dump(res,open('map.json','w')); print(res)
