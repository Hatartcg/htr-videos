import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, fftconvolve
import json
CU=json.load(open('cues.json'))
SR = 48000; DUR = CU['total']; N = int(SR * DUR); rng = np.random.default_rng(11)
VO = 0.5; T_YGO, T_BOX, T_RC, T_24, T_CARDS, T_PRICE, T_CTA = 1.3, 2.4, 3.7, 5.04, 6.4, 8.37, 10.63
import os
B = 60 / float(os.environ.get('BPM','118'))
mus = np.zeros((N, 2)); drm = np.zeros((N, 2)); sfx = np.zeros((N, 2)); kenv = np.zeros(N)
def tt(d): return np.arange(int(d * SR)) / SR
def add(buf, t, s, g=1, pan=0):
    i = int(round(t * SR))
    if i >= N or i < 0: return
    s = s[:N - i] * g
    if s.ndim == 1: buf[i:i + len(s), 0] += s * (1 - max(0, pan)); buf[i:i + len(s), 1] += s * (1 + min(0, pan))
    else: buf[i:i + len(s)] += s
def mtof(m): return 440 * 2 ** ((m - 69) / 12)
def lp(s, fc): b, a = butter(2, min(fc, 23000) / (SR / 2)); return lfilter(b, a, s)
def hp(s, fc): b, a = butter(2, fc / (SR / 2), 'high'); return lfilter(b, a, s)
def bp(s, lo, hi): b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], 'band'); return lfilter(b, a, s)
def nz(d): return rng.standard_normal(int(d * SR))
def saw(f, t): return 2 * ((f * t + rng.uniform()) % 1) - 1
def kick():
    t = tt(.35); return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(48 + 160 * np.exp(-t / .025)) / SR) * np.exp(-t / .18))
def clap():
    t = tt(.3); n = bp(nz(.3), 900, 6000); e = sum(np.exp(-np.clip(t - d, 0, None) / .012) * (t >= d) for d in (0, .01, .02)) * .5 + np.exp(-t / .12) * .6
    return n * e
def hat(o=False): t = tt(.15 if o else .04); return hp(nz(len(t) / SR), 9000) * np.exp(-t / (.06 if o else .012))
def supersaw(ms, d, fc=6000):
    t = tt(d); s = np.zeros_like(t)
    for m in ms:
        for dt in (-.012, -.005, 0, .006, .013): s += saw(mtof(m) * (1 + dt), t)
    s /= (len(ms) * 5); s = lp(s, fc)
    stereo = np.stack([s, np.roll(s, 240)], 1)
    return stereo * np.minimum(1, t / .01)[:, None] * np.minimum(1, (d - t) / .05)[:, None]
def pluck(m, d=.3):
    t = tt(d); s = saw(mtof(m), t) * .6 + np.sin(2 * np.pi * mtof(m + 12) * t) * .4
    return lp(s, 3500) * np.exp(-t / .09)
def bass(m, d):
    t = tt(d); s = np.sin(2 * np.pi * mtof(m) * t) + .3 * np.tanh(3 * np.sin(2 * np.pi * mtof(m) * t))
    return s * np.minimum(1, t / .005) * np.minimum(1, (d - t) / .02)
def whoosh(d=.4):
    t = tt(d); x = t / d; n = nz(d); out = np.zeros_like(t); seg = 480
    for i in range(0, len(t), seg): fc = 400 * (7000 / 400) ** x[i]; out[i:i + seg] = bp(n[max(0, i - 400):i + seg], max(80, fc * .6), min(20000, fc * 1.6))[-len(out[i:i + seg]):]
    return out * np.sin(np.pi * x) ** 1.5 * 1.4
def riser(d): t = tt(d); x = t / d; return hp(nz(d), 2000) * x ** 2.5 * .5 + .25 * np.sin(2 * np.pi * np.cumsum(300 + 2500 * x ** 2) / SR) * x ** 2
def impact(d=1.6):
    t = tt(d); return (np.tanh(2 * np.sin(2 * np.pi * np.cumsum(35 + 110 * np.exp(-t / .05)) / SR)) * np.exp(-t / .5) + .5 * lp(nz(d), 400) * np.exp(-t / .25) + .35 * hp(nz(d), 5000) * np.exp(-t / .5))
def chime(base=84):
    out = np.zeros(int(1.2 * SR))
    for i, m in enumerate([base, base + 4, base + 7, base + 12, base + 16, base + 19]):
        t = tt(1.2 - i * .05); s = np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t / .35) + .3 * np.sin(2 * np.pi * mtof(m) * 3 * t) * np.exp(-t / .1)
        j = int(i * .05 * SR); out[j:j + len(s)] += s * .25
    return out
