import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep26/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=84; beat=60/bpm; rng=np.random.default_rng(26)
# style: lo-fi electric piano chords (A minor, i-VI-III-VII) + soft kick/hat + sub bass
def ep(f,dur):
    n=int(dur*SR); x=np.arange(n)/SR
    return (np.sin(2*np.pi*f*x+.8*np.sin(2*np.pi*f*x)*np.exp(-x*4))*np.exp(-x*1.6))*np.minimum(1,x/.01)
def kick():
    n=int(.25*SR); x=np.arange(n)/SR; f=50+90*np.exp(-x*30); return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*14)
def hat():
    n=int(.04*SR); h=rng.standard_normal(n)*np.exp(-np.arange(n)/SR*120); return np.diff(h,prepend=0)
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
A=220.0
chords=[(A,[1,6/5,3/2,9/4]),(174.61,[1,5/4,3/2,15/8]),(261.63,[1,5/4,3/2,15/8]),(196.0,[1,5/4,3/2,9/4])]  # Am F C G
b=0
while b*beat<T+1:
    bar=int(b//4); root,ch=chords[bar%4]
    if b%4==0:
        for j,r in enumerate(ch): add(ep(root*r,4*beat),b*beat+j*.015,.045)
    if b%2==0: add(kick(),b*beat,.25)
    if b%4==0 or b%4==3: add(np.sin(2*np.pi*root/4*np.arange(int(beat*SR))/SR)*np.exp(-np.arange(int(beat*SR))/SR*2.5),b*beat,.18)
    for h in (.5,):
        add(hat(),(b+h)*beat,.06)
    b+=1
m=m[:N]
# simple tape-ish lowpass
k=np.ones(6)/6; m=np.convolve(m,k,'same')
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.72*np.clip(env*6,0,1)
sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/1.0)*np.minimum(1,(T-t)/1.2)
mix=v*1.0+m*.55
mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
