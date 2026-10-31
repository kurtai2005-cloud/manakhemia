"""方案 A SFX 響度歸一（純增益，無壓縮／失真）。用法：norm_pet2.py name:目標LUFS ...  （讀 tmp/<name>.wav → tmp/<name>_n.wav）
短音用「重複約 4 秒（間隔 0.1 s）」量；`*_loop` 用連續重複 3 次（無間隔）量。峰值上限 -2 dBFS（留位畀 ogg 過衝）。"""
import sys, subprocess, re, numpy as np, soundfile as sf
LCEIL = 10 ** (-2.0 / 20)
def lufs(x, sr, loop):
    if loop: y = np.tile(x, 3)
    else:
        gap = np.zeros(int(.1 * sr)); r = int(np.ceil(4 / (len(x) / sr + .1))); y = np.concatenate([np.concatenate([x, gap])] * r)
    sf.write('/tmp/_p2rep.wav', y, sr, subtype='FLOAT')
    o = subprocess.run(['/usr/bin/ffmpeg', '-hide_banner', '-nostats', '-i', '/tmp/_p2rep.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
for a in sys.argv[1:]:
    k, _, tg = a.partition(':'); T = float(tg); loop = k.endswith('_loop')
    x, sr = sf.read(f'tmp/{k}.wav'); x = x - np.mean(x)
    y = x / np.max(np.abs(x)) * LCEIL; L = lufs(y, sr, loop); g = min(1.0, 10 ** ((T - L) / 20)); y = y * g
    sf.write(f'tmp/{k}_n.wav', y, sr, subtype='FLOAT')
    print(f'{k:30s} target {T:6.1f}  result {L + 20 * np.log10(g):6.1f} LUFS  peak {20 * np.log10(np.max(np.abs(y))):6.2f}' + ('' if g < 1 else '  (峰值受限，未達目標)'))
