import subprocess,re,sys,numpy as np,soundfile as sf
def lufs(path):
    # gated meters ignore <0.4s clips; measure the clip repeated back-to-back (with 0.1s gap) for ~4s
    x,sr=sf.read(path); gap=np.zeros(int(.1*sr)); r=int(np.ceil(4/(len(x)/sr+.1)))
    sf.write('/tmp/rep.wav',np.concatenate([np.concatenate([x,gap])]*r),sr)
    o=subprocess.run(['/usr/bin/ffmpeg','-hide_banner','-nostats','-i','/tmp/rep.wav','-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS',o)[-1])

CEIL=10**(-1.5/20)
def proc(x,drive): 
    y=np.tanh(x*drive)/np.tanh(drive*max(np.max(np.abs(x)),1e-9))  # soft-saturate, peak-normalised
    return y*CEIL
if __name__=="__main__":
  for k in sys.argv[1:]:
    x,sr=sf.read(f'tmp/{k}.wav'); x=x-np.mean(x)
    best=None
    for d in [0.5,1,1.5,2,3,4,6]:
        y=proc(x,d); sf.write('tmp/_t.wav',y,sr,subtype='FLOAT'); L=lufs('tmp/_t.wav')
        if best is None or abs(L+12)<abs(best[1]+12): best=(d,L,y)
        if L>=-12.5: break
    d,L,y=best; sf.write(f'tmp/{k}_n.wav',y,sr,subtype='FLOAT')
    print(k,'drive',d,'LUFS(repeat-measured)',round(L,1),'peak',round(20*np.log10(np.max(np.abs(y))),2))
