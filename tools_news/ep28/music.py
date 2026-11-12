import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep28/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=92; beat=60/bpm; rng=np.random.default_rng(28)
# style ep28: underwater marimba (E minor pentatonic) + soft kick on 1&3 + bubbly high blips + warm pad
def marimba(f,dur):
    n=int(dur*SR); x=np.arange(n)/SR
    return (np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*4*f*x)*np.exp(-x*30))*np.exp(-x*6)*np.minimum(1,x/.003)
def kick():
    n=int(.25*SR); x=np.arange(n)/SR; return np.sin(2*np.pi*(55+70*np.exp(-x*25))*x)*np.exp(-x*12)
def blip(f):
    n=int(.08*SR); x=np.arange(n)/SR; return np.sin(2*np.pi*f*(1+2*x)*x)*np.exp(-x*40)
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
scale=[329.63,392.0,440.0,493.88,587.33,659.25]
roots=[82.41,65.41,98.0,73.42]   # E C G D
s=0
while s*beat/2<T+1:
    at=s*beat/2; bar=s//8
    if rng.random()<.8: add(marimba(scale[rng.integers(len(scale))],beat),at,.06)
    if s%4==0: add(kick(),at,.12)
    if s%8==3 and rng.random()<.6: add(blip(1200+rng.random()*800),at,.02)
    if s%8==0:
        r=roots[bar%4]; n=int(4*beat*SR); x=np.arange(n)/SR
        pad=sum(np.sin(2*np.pi*r*k*x+k) for k in (2,3,4))/3*np.minimum(1,x/.4)*np.minimum(1,(4*beat-x)/.4)
        add(pad,at,.05)
    s+=1
m=m[:N]
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.72*np.clip(env*6,0,1); sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/.3)*np.minimum(1,(T-t)/1.0)
mix=v+m*.55; mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
