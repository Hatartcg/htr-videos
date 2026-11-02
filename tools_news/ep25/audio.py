import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep25/'; SR=44100; TEMPO=1.12
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
# hook 0-6.36 s with its inner pause (1.86-2.31) trimmed to 0.3 s
hook=np.concatenate([v[:int(2.01*SR)], v[int(2.16*SR):int(6.36*SR)]])
gaps=[(11.81,12.77),(22.99,23.74),(28.95,29.59),(36.86,37.29),(45.74,46.30),(51.62,52.19)]
keep=[]; cur=7.16
for a,b in gaps:
    keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,len(v)/SR))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep])
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
f=int(.01*SR); h[-f:]*=np.linspace(1,0,f)
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
pts=[7.16,12.62,23.59,29.44,37.14,46.15,52.04]
json.dump({'H':H,'intro_end':R0,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in pts}},open(W+'map.json','w'))
print(open(W+'map.json').read())
