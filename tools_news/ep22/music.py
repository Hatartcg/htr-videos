import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep22/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=96; beat=60/bpm; rng=np.random.default_rng(22)
# style: marimba-ish plucks in D dorian + warm pad + shaker
def note(f,dur,kind):
    n=int(dur*SR); x=np.arange(n)/SR
    if kind=='pluck': return (np.sin(2*np.pi*f*x)+.3*np.sin(2*np.pi*4*f*x)*np.exp(-x*30))*np.exp(-x*7)
    if kind=='pad': return (np.sin(2*np.pi*f*x)+.5*np.sin(2*np.pi*f*1.003*x))*np.minimum(1,x/.6)*np.minimum(1,(dur-x)/.6)
    if kind=='bass': return np.sin(2*np.pi*f*x)*np.exp(-x*3)
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
D=146.83; scale=[1,9/8,6/5,4/3,3/2,5/3,16/9,2]
chords=[(D,[1,6/5,3/2]),(D*4/3,[1,5/4,3/2]),(D*16/9/2*2,[1,6/5,3/2]),(D*3/2,[1,5/4,3/2])]
pat=[0,2,4,7,4,2,5,3]
b=0; k=0
while b*beat<T+1:
    bar=int(b//4); root,ch=chords[bar%4]
    if b%4==0:
        for r in ch: add(note(root*r,4*beat,'pad'),b*beat,.05)
        add(note(root/2,2*beat,'bass'),b*beat,.22)
    if b%4==2: add(note(root/2,2*beat,'bass'),b*beat,.16)
    for h in (0,.5):
        f=D*2*scale[pat[k%8]]; add(note(f,.6,'pluck'),(b+h)*beat,.09); k+=1
        sh=rng.standard_normal(int(.05*SR))*np.exp(-np.arange(int(.05*SR))/SR*80); add(np.diff(sh,prepend=0),(b+h+.25)*beat,.05)
    b+=1
m=m[:N]
# sidechain duck under voice
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.7*np.clip(env*6,0,1)
sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/1.0)*np.minimum(1,(T-t)/1.2)
mix=v*1.0+m*.55
mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
