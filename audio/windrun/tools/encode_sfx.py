"""tmp/<name>_n.wav → sfx/<name>.ogg（Vorbis q5）。Vorbis 解碼後會有 ≤~1.2 dB 過衝，所以每個檔編碼後即量度解碼結果：
若 sample peak 或 true peak > -1.05 dB，就按超出量降增益再編碼（最多 6 次），確保解碼後 peak／TP ≤ -1 dB。
聲道：finish_line／stinger 立體聲，其餘單聲道。"""
import glob, os, re, subprocess, sys, numpy as np, soundfile as sf
FF = os.environ.get('FF', 'ffmpeg')
def tp_of(p):
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
os.makedirs('sfx', exist_ok=True)
for f in sorted(glob.glob('tmp/sfx_*_n.wav')):
    b = os.path.basename(f)[:-6]; ch = 2 if b in ('sfx_finish_line',) or b.startswith('sfx_stinger_') else 1
    x, sr = sf.read(f); g = 1.0; out = f'sfx/{b}.ogg'
    for it in range(6):
        sf.write('tmp/_e.wav', x * g, sr, subtype='FLOAT')
        subprocess.run([FF, '-y', '-v', 'error', '-i', 'tmp/_e.wav', '-ac', str(ch), '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', out], check=True)
        d, _ = sf.read(out); sp = 20 * np.log10(np.abs(d).max()); tp = tp_of(out); worst = max(sp, tp)
        if worst <= -1.05: break
        g *= 10 ** ((-1.1 - worst) / 20)
    print(b, 'extra gain dB', round(20 * np.log10(g), 2), 'decoded samplePeak', round(float(sp), 2), 'TP', tp)
