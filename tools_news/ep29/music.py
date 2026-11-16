import numpy as np, soundfile as sf
SR=44100; W='/tmp/claude-0/ep29/'
v,_=sf.read(W+'voice_full.wav'); N=len(v); T=N/SR; t=np.arange(N)/SR
bpm=104; beat=60/bpm; rng=np.random.default_rng(29)
# style ep29: festive "celebration" — bright synth-pluck arpeggio (A major), hand claps on 2&4, soft sub bass, sparkle bells
def pluck(f,dur):
    n=int(dur*SR); x=np.arange(n)/SR
    return (np.sign(np.sin(2*np.pi*f*x))*.25+np.sin(2*np.pi*f*x))*np.exp(-x*9)*np.minimum(1,x/.002)
def clap():
    n=int(.15*SR); x=np.arange(n)/SR; return rng.standard_normal(n)*np.exp(-x*35)
def bass(f,dur):
    n=int(dur*SR); x=np.arange(n)/SR; return np.sin(2*np.pi*f*x)*np.minimum(1,x/.01)*np.exp(-x*2.5)
def bell(f):
    n=int(.6*SR); x=np.arange(n)/SR; return (np.sin(2*np.pi*f*x)+.4*np.sin(2*np.pi*2.76*f*x))*np.exp(-x*6)
m=np.zeros(N+SR*4)
def add(x,at,g):
    i=int(at*SR); m[i:i+len(x)]+=g*x[:len(m)-i]
chords=[[440,554.37,659.25],[369.99,440,554.37],[293.66,369.99,440],[329.63,415.3,493.88]]  # A F#m D E
roots=[110,92.5,73.42,82.41]
s=0
while s*beat/4<T+1:
    at=s*beat/4; bar=s//16; ch=chords[bar%4]
    if s%2==0: add(pluck(ch[(s//2)%3]*(2 if (s//2)%6>2 else 1),beat/2),at,.035)
    if s%16 in (4,12): add(clap(),at,.05)
    if s%8==0: add(bass(roots[bar%4],beat*2),at,.10)
    if s%16==14 and rng.random()<.5: add(bell(ch[rng.integers(3)]*4),at,.012)
    s+=1
m=m[:N]
env=np.convolve(np.abs(v),np.ones(int(.08*SR))/int(.08*SR),'same'); env=env/env.max()
duck=1-.72*np.clip(env*6,0,1); sm=np.convolve(duck,np.ones(int(.15*SR))/int(.15*SR),'same')
m=m*sm*np.minimum(1,t/.05)
mix=v+m*.55; mix/=max(1,np.abs(mix).max()/0.97)
sf.write(W+'mix.wav',mix,SR); print(T)
