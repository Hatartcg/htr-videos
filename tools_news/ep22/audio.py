import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep22/'; SR=44100; TEMPO=1.12
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav')
HOOK_END=6.62; REST0=7.35
gaps=[(15.777,16.691),(25.453,26.151),(32.946,33.494),(38.455,39.015),(52.872,53.479)]
keep=[]; cur=REST0
for a,b in gaps:
    keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,len(v)/SR))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep])
hook=v[:int(HOOK_END*SR)]
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
json.dump({'H':H,'intro_end':R0,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in [16.69,26.15,39.0,46.69,53.48,57.68]}},open(W+'map.json','w'))
print(open(W+'map.json').read())
