"""量度環境聲（立體聲 ogg，解碼後）：格式、樣本數、LUFS／TP、頻帶能量比、頻譜重心、循環接縫（*_loop）、淡入淡出（*_short）。
用法：measure_amb.py amb/*.ogg"""
import sys, os, numpy as np, soundfile as sf
from measure import probe, ebur
BAR = 240 / 68
BANDS = [(0, 150), (150, 400), (400, 1500), (1500, 3000), (3000, 6000), (6000, 22050)]
# v2（2026-10-31）：加遊測量法頻段（單聲道平均 FFT 功率；可重疊）：<250 / 250–400 / 400–1500 / 1–8k / 2–6k / >8k
BANDS2 = [(0, 250), (250, 400), (400, 1500), (1000, 8000), (2000, 6000), (8000, 22051)]
for p in sys.argv[1:]:
    codec, sr, ch, dur = probe(p); x, _ = sf.read(p); N = len(x); I, TP = ebur(p)
    m = x.mean(axis=1); P = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(N, 1 / sr)
    cen = np.sum(f * P) / np.sum(P); fr = [P[(f >= a) & (f < b)].sum() / P.sum() * 100 for a, b in BANDS]
    corr = np.corrcoef(x[:, 0], x[:, 1])[0, 1]
    print(f'{os.path.basename(p)}: {codec} {sr} Hz ch={ch} samples={N} ({N / sr:.3f} s, {N / sr / BAR:.3f} bars) I={I} LUFS TP={TP} dBTP '
          f'peak={20 * np.log10(np.abs(x).max()):.2f} dBFS centroid={cen:.0f} Hz L/R corr={corr:.2f} size={os.path.getsize(p)} B')
    print('   band % ' + '  '.join(f'{a}-{b}:{v:.1f}' for (a, b), v in zip(BANDS, fr)))
    print('   QA band % ' + '  '.join(f'{a}-{b}:{P[(f >= a) & (f < b)].sum() / P.sum() * 100:.1f}' for a, b in BANDS2))
    if '_loop' in p:
        d = np.abs(np.diff(x, axis=0)); seam = np.abs(x[0] - x[-1]); p999 = np.percentile(d, 99.9, axis=0)
        w = int(.05 * sr); rb = np.sqrt((x[-w:] ** 2).mean()); ra = np.sqrt((x[:w] ** 2).mean())
        print(f'   seam_diff L,R={seam[0]:.5f},{seam[1]:.5f}  p99.9_diff={p999[0]:.5f},{p999[1]:.5f}  max_diff={d.max():.5f}  rms50ms before/after={rb:.5f}/{ra:.5f}')
    if '_short' in p:
        def db(a, b): s = x[int(a * sr):int(b * sr)]; return 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-12)
        print(f'   RMS dBFS 0-0.1s={db(0, .1):.1f} 0.7-0.8s={db(.7, .8):.1f} 1.5-4.0s={db(1.5, 4.0):.1f} 5.0-5.5s={db(5, 5.5):.1f} 5.9-6.0s={db(5.9, 6):.1f}  first/last sample={np.abs(x[0]).max():.5f}/{np.abs(x[-1]).max():.5f}')