def pop(): t = tt(.12); return np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t / .03) + 300) / SR) * np.exp(-t / .03)
def tick(f=2400): t = tt(.04); return np.sin(2 * np.pi * f * t) * np.exp(-t / .008)
def ding():
    t = tt(1.4); return sum(np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t / .5) * g for m, g in ((93, .5), (100, .35), (105, .2)))
def kk(t, g=1):
    add(drm, t, kick(), g); i = int(t * SR); L = min(int(.3 * SR), N - i)
    if L > 0: kenv[i:i + L] = np.maximum(kenv[i:i + L], np.exp(-tt(.3)[:L] / .09))


def mallet(m,d=.25):
    t=tt(d); return (np.sin(2*np.pi*mtof(m)*t)+.3*np.sin(2*np.pi*mtof(m)*4*t)*np.exp(-t/.02))*np.exp(-t/.09)
def roll(d):
    t=tt(d); n=bp(nz(d),200,5000); g=(np.sin(2*np.pi*(18+10*t/d)*t)>0).astype(float)*.6+.4; return n*g*(.2+.8*t/d)*.5
KEY=int(os.environ.get('KEY','0'))
CH=[[n+KEY for n in c] for c in [[60,64,67,72],[57,60,64,69],[53,57,60,65],[55,59,62,67]]]; BS=[n+KEY for n in [36,33,29,31]]
mel=[n+KEY for n in [72,76,79,76,74,72,67,69]]
def stab(ms, d=.25):
    t = tt(d); return lp(sum(saw(mtof(m), t) for m in ms) / len(ms), 3500) * np.exp(-t / .08)
def bed(t0,t1,full=True):
    t=t0;k=0
    while t<t1-1e-6:
        bar=(k//4)%4; beat=k%4
        if beat==0: add(mus,t,bass(BS[bar],B*3.6),.4)
        add(mus,t+B/2,stab([m for m in CH[bar]],.18),.12)
        if full: add(mus,t,mallet(mel[k%8]),.18,pan=.3); add(mus,t+B/2,mallet(mel[(k+3)%8]-12),.1,pan=-.3)
        if beat in (0,2): kk(t,.7)
        if beat in (1,3): add(drm,t,clap(),.3)
        add(drm,t+B/2,hat(),.08); t+=B; k+=1
bed(0.0,CU['intro']+3.0)
add(sfx,0.05,impact(1.0),.6)
for j in range(3): add(sfx,.5+j*.12,whoosh(.3),.35)
for s_ in CU.get('starts',[]): add(sfx,s_,whoosh(.3),.45); add(sfx,s_+.05,pop(),.3)
if not CU['rounds']: bed(3.0, CU['outro'])
for r in CU['rounds']:
    a,cd,rv=r['start'],r['cd'],r['reveal']
    add(sfx,a,whoosh(.35),.5); bed(a,cd)
    for j in range(3): add(sfx,a+.3+j*.1,pop(),.35)
    add(sfx,cd,roll(rv-cd),.55)
    for j in range(3): add(sfx,cd+j,tick(1600+j*300),.8); add(drm,cd+j,kick(),.5)
    add(sfx,rv,impact(1.2),.9); add(sfx,rv+.02,ding(),.5); add(sfx,rv+.05,chime(84),.35)
    bed(rv,r['end'])
o=CU['outro']; bed(o,CU['end']); add(sfx,o,whoosh(.4),.5); add(sfx,o+2.0,chime(88),.4)
add(sfx,CU['end'],impact(1.5),.8); add(mus,CU['end'],supersaw([48,55,60,64,67],2.5,fc=3000),.4)
vs,vv=wavfile.read('vo.wav'); vv=vv.astype(np.float32)/32768; voice=np.zeros(N); voice[:min(N,len(vv))]=vv[:N]
venv=np.convolve(np.abs(voice),np.ones(int(.1*SR))/int(.1*SR),'same'); venv=np.clip(venv/(np.percentile(venv,95)+1e-9)*2,0,1)
mus*=(1-.4*kenv[:,None])
def norm(x): return x/(np.abs(x).max()+1e-9)
out=(norm(mus)*.45+norm(drm)*.5)*(1-.6*venv[:,None])*.6+norm(sfx)*.45*(1-.3*venv[:,None])+voice[:,None]*1.0
fo=int(.5*SR); out[-fo:]*=np.linspace(1,0,fo)[:,None]
out=np.tanh(out*1.3)/np.tanh(1.3); out=out/np.abs(out).max()*.95
wavfile.write('mix.wav',SR,(out*32767).astype(np.int16)); print('ok')
