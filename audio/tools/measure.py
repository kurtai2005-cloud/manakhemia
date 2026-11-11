"""量度 ogg：格式、長度、integrated LUFS、true peak、sample peak。用法：measure.py [--sfx] files...
SFX（<3.5s）用重複 4 秒方式量 LUFS（同 norm.py 一致）；BGM 直接量。"""
import subprocess, re, sys, json, os, numpy as np, soundfile as sf
FF = os.environ.get('FF', 'ffmpeg'); FP = os.environ.get('FP', 'ffprobe')
def probe(p):
    j = json.loads(subprocess.run([FP, '-v', 'error', '-show_streams', '-show_format', '-of', 'json', p], capture_output=True, text=True).stdout)
    s = j['streams'][0]; return s['codec_name'], int(s['sample_rate']), int(s['channels']), float(j['format']['duration'])
def ebur(p):
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
def measure(p):
    codec, sr, ch, dur = probe(p); x, _ = sf.read(p); src = p
    if dur < 3.5:
        g = np.zeros((int(.1 * sr),) + x.shape[1:]); r = int(np.ceil(4 / (dur + .1)))
        sf.write('/tmp/_rep.wav', np.concatenate([np.concatenate([x, g])] * r), sr); src = '/tmp/_rep.wav'
    I, TP = ebur(src); sp = 20 * np.log10(np.max(np.abs(x)))
    return dict(file=os.path.basename(p), codec=codec, sr=sr, ch=ch, dur=round(dur, 3), size=os.path.getsize(p), LUFS=I, TP=TP, peak=round(float(sp), 2))
if __name__ == '__main__':
    for p in sys.argv[1:]:
        m = measure(p); print('{file:28s} {codec} {sr} ch={ch} {dur:7.3f}s {size:7d}B  I={LUFS:6.1f} LUFS  TP={TP:5.1f} dBTP  samplePeak={peak} dBFS'.format(**m))
