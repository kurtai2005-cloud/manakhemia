"""tmp_new/<name>_n.wav → sfx/（stinger_entry、jingle_*、sfx_*）或 amb/（amb_*）ogg（Vorbis q5，44.1 kHz）。
聲道：stinger_entry、jingle_*、amb_* 立體聲；sfx_* 單聲道。編碼後即量度解碼結果：sample peak 或 TP > -1.05 dB 就降增益再編碼（最多 6 次）。
amb_wind_title 另外：解碼後 integrated 偏離 -24 LUFS 超過 0.25 就微調增益再編碼（最多 4 次）。"""
import glob, os, re, subprocess, numpy as np, soundfile as sf
FF = os.environ.get('FF', 'ffmpeg')
def ebur(p):
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1]), float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', o)[-1])
os.makedirs('sfx', exist_ok=True); os.makedirs('amb', exist_ok=True)
for f in sorted(glob.glob('tmp_new/*_n.wav')):
    b = os.path.basename(f)[:-6]; ch = 1 if b.startswith('sfx_') else 2; out = ('amb/' if b.startswith('amb_') else 'sfx/') + b + '.ogg'
    x, sr = sf.read(f); g = 1.0
    for it in range(8):
        sf.write('tmp_new/_e.wav', x * g, sr, subtype='FLOAT')
        subprocess.run([FF, '-y', '-v', 'error', '-i', 'tmp_new/_e.wav', '-ac', str(ch), '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '5', out], check=True)
        d, _ = sf.read(out); sp = 20 * np.log10(np.abs(d).max()); I, tp = ebur(out); worst = max(sp, tp)
        if worst > -1.05: g *= 10 ** ((-1.1 - worst) / 20); continue
        if b.startswith('amb_') and abs(I + 24) > 0.25: g *= 10 ** ((-24 - I) / 20); continue
        break
    print(out, 'extra gain dB', round(20 * np.log10(g), 2), 'decoded samplePeak', round(float(sp), 2), 'TP', tp, 'I(direct)', I)
