"""Original procedurally generated SFX (numpy/scipy/soundfile). No samples used."""
import numpy as np, soundfile as sf
from scipy.signal import butter, lfilter
SR=44100
rng=np.random.default_rng(20261026)
def t(d): return np.arange(int(SR*d))/SR
def env(n,a=0.005,r=0.05,decay=None):
    e=np.ones(n); na=max(1,int(a*SR)); nr=max(1,int(r*SR))
    e[:na]=np.linspace(0,1,na); e[-nr:]*=np.linspace(1,0,nr)
    if decay: e*=np.exp(-np.arange(n)/SR*decay)
    return e
def tone(f,d,decay=8,a=0.003,r=0.03,harm=(1,),amps=(1,)):
    x=t(d); y=sum(A*np.sin(2*np.pi*f*h*x) for h,A in zip(harm,amps))
    return y*env(len(x),a,r,decay)
def sweep(f0,f1,d,decay=6,a=0.003,r=0.03):
    x=t(d); f=f0*(f1/f0)**(x/d); ph=2*np.pi*np.cumsum(f)/SR
    return np.sin(ph)*env(len(x),a,r,decay)
def noise(d,lo=None,hi=None,decay=30,a=0.001,r=0.02):
    n=rng.standard_normal(int(SR*d))
    if lo and hi: b,aa=butter(2,[lo/(SR/2),hi/(SR/2)],'band'); n=lfilter(b,aa,n)
    return n*env(len(n),a,r,decay)
def seq(parts,sr=SR):
    L=max(int(s*SR)+len(p) for s,p in parts); y=np.zeros(L)
    for s,p in parts: i=int(s*SR); y[i:i+len(p)]+=p
    return y
def mix(*a):
    L=max(len(x) for x in a); y=np.zeros(L)
    for x in a: y[:len(x)]+=x
    return y
n=lambda m:440*2**((m-69)/12)
S={}
S['sfx_tap']=mix(tone(1200,0.08,decay=45,harm=(1,2),amps=(1,.25)),0.3*noise(0.02,2000,8000,decay=150))
S['sfx_confirm']=seq([(0,tone(n(76),0.14,decay=14,harm=(1,2),amps=(1,.3))),(0.07,tone(n(83),0.25,decay=9,harm=(1,2),amps=(1,.3)))])
S['sfx_cancel']=seq([(0,tone(n(76),0.12,decay=16,harm=(1,2),amps=(1,.2))),(0.07,tone(n(69),0.22,decay=10,harm=(1,2),amps=(1,.2)))])
S['sfx_coin']=seq([(0,tone(n(88),0.06,decay=25,harm=(1,2,3),amps=(1,.4,.2))),(0.06,tone(n(95),0.4,decay=9,harm=(1,2,3),amps=(1,.4,.2)))])
S['sfx_hit']=mix(0.9*sweep(180,55,0.18,decay=14),0.8*noise(0.12,300,3500,decay=35))
S['sfx_win']=seq([(i*0.11,tone(n(m),0.5-i*0.02,decay=5,harm=(1,2,3),amps=(1,.35,.12))) for i,m in enumerate([72,76,79,84])]+
                 [(0.44,tone(n(m),1.2,decay=3,harm=(1,2),amps=(.7,.25))) for m in (72,76,79,84)])
S['sfx_lose']=seq([(0,tone(n(67),0.35,decay=6,harm=(1,2),amps=(1,.3))),(0.22,tone(n(63),0.35,decay=6,harm=(1,2),amps=(1,.3))),(0.44,sweep(n(60),n(53),0.9,decay=3.5))])
S['sfx_error']=seq([(0,tone(150,0.12,decay=6,harm=(1,3,5),amps=(1,.4,.2))),(0.15,tone(150,0.18,decay=6,harm=(1,3,5),amps=(1,.4,.2)))])
for k,v in S.items():
    v=v/np.max(np.abs(v))*0.8
    sf.write(f'tmp/{k}.wav',v,SR,subtype='PCM_16')
print(len(S))
