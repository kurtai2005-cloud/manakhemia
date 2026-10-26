#!/usr/bin/env python3
"""Detail analysis for selected pet SFX (measurement only)."""
import sys, json, subprocess, re, numpy as np
from scipy.signal import stft, find_peaks, butter, sosfilt
sys.path.insert(0,'.')
from audio_metrics import decode, db
D="/workspace/遊音-staging/audio/sfx/"
def loop_lufs(name):
    r=subprocess.run(["ffmpeg","-nostats","-i",D+name,"-af","aloop=loop=20:size=2000000000,ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    b=r[r.rfind("Summary:"):]; return float(re.search(r"I:\s+(-?[\d.]+)\s+LUFS",b).group(1))
def band(x,sr,lo,hi):
    f,t,Z=stft(x,sr,nperseg=2048,noverlap=1536); P=np.abs(Z)**2
    m=(f>=lo)&(f<hi); return float(P[m].sum()/P.sum()*100)
def onsets(x,sr):
    w=int(sr*0.005); env=np.sqrt(np.convolve(x**2,np.ones(w)/w,mode="same")); edb=20*np.log10(np.maximum(env,1e-6))
    # onset = rise of >=12 dB within 20 ms, from level below -30 dB rel peak or at least 12dB
    hop=int(sr*0.005); res=[]; last=-1
    for i in range(hop*4,len(edb)-hop*4,hop):
        rise=edb[i+4*hop//1 if False else min(i+4*hop,len(edb)-1)]-edb[i]
        if rise>=10 and (i-last)>sr*0.08:
            res.append((i/sr, float(rise))); last=i
    return res, edb.max()
def roughness(x,sr):
    # amplitude-modulation energy 15-150 Hz of envelope (rough zone), relative to total envelope AC energy
    w=int(sr*0.001); env=np.sqrt(np.convolve(x**2,np.ones(w)/w,mode="same"))[::int(sr*0.001)]
    e=env-env.mean(); F=np.abs(np.fft.rfft(e*np.hanning(len(e))))**2; fr=np.fft.rfftfreq(len(e),0.001)
    m=(fr>=15)&(fr<=150); return float(F[m].sum()/max(F[fr>1].sum(),1e-12)*100), float(fr[m][np.argmax(F[m])]) if m.any() else 0
def hnr(x,sr):
    # harmonic-to-noise proxy: autocorrelation peak height in voiced frames
    vals=[]
    for s in range(0,len(x)-2048,512):
        fr=x[s:s+2048]
        if np.sqrt(np.mean(fr**2))<10**(-40/20): continue
        fr=fr-fr.mean(); ac=np.correlate(fr,fr,"full")[2047:]; ac/=ac[0]
        lo=int(sr/1000); hi=int(sr/70); vals.append(ac[lo:hi].max())
    return float(np.median(vals)) if vals else None
def prof(x,sr,step=0.1):
    n=int(sr*step); return [round(db(np.sqrt(np.mean(x[i:i+n]**2))),1) for i in range(0,len(x)-n+1,n)]
def pitch_track(x,sr):
    out=[]
    for s in range(0,len(x)-2048,1024):
        fr=x[s:s+2048]
        if np.sqrt(np.mean(fr**2))<10**(-40/20): out.append(None); continue
        fr=fr-fr.mean(); ac=np.correlate(fr,fr,"full")[2047:]; ac/=ac[0]
        lo=int(sr/1000); hi=int(sr/70); k=lo+int(np.argmax(ac[lo:hi])); out.append(round(sr/k) if ac[k]>0.5 else None)
    return out
def loopcheck(x,sr):
    t=np.concatenate([x,x,x]); d=np.abs(np.diff(t)); n=len(x)
    seam=max(d[n-3:n+2].max(),d[2*n-3:2*n+2].max())
    d2=np.abs(np.diff(t,2)); seam2=max(d2[n-3:n+2].max(),d2[2*n-3:2*n+2].max())
    w=int(sr*0.05); a=db(np.sqrt(np.mean(x[-w:]**2))); b=db(np.sqrt(np.mean(x[:w]**2)))
    return dict(seam_step=float(seam),p999_step=float(np.percentile(d,99.9)),max_step=float(d.max()),seam_step2=float(seam2),p999_step2=float(np.percentile(d2,99.9)),rms_tail50=a,rms_head50=b,dc=float(x.mean()))
res={}
for nm in ["sfx_pet_grumpy","sfx_pet_uncomfortable","sfx_pet_content","sfx_pet_happy","sfx_pet_hungry","sfx_pet_curious","sfx_pet_sleepy","sfx_event_sulk","sfx_event_dream_talk","sfx_event_shiny_day","sfx_event_gift_return","sfx_pet_sleep_breath_loop","sfx_env_sunbathe_loop","sfx_pet_touch_a","sfx_pet_touch_b","sfx_pet_yawn"]:
    x,sr=decode(D+nm+".ogg"); o,_=onsets(x,sr); r,rf=roughness(x,sr)
    res[nm]=dict(lufs_loop=loop_lufs(nm+".ogg"),b_2_5k=band(x,sr,2000,5000),b_sub150=band(x,sr,0,150),b_150_1k=band(x,sr,150,1000),b_1_4k=band(x,sr,1000,4000),b_4k=band(x,sr,4000,22050),
      onsets=[(round(a,3),round(b,1)) for a,b in o],rough_pct=r,rough_hz=rf,hnr=hnr(x,sr),prof100=prof(x,sr),pitch=pitch_track(x,sr),loop=loopcheck(x,sr))
json.dump(res,open('/tmp/d.json','w'),indent=1)
for k,v in res.items(): print(k,{a:(round(b,2) if isinstance(b,float) else b) for a,b in v.items() if a not in('loop',)}, "\n")
for k in ['sfx_pet_sleep_breath_loop','sfx_env_sunbathe_loop']: print(k,res[k]['loop'])
