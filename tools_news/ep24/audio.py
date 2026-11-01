import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep24/'; SR=44100; TEMPO=1.12
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
gaps=[(10.88,11.62),(20.96,21.5),(28.12,28.62),(30.78,31.28),(37.3,37.78),(44.68,45.18),(51.66,52.12)]
keep=[]; cur=5.08
for a,b in gaps:
    keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,len(v)/SR))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep])
hook=v[:int(4.6*SR)]
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
f=int(.01*SR); h[-f:]*=np.linspace(1,0,f)
out=np.concatenate([h,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),r])
sf.write(W+'voice_full.wav',out,SR)
H=len(h)/SR; R0=H+.15+len(intro)/SR+.3
def m(t):
    if t<=4.6: return min(t,4.6)/TEMPO
    acc=0
    for a,b in keep:
        if t<a: return R0+acc/TEMPO
        if t<=b: return R0+(acc+t-a)/TEMPO
        acc+=b-a
    return R0+acc/TEMPO
pts=[5.08,11.5,21.4,28.5,37.7,40.15,42.4,45.1,52.0,56.8]
json.dump({'H':H,'intro_end':R0,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in pts}},open(W+'map.json','w'))
print(open(W+'map.json').read())
