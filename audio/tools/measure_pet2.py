"""量度方案 A 新檔（解碼後 ogg）。短音：重複 4 s 量 LUFS；*_loop：連續 3 次（無間隔）量 LUFS ＋ 檢查接縫。用法：measure_pet2.py files..."""
import sys, os, numpy as np, soundfile as sf
from measure import probe, ebur
for p in sys.argv[1:]:
    codec, sr, ch, dur = probe(p); x, _ = sf.read(p); loop = p.endswith('_loop.ogg')
    if loop: y = np.tile(x, 3)
    else:
        g = np.zeros(int(.1 * sr)); r = int(np.ceil(4 / (dur + .1))); y = np.concatenate([np.concatenate([x, g])] * r)
    sf.write('/tmp/_m2.wav', y, sr, subtype='FLOAT'); I, TP = ebur('/tmp/_m2.wav')
    extra = ''
    if loop:
        d = np.abs(np.diff(x)); seam = abs(x[0] - x[-1]); extra = f'  samples={len(x)} seam_diff={seam:.5f} p99.9_diff={np.percentile(d, 99.9):.5f}'
    print(f'{os.path.basename(p):32s} {codec} {sr} ch={ch} {dur:6.3f}s  I={I:6.1f} LUFS  TP={TP:5.1f} dBTP  samplePeak={20 * np.log10(np.max(np.abs(x))):6.2f} dBFS{extra}')
