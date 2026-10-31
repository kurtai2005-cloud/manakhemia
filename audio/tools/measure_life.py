"""量度團絨生命感 16 檔（解碼後 ogg）：格式、長度、LUFS4s（measure_pet2 方法：重複約 4 s、間隔 0.1 s）、
LUFS20（遊測：無間隔重複 20 次）、TP、sample peak、>4 kHz 能量比、首 5 ms 峰值、尾 10 ms 峰值。用法：measure_life.py files..."""
import sys, os, numpy as np, soundfile as sf
from measure import probe, ebur
def rep(x, sr, gap):
    g = np.zeros(int(gap * sr)); r = int(np.ceil(4 / (len(x) / sr + gap))); return np.concatenate([np.concatenate([x, g])] * r)
db = lambda v: 20 * np.log10(max(v, 1e-12))
print(f'{"file":28s} {"codec":7s} sr  ch  dur(s) LUFS4s LUFS20  TP   peak  >4k%  head5ms tail10ms')
for p in sys.argv[1:]:
    codec, sr, ch, dur = probe(p); x, _ = sf.read(p)
    sf.write('/tmp/_ml4.wav', rep(x, sr, .1), sr, subtype='FLOAT'); L4, TP = ebur('/tmp/_ml4.wav')
    sf.write('/tmp/_ml20.wav', np.tile(x, 20), sr, subtype='FLOAT'); L20 = ebur('/tmp/_ml20.wav')[0]
    X = np.abs(np.fft.rfft(x)) ** 2; f = np.fft.rfftfreq(len(x), 1 / sr); hi = 100 * X[f > 4000].sum() / X.sum()
    h = db(np.max(np.abs(x[:int(.005 * sr)]))); t = db(np.max(np.abs(x[-int(.01 * sr):])))
    print(f'{os.path.basename(p)[:-4]:28s} {codec:7s} {sr} {ch} {dur:6.3f} {L4:6.1f} {L20:6.1f} {TP:5.1f} {db(np.max(np.abs(x))):6.2f} {hi:5.2f} {h:7.1f} {t:7.1f}')
