"""驗證全部輸出（解碼後 ogg）：格式、長度、LUFS/TP/sample peak、起音時間（音畫同步）、BGM 循環接縫、切換試聽檔。
用法（喺 windrun-audio/）：PYTHONPATH=tools python tools/verify.py [--json out.json]"""
import glob, os, sys, json, numpy as np, soundfile as sf, subprocess
from measure import measure, probe
FF = os.environ.get('FF', 'ffmpeg')
SR = 44100
def onset(x, thr_db=-30):
    """起音：第一個絕對值超過 (峰值 -30 dB 相對) 嘅樣本時間 (ms)；以及峰值位置 (ms)"""
    m = np.abs(x) if x.ndim == 1 else np.abs(x).max(1); pk = m.max(); i = int(np.argmax(m > pk * 10 ** (thr_db / 20)))
    return 1000 * i / SR, 1000 * int(np.argmax(m)) / SR
def loop_check(p, bpm, nbar):
    x, sr = sf.read(p); n = int(round(nbar * 4 * 60 / bpm * sr)); d = np.abs(np.diff(x, axis=0)).max(1)
    seam = max(np.abs(x[0] - x[-1]).max(), 0)          # 末樣本→首樣本（循環）嘅差
    r = lambda a: float(np.sqrt(np.mean(a ** 2)))
    w = int(.05 * sr); pre, post = r(x[-w:]), r(x[:w])
    # 模擬循環兩圈，睇接縫附近一階差分最大值
    y = np.concatenate([x[-2000:], x[:2000]]); ds = np.abs(np.diff(y, axis=0)).max(1)
    ok_len = len(x) == n
    return dict(samples=len(x), expected=n, len_ok=ok_len, seam_diff=round(float(seam), 4), p999_diff=round(float(np.percentile(d, 99.9)), 4),
                max_diff=round(float(d.max()), 4), seam_max_diff=round(float(ds.max()), 4), rms_pre50ms=round(r(pre), 4) if False else round(pre, 4), rms_post50ms=round(post, 4))
def switch_demo(main, final, bpm_main=128, bpm_final=144, switch_bar=7, xf=0.3, out='tmp/switch_demo.wav'):
    """按 README 嘅切換做法拼一條：主循環播到第 switch_bar 小節線，末段循環以「提早 xf 秒、由其尾段開始」淡入，downbeat 對齊小節線。"""
    a, _ = sf.read(main); b, _ = sf.read(final); bar_a = 4 * 60 / bpm_main; T = switch_bar * bar_a; nT = int(round(T * SR)); nx = int(xf * SR)
    La = np.concatenate([a, a]); y_main = La[:nT + 2 * SR].copy()
    y = np.zeros((nT + 2 * SR + len(b) * 2, 2)); y[:len(y_main)] = y_main
    t = np.linspace(0, np.pi / 2, nx)[:, None]
    y[nT - nx:nT] = y[nT - nx:nT] * np.cos(t) + b[-nx:] * np.sin(t)       # 淡出主、淡入末段（其尾 xf 秒）
    y[nT:nT + 2 * len(b)] = np.concatenate([b, b])[:len(y) - nT]; y = y[:nT + 2 * len(b)]
    os.makedirs(os.path.dirname(out), exist_ok=True); sf.write(out, y, SR, subtype='FLOAT')
    d = np.abs(np.diff(y[nT - nx - 200:nT + 200], axis=0)).max(); pk = 20 * np.log10(np.abs(y).max())
    return dict(switch_s=round(T, 3), peak_dbfs=round(float(pk), 2), max_step_near_switch=round(float(d), 4))
if __name__ == '__main__':
    res = {}; fmt = '{file:26s} {codec} {sr} ch={ch} {dur:7.3f}s {size:7d}B  I={LUFS:6.1f} LUFS  TP={TP:5.1f} dBTP  samplePeak={peak:6.2f} dBFS  onset={onset_ms:5.1f}ms peakAt={peak_ms:6.1f}ms'
    tot = 0
    for p in sorted(glob.glob('bgm/*.ogg')) + sorted(glob.glob('sfx/*.ogg')):
        m = measure(p); x, _ = sf.read(p); on, pk = onset(x); m.update(onset_ms=on, peak_ms=pk); res[m['file']] = m; tot += m['size']; print(fmt.format(**m))
    print('total bytes', tot, '(%.2f MB)' % (tot / 1e6)); res['_total_bytes'] = tot
    for name, bpm, nb in (('bgm_race_loop', 128, 20), ('bgm_race_final_loop', 144, 12)):
        c = loop_check(f'bgm/{name}.ogg', bpm, nb); res[name + '_loop'] = c; print(name, c)
    if os.path.isdir('tmp') or True:
        s = switch_demo('bgm/bgm_race_loop.ogg', 'bgm/bgm_race_final_loop.ogg'); res['switch_demo'] = s; print('switch_demo', s)
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1, default=float)
