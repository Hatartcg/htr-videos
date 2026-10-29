import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep23/'; SR=44100; TEMPO=1.12
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
gaps=[(11.364,12.0555),(19.0195,19.5791),(25.2887,25.8237),(35.5939,36.1185),(42.9789,43.4566)]
# rest: 5.40..end, shortening gaps to 0.3
keep=[]; cur=5.40
for a,b in gaps:
    keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,len(v)/SR))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep])
hook=v[:int(4.55*SR)]
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
# fade edges a bit
f=int(.01*SR); h[-f:]*=np.linspace(1,0,f)
out=np.concatenate([h,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),r])
sf.write(W+'voice_full.wav',out,SR)
H=len(h)/SR; R0=H+.15+len(intro)/SR+.3
def m(t):  # original time -> new time
    if t<=4.55: return min(t,4.55)/TEMPO
    acc=0
    for a,b in keep:
        if t<a: return R0+acc/TEMPO
        if t<=b: return R0+(acc+t-a)/TEMPO
        acc+=b-a
    return R0+acc/TEMPO
json.dump({'H':H,'intro_end':R0,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in [5.40,12.0,19.5,25.8,27.0,36.1,43.4,48.72]}},open(W+'map.json','w'))
print(open(W+'map.json').read())
