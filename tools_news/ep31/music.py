import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep31/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=112; beat=60/bpm; rng=np.random.default_rng(31)
# style ep31: retro synthwave (RGB theme) — 16th-note saw arpeggio Am-F-C-G, soft four-on-floor kick, offbeat hats, warm pad
def saw(f,dur,dec=7):
    n=int(dur*SR); x=np.arange(n)/SR; s=sum(np.sin(2*np.pi*f*k*x)/k for k in range(1,6))
    return s*np.exp(-x*dec)*np.minimum(1,x/.003)
def kick():
    n=int(.25*SR); x=np.arange(n)/SR; f=50+90*np.exp(-x*30); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*12)
def hat():
    n=int(.05*SR); x=np.arange(n)/SR; h=rng.standard_normal(n); h=np.diff(h,prepend=0); return h*np.exp(-x*80)
def pad(fs,dur):
    n=int(dur*SR); x=np.arange(n)/SR; env=np.minimum(1,x/.4)*np.minimum(1,(dur-x)/.4)
    return sum(np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*f*1.004*x) for f in fs)*env
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
chords=[[220,261.63,329.63],[174.61,220,261.63],[261.63,329.63,392],[196,246.94,293.66]]
s=0
while s*beat/4<T+1:
    at=s*beat/4; bar=s//16; ch=chords[bar%4]
    add(saw(ch[[0,1,2,1][s%4]]*2,beat/4,14),at,.02)
    if s%4==0: add(kick(),at,.09)
    if s%4==2: add(hat(),at,.025)
    if s%16==0: add(pad([c/2 for c in ch],beat*4),at,.018)
    s+=1
m=m[:N]
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.72*np.clip(env*6,0,1); sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/.05)
mix=v+m*.55; mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
