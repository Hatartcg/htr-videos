import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep27/'; SR=44100; TEMPO=1.08
v,_=sf.read(W+'v.wav'); intro,_=sf.read(W+'intro.wav'); end,_=sf.read(W+'end.wav')
hook=v[:int(4.06*SR)]
gaps=[(9.95,10.47),(16.09,16.59),(22.53,23.03)]   # silences >0.4 s -> 0.3 s
keep=[]; cur=4.56
for a,b in gaps: keep.append((cur,a+0.15)); cur=b-0.15
keep.append((cur,28.45))
rest=np.concatenate([v[int(a*SR):int(b*SR)] for a,b in keep]+[np.zeros(int(.3*SR)),end[:int(4.05*SR)]])
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
f=int(.03*SR); h[-f:]*=np.linspace(1,0,f)
out=np.concatenate([h,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),r,np.zeros(int(.4*SR))])
sf.write(W+'voice_full.wav',out,SR)
H=len(h)/SR; R0=H+.15+len(intro)/SR+.3
L=sum(b-a for a,b in keep)
def m(t):
    acc=0
    for a,b in keep:
        if t<a: return R0+acc/TEMPO
        if t<=b: return R0+(acc+t-a)/TEMPO
        acc+=b-a
    return R0+acc/TEMPO
pts=[4.56,10.2,16.3,22.8,28.45]
res={'H':H,'intro_end':R0,'end_start':R0+(L+.3)/TEMPO,'total':len(out)/SR,'map':{str(x):round(m(x),2) for x in pts}}
json.dump(res,open('map.json','w')); print(res)
