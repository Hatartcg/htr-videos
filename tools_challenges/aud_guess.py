import subprocess,json,numpy as np
from scipy.io import wavfile
from scipy.signal import butter,lfilter
SR=48000; C=json.load(open('cues.json')); T=C['total']; N=int(T*SR)
def rd(f):
    return np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',f,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout,np.float32).astype(np.float64)
rng=np.random.default_rng(19)
def tt(d): return np.arange(int(d*SR))/SR
def add(b,t,s,g=1):
    i=int(t*SR)
    if i>=len(b): return
    s=s[:len(b)-i]*g; b[i:i+len(s)]+=s
def lp(x,f): b,a=butter(2,f/(SR/2)); return lfilter(b,a,x)
def hp(x,f): b,a=butter(2,f/(SR/2),'high'); return lfilter(b,a,x)
def mtof(m): return 440*2**((m-69)/12)
mus=np.zeros(N); drm=np.zeros(N); sfx=np.zeros(N)
B=60/104; prog=[(52,55,59),(48,52,55),(50,54,57),(47,50,54)]
k=0; t=0.0; end_music=C['end']+1.5
while t<end_music:
    ch=prog[(k//4)%4]
    tk=tt(.35); kick=np.tanh(3*np.sin(2*np.pi*np.cumsum(50+140*np.exp(-tk/.02))/SR)*np.exp(-tk/.16))
    if k%2==0: add(drm,t,kick,.8)
    else: ts=tt(.2); add(drm,t,hp(rng.standard_normal(len(ts)),1500)*np.exp(-ts/.05),.5)
    for j in range(2): th=tt(.05); add(drm,t+j*B/2+B/4,hp(rng.standard_normal(len(th)),8000)*np.exp(-th/.01),.18)
    for j in range(4):
        tp=tt(B/4*.95); m=ch[(k*4+j)%3]+12; add(mus,t+j*B/4,lp(2*((mtof(m)*tp)%1)-1,2500)*np.exp(-tp/.09),.16)
    tb=tt(B*.9); add(mus,t,lp(np.sin(2*np.pi*mtof(ch[0]-12)*tb)+.3*(2*((mtof(ch[0]-12)*tb)%1)-1),500)*np.exp(-tb/.5),.35)
    t+=B; k+=1
for r in C['rounds']:
    for j in range(3): tc=tt(.12); add(sfx,r['cd']+j,np.sin(2*np.pi*(1200+300*j)*tc)*np.exp(-tc/.04),.4)
    tw=tt(.45); add(sfx,r['end']-.3,lp(hp(rng.standard_normal(len(tw)),500),6000)*np.sin(np.pi*tw/.45)**2,.4)
ti=tt(1.2); add(sfx,C['outro'],np.tanh(2*np.sin(2*np.pi*np.cumsum(30+100*np.exp(-ti/.05))/SR)*np.exp(-ti/.4)),.6)
L=[rd(f'v/L{i}.mp3') for i in range(1,7)]
def fade(x,f=.01):
    k=int(f*SR); x=x.copy(); x[:k]*=np.linspace(0,1,k); x[-k:]*=np.linspace(1,0,k); return x
def lev(x): return x/ (np.sqrt(np.mean(x[np.abs(x)>.02]**2))+1e-9)*.18
V=np.zeros(N); R=C['rounds']
for t,x in zip([0.15,R[0]['start']+.10,R[1]['start']+.10,R[2]['start']+.10,C['outro']+.10,C['end']+.05],L): add(V,t,fade(lev(x)))
w=int(.12*SR); env=np.convolve(np.abs(V),np.ones(w)/w,'same'); env=np.clip(env/(np.percentile(env[env>1e-4],70)+1e-9),0,1)
bed=(mus/np.abs(mus).max()*.5+drm/np.abs(drm).max()*.55)*(1-.6*env)
out=bed*.42+sfx/np.abs(sfx).max()*.18+V/np.abs(V).max()*.95
fo=int(.12*SR); out[-fo:]*=np.linspace(1,0,fo)
out=np.tanh(out*1.2)/np.tanh(1.2); out=out/np.abs(out).max()*.95
wavfile.write('mix19b.wav',SR,(out*32767).astype(np.int16)); print('ok',T)
