import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep27/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=100; beat=60/bpm; rng=np.random.default_rng(27)
# style ep27: 16th-note synth pluck arpeggio (D minor: Dm-Bb-F-C), clap on 2&4, shaker 8ths, sine sub
def pluck(f,dur):
    n=int(dur*SR); x=np.arange(n)/SR
    s=np.sign(np.sin(2*np.pi*f*x))*.35+np.sin(2*np.pi*f*x)
    return s*np.exp(-x*9)*np.minimum(1,x/.004)
def clap():
    n=int(.12*SR); return rng.standard_normal(n)*np.exp(-np.arange(n)/SR*35)
def shaker():
    n=int(.05*SR); h=rng.standard_normal(n)*np.exp(-np.arange(n)/SR*90); return np.diff(h,prepend=0)
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
chords=[(293.66,[1,6/5,3/2,2]),(233.08,[1,5/4,3/2,2]),(349.23,[1,5/4,3/2,2]),(261.63,[1,5/4,3/2,2])]
pat=[0,1,2,3,2,1,2,3]
s=0
while s*beat/4<T+1:
    b=s//4; root,ch=chords[(b//4)%4]
    if s%2==0: add(pluck(root*ch[pat[(s//2)%8]],beat*.6),s*beat/4,.05)
    if s%4==0:
        add(shaker(),s*beat/4,.04); add(shaker(),(s+2)*beat/4,.03)
        if b%2==1: add(clap(),s*beat/4,.07)
        if b%4==0: add(np.sin(2*np.pi*root/4*np.arange(int(4*beat*SR))/SR)*np.exp(-np.arange(int(4*beat*SR))/SR*.9),s*beat/4,.16)
    s+=1
m=m[:N]; m=np.convolve(m,np.ones(4)/4,'same')
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.72*np.clip(env*6,0,1); sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/1.0)*np.minimum(1,(T-t)/1.2)
mix=v+m*.55; mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
