import numpy as np, json, wave
from scipy.signal import butter, sosfilt
SR=44100; D=sum(json.load(open("timing.json")))+0.3; N=int(D*SR)
rng=np.random.default_rng(7); bpm=140; beat=60/bpm
L=np.zeros(N); R=np.zeros(N)
def tt(d): return np.arange(int(d*SR))/SR
def env(x,a=0.004,r=0.02):
    n=len(x); e=np.ones(n); ai=max(1,int(a*SR)); ri=max(1,int(r*SR)); e[:ai]=np.linspace(0,1,ai); e[-ri:]*=np.linspace(1,0,ri); return x*e
def add(sig,at,g=1.0,pan=0.0):
    i=int(at*SR); j=min(N,i+len(sig))
    if i<0 or i>=N: return
    L[i:j]+=sig[:j-i]*g*(1-pan)/1.0; R[i:j]+=sig[:j-i]*g*(1+pan)/1.0
lp=lambda x,f: sosfilt(butter(2,f,'low',fs=SR,output='sos'),x)
hp=lambda x,f: sosfilt(butter(2,f,'high',fs=SR,output='sos'),x)
def kick():
    x=tt(.35); f=48+110*np.exp(-x*30); s=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*7)
    click=hp(rng.standard_normal(len(x)),2000)*np.exp(-x*300)*0.3
    return env(np.tanh((s+click)*1.6))
def snare():
    x=tt(.25); n=hp(rng.standard_normal(len(x)),1500)*np.exp(-x*18); b=np.sin(2*np.pi*190*x)*np.exp(-x*25)
    return env(0.6*n+0.5*b)
def hat(d=.05,open_=False):
    x=tt(d if not open_ else .2); n=hp(rng.standard_normal(len(x)),7000)*np.exp(-x*(60 if not open_ else 14)); return env(n*0.5)
def b808(f,d):
    x=tt(d); s=np.sin(2*np.pi*f*x); s=np.tanh(s*1.8)*np.minimum(1,x/0.01)*np.exp(-x*1.2); return env(s,0.005,0.04)
def saw(f,d,cut=3500):
    x=tt(d); s=sum(np.sin(2*np.pi*f*k*x)/k for k in range(1,12) if f*k<9000)
    s2=sum(np.sin(2*np.pi*f*1.006*k*x)/k for k in range(1,12) if f*k<9000)
    return env(lp((s+s2)*0.5,cut)*np.exp(-x*3.0),0.006,0.03)
def pad(fs,d):
    x=tt(d); s=sum(np.sin(2*np.pi*f*x)+0.5*np.sin(2*np.pi*f*2.003*x) for f in fs)
    return env(lp(s,2500),0.25,0.3)
mid=lambda m:440*2**((m-69)/12)
prog=[(45,[57,60,64]),(41,[53,57,60]),(48,[55,60,64]),(43,[55,59,62])]  # Am F C G (bass roots low)
lead=[76,74,72,74, 76,79,76,74, 72,72,74,76, 74,72,71,72]
bar=beat*4; nb=int(D/bar)+1; start=0.0
for b in range(nb):
    t0=start+b*bar; root,ch=prog[b%4]; inten=0.6 if b==0 else 1.0
    for k in range(4):
        add(kick(),t0+k*beat,0.9*inten)
        if k==2 and b%2==1: add(kick(),t0+k*beat+beat*0.5,0.6*inten)
        if k in(1,3): add(snare(),t0+k*beat,0.55*inten)
    for s in range(16):
        roll = (b%4==3 and s>=12)
        add(hat(.04),t0+s*beat/4,(0.22 if s%2 else 0.3)*inten,pan=0.3)
        if roll: add(hat(.03),t0+s*beat/4+beat/8,0.18,pan=0.3)
    add(hat(open_=True),t0+beat*3.5,0.2,pan=-0.3)
    add(b808(mid(root-12+12),bar*0.95),t0,0.55*inten)
    add(pad([mid(m) for m in ch],bar),t0,0.07*inten)
    for s,m in enumerate(lead[(b%2)*8:(b%2)*8+8]):
        add(saw(mid(m),beat/2*0.95),t0+s*beat/2,0.10*inten,pan=-0.15 if s%2 else 0.15)
# soft whooshes into each new segment (no burst at t=0)
tb=0; segs=json.load(open("timing.json"))
for d in segs[:-1]:
    tb+=d; x=tt(0.5); n=rng.standard_normal(len(x)); sw=lp(n, 3000)*np.linspace(0,1,len(x))**2*0.25
    add(env(sw,0.01,0.03),tb-0.5,1.0)
st=np.stack([L,R],1)
fi=int(0.8*SR); st[:fi]*=np.linspace(0,1,fi)[:,None]; fo=int(1.5*SR); st[-fo:]*=np.linspace(1,0,fo)[:,None]
st=np.tanh(st/np.abs(st).max()*1.2)*0.85
w=wave.open("hype.wav","wb");w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((st*32767).astype(np.int16).tobytes());w.close()
d=np.abs(np.diff(sosfilt(butter(4,1500,'low',fs=SR,output='sos'),st[:,0]),2)); print("ok",round(D,2),"lowband jump",d.max().round(5))
