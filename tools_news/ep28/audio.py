import numpy as np, soundfile as sf, json, subprocess
W='/tmp/claude-0/ep28/'; SR=44100; TEMPO=1.08
v,_=sf.read(W+'v.wav'); fix,_=sf.read(W+'fix.wav'); intro,_=sf.read(W+'intro.wav')
hook=fix[:int(3.78*SR)]                      # redo take: hook line ("دولار" fixed)
G=np.zeros(int(.3*SR))
# lines (source, start, end)
L=[(v,4.57,10.34),(v,10.63,17.32),(v,17.52,22.81),(fix,4.48,11.36),(v,30.17,36.75),(v,36.84,40.6)]
parts=[]; starts=[]; acc=0
for i,(src,a,b) in enumerate(L):
    seg=src[int(a*SR):int(b*SR)].copy(); f=int(.02*SR); seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    starts.append(acc); parts.append(seg); acc+=len(seg)/SR
    if i<len(L)-1: parts.append(G); acc+=.3
rest=np.concatenate(parts)
def tempo(x,name):
    sf.write(W+name+'_in.wav',x,SR); subprocess.run(['ffmpeg','-v','error','-y','-i',W+name+'_in.wav','-af',f'atempo={TEMPO}',W+name+'_t.wav'],check=True)
    return sf.read(W+name+'_t.wav')[0]
h=tempo(hook,'hook'); r=tempo(rest,'rest')
f=int(.03*SR); h[-f:]*=np.linspace(1,0,f)
out=np.concatenate([h,np.zeros(int(.15*SR)),intro,np.zeros(int(.3*SR)),r,np.zeros(int(.15*SR))])
sf.write(W+'voice_full.wav',out,SR)
H=len(h)/SR; R0=H+.15+len(intro)/SR+.3
res={'H':round(H,2),'intro_end':round(R0,2),'line_starts':[round(R0+s/TEMPO,2) for s in starts],'total':round(len(out)/SR,2)}
json.dump(res,open('map.json','w')); print(res)
