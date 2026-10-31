"""量度時段 BGM（立體聲，解碼後 ogg）：格式、樣本數、小節數、LUFS／TP、循環接縫。用法：measure_tod.py bgm/bgm_care_*_loop.ogg"""
import sys, os, numpy as np, soundfile as sf
from measure import probe, ebur
BAR = 240 / 68
for p in sys.argv[1:]:
    codec, sr, ch, dur = probe(p); x, _ = sf.read(p); N = len(x)
    I, TP = ebur(p); d = np.abs(np.diff(x, axis=0)); seam = np.abs(x[0] - x[-1]); p999 = np.percentile(d, 99.9, axis=0)
    w = int(.05 * sr); rb = np.sqrt((x[-w:] ** 2).mean()); ra = np.sqrt((x[:w] ** 2).mean())
    print(f'{os.path.basename(p):28s} {codec} {sr} ch={ch} samples={N} {N / sr:7.3f}s bars={N / sr / BAR:.3f}  I={I:6.1f} LUFS TP={TP:5.1f} dBTP  '
          f'seam_diff(L,R)={seam[0]:.5f},{seam[1]:.5f} p99.9_diff={p999[0]:.5f},{p999[1]:.5f}  rms50ms before/after seam={rb:.4f}/{ra:.4f}')
