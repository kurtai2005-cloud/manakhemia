import subprocess,re,sys,numpy as np,soundfile as sf
def lufs(path):
    # gated meters ignore <0.4s clips; measure the clip repeated back-to-back (with 0.1s gap) for ~4s
    x,sr=sf.read(path); gap=np.zeros(int(.1*sr)); r=int(np.ceil(4/(len(x)/sr+.1)))
    sf.write('/tmp/rep.wav',np.concatenate([np.concatenate([x,gap])]*r),sr)
    o=subprocess.run(['/usr/bin/ffmpeg','-hide_banner','-nostats','-i','/tmp/rep.wav','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS',o)[-1])

CEIL=10**(-1.5/20)
LCEIL=10**(-2.0/20)  # --linear 模式峰值上限 -2 dBFS（留位畀 ogg 編碼過衝）
def proc(x,drive): 
    y=np.tanh(x*drive)/np.tanh(drive*max(np.max(np.abs(x)),1e-9))  # soft-saturate, peak-normalised
    return y*CEIL
if __name__=="__main__":
  # usage: norm.py name[:targetLUFS] ...   (default -12, tanh-drive mode: legacy generic UI sfx)
  #        norm.py --linear name[:targetLUFS] ...  (pure gain, peak ceiling -2.0 dBFS; for soft/tonal sounds)
  args=sys.argv[1:]; linear=False
  if args and args[0]=='--linear': linear=True; args=args[1:]
  for a in args:
    k,_,tg=a.partition(':'); T=float(tg) if tg else -12.0
    x,sr=sf.read(f'tmp/{k}.wav'); x=x-np.mean(x)
    if linear:
        y=x/np.max(np.abs(x))*LCEIL; sf.write('tmp/_t.wav',y,sr,subtype='FLOAT'); L=lufs('tmp/_t.wav')
        g=min(1.0,10**((T-L)/20)); y=y*g; sf.write(f'tmp/{k}_n.wav',y,sr,subtype='FLOAT')
        print(k,'linear target',T,'LUFS(repeat-measured)',round(L+20*np.log10(g),1),'peak',round(20*np.log10(np.max(np.abs(y))),2)); continue
    best=None
    for d in [0.5,1,1.5,2,3,4,6]:
        y=proc(x,d); sf.write('tmp/_t.wav',y,sr,subtype='FLOAT'); L=lufs('tmp/_t.wav')
        if best is None or abs(L-T)<abs(best[1]-T): best=(d,L,y)
        if L>=T-0.5: break
    d,L,y=best; sf.write(f'tmp/{k}_n.wav',y,sr,subtype='FLOAT')
    print(k,'drive',d,'LUFS(repeat-measured)',round(L,1),'peak',round(20*np.log10(np.max(np.abs(y))),2))
