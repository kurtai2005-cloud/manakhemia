#!/usr/bin/env python3
"""Measurement-only audio metrics for SFX (reads, never modifies). Usage: audio_metrics.py DIR OUT.json"""
import sys, os, json, subprocess, re, glob
import numpy as np
from scipy.signal import stft

def decode(p, sr=44100):
    raw = subprocess.run(["ffmpeg","-v","error","-i",p,"-f","f32le","-ac","1","-ar",str(sr),"-"],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32).astype(np.float64), sr

def ebur(p):
    r = subprocess.run(["ffmpeg","-nostats","-i",p,"-filter_complex","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    blk = r[r.rfind("Summary:"):]
    I = re.search(r"I:\s+(-?[\d.]+|-inf)\s+LUFS",blk); TP = re.search(r"Peak:\s+(-?[\d.]+|-inf)\s+dBFS",blk)
    f=lambda m: float(m.group(1)) if m else None
    return f(I), f(TP)

def db(x): return 20*np.log10(max(x,1e-12))

def yin_f0(x, sr, fmin=60, fmax=3000, frame=2048, hop=512):
    f0=[]; 
    for s in range(0,len(x)-frame,hop):
        fr=x[s:s+frame]
        if np.sqrt(np.mean(fr**2))<10**(-45/20): continue
        tmax=int(sr/fmin); tmin=int(sr/fmax)
        d=np.array([np.sum((fr[:frame//2]-fr[t:t+frame//2])**2) for t in range(tmax)])
        cm=np.cumsum(d)/np.arange(1,tmax+1); dn=np.ones_like(d); dn[1:]=d[1:]*np.arange(1,tmax)/np.maximum(np.cumsum(d)[1:],1e-12)
        for t in range(tmin,tmax-1):
            if dn[t]<0.15 and dn[t]<=dn[t+1]:
                f0.append(sr/t); break
    return np.array(f0)

def analyze(p):
    x,sr=decode(p); n=len(x); dur=n/sr
    I,TP=ebur(p)
    pk=np.max(np.abs(x)); rms=np.sqrt(np.mean(x**2))
    # envelope 2ms RMS
    w=int(sr*0.002); env=np.sqrt(np.convolve(x**2,np.ones(w)/w,mode="same"))
    emax=env.max(); i10=np.argmax(env>0.1*emax); i90=np.argmax(env>0.9*emax); imax=int(np.argmax(env))
    onset=np.argmax(env>0.02*emax)
    attack_10_90=(i90-i10)/sr*1000; t_to_peak=(imax-onset)/sr*1000
    # sharpness: max env slope dB/ms
    edb=20*np.log10(np.maximum(env,1e-6)); 
    slope=np.max(np.diff(edb[:max(imax,2)])) *sr/1000 if imax>2 else 0
    # clip
    clip=int(np.sum(np.abs(x)>=0.999))
    # spectrum
    f,t,Z=stft(x,sr,nperseg=2048,noverlap=1536); P=np.abs(Z)**2
    tot=P.sum(); ps=P.sum(axis=1)
    cen=float((f*ps).sum()/max(ps.sum(),1e-12)); hf=float(ps[f>4000].sum()/max(tot,1e-12))
    hf8=float(ps[f>8000].sum()/max(tot,1e-12))
    dom=float(f[np.argmax(ps)])
    f0=yin_f0(x[::1],sr) if dur<4 else yin_f0(x[:sr*4],sr)
    f0lo,f0hi,f0med=(np.percentile(f0,5),np.percentile(f0,95),np.median(f0)) if len(f0)>3 else (None,None,None)
    # fades
    def rms_ms(a,b): 
        seg=x[int(a*sr/1000):int(b*sr/1000)]; return db(np.sqrt(np.mean(seg**2))) if len(seg) else None
    first5=db(np.max(np.abs(x[:int(.005*sr)]))); last5=db(np.max(np.abs(x[-int(.005*sr):])))
    last20=rms_ms(dur*1000-20,dur*1000)
    # loudness range of 100ms windows
    w100=int(0.1*sr); fr=[db(np.sqrt(np.mean(x[i:i+w100]**2))) for i in range(0,n-w100,w100)]
    dyn=(max(fr)-np.percentile(fr,10)) if fr else 0
    # seam (loop)
    seam=abs(x[0]-x[-1]); d=np.abs(np.diff(x)); p999=np.percentile(d,99.9)
    # transient: peak vs 100ms RMS around
    return dict(file=os.path.basename(p),dur=dur,peak_db=db(pk),tp_db=TP,lufs=I,rms_db=db(rms),crest_db=db(pk)-db(rms),
        attack_10_90_ms=attack_10_90,t_onset_to_peak_ms=t_to_peak,max_rise_db_per_ms=float(slope),clip_samples=clip,
        centroid_hz=cen,hf4k_pct=hf*100,hf8k_pct=hf8*100,dom_hz=dom,f0_p5=f0lo,f0_p95=f0hi,f0_med=f0med,
        first5ms_peak_db=first5,last5ms_peak_db=last5,last20ms_rms_db=last20,dyn_range_100ms=dyn,
        seam_diff=float(seam),step_p999=float(p999),dc=float(np.mean(x)),samples=n,
        env_1s=[round(float(np.mean(edb[int(i*sr*dur/10):int((i+1)*sr*dur/10)])),1) for i in range(10)])

if __name__=="__main__":
    out={}
    for p in sorted(glob.glob(os.path.join(sys.argv[1],"*.ogg"))):
        out[os.path.basename(p)]=analyze(p)
    json.dump(out,open(sys.argv[2],"w"),indent=1,ensure_ascii=False)
