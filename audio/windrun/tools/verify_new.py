"""驗證新增 7 個音訊（解碼後 ogg）：格式、長度、LUFS／TP／sample peak、起音、tick 音高、stinger 重拍位置、amb 無縫循環（樣本精確）。
用法（喺 windrun-audio/）：PYTHONPATH=tools python tools/verify_new.py [--json out.json]；有 tmp_new/amb_wind_title.wav 時加「編碼前後對比」。"""
import os, sys, json, re, subprocess, tempfile, numpy as np, soundfile as sf
from scipy.signal import welch
from measure import measure
from verify import onset
FF = os.environ.get('FF', 'ffmpeg'); SR = 44100
FILES = {'sfx/stinger_entry.ogg': (2, 3.0, 'jingle'), 'sfx/jingle_capture.ogg': (2, 2.0, 'jingle'), 'sfx/jingle_levelup.ogg': (2, 1.2, 'jingle'),
         'sfx/sfx_countdown_tick.ogg': (1, 0.2, 'sfx'), 'sfx/sfx_stamina_warn.ogg': (1, 0.5, 'sfx'), 'sfx/sfx_stamina_empty.ogg': (1, 0.5, 'sfx'),
         'amb/amb_wind_title.ogg': (2, 18.0, 'amb')}
def ebur_arr(x, tmp):
    sf.write(tmp, x, SR, subtype='FLOAT')
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', tmp, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
def main():
    res = {}; bad = []; tmpf = tempfile.mktemp(suffix='.wav')
    fmt = '{file:24s} {codec} {sr} ch={ch} {dur:7.3f}s {size:7d}B  I={LUFS:6.1f} LUFS  TP={TP:5.1f} dBTP  samplePeak={peak:6.2f} dBFS  onset={onset_ms:6.1f}ms'
    for p, (ch, lim, kind) in FILES.items():
        m = measure(p); x, _ = sf.read(p); on, pk = onset(x); m.update(onset_ms=round(on, 2), peak_ms=round(pk, 1)); res[m['file']] = m; print(fmt.format(**m))
        if m['ch'] != ch or m['sr'] != 44100 or m['codec'] != 'vorbis': bad.append(m['file'] + ' format')
        if kind != 'amb' and m['dur'] > lim + 0.001: bad.append(m['file'] + ' too long')
        if kind != 'amb' and (m['peak'] > -1.0 or m['TP'] > -1.0): bad.append(m['file'] + ' peak/TP')
        if kind == 'jingle' and not (-16.05 <= m['LUFS'] <= -13.95): bad.append(m['file'] + ' LUFS')
        if kind == 'amb' and abs(m['LUFS'] + 24) > 0.5: bad.append(m['file'] + ' LUFS')
    # tick 音高：解碼後頻譜主峰
    x, _ = sf.read('sfx/sfx_countdown_tick.ogg'); w = x * np.hanning(len(x)); N = 2 ** 18; S = np.abs(np.fft.rfft(w, N)); f = np.fft.rfftfreq(N, 1 / SR); i = int(np.argmax(S * (f > 200)))
    res['tick_peak_hz'] = round(float(f[i]), 1); res['tick_peak_midi'] = round(float(12 * np.log2(f[i] / 440) + 69), 2); print('tick 主峰', res['tick_peak_hz'], 'Hz = MIDI', res['tick_peak_midi'], '（D5=587.3 Hz，GO 和弦含 D5）')
    # stinger：128 BPM 重拍 1.875 s 附近嘅能量上升；結尾 0.2 s RMS（應已淡出）
    x, _ = sf.read('sfx/stinger_entry.ogg'); m = x.mean(1); env = lambda a: float(np.sqrt(np.mean(a ** 2)))
    w = int(.05 * SR); b2 = int(1.875 * SR)
    res['stinger'] = dict(rms_before_bar2_50ms=round(env(m[b2 - w:b2]), 4), rms_after_bar2_50ms=round(env(m[b2:b2 + w]), 4), rms_last200ms=round(env(m[-int(.2 * SR):]), 4), rms_1_5s_to_1_875s=round(env(m[int(1.5 * SR):b2]), 4))
    print('stinger', res['stinger'])
    # 低頻 SFX：能量分佈（細喇叭可聽性）
    for n in ('sfx_stamina_warn', 'sfx_stamina_empty'):
        x, _ = sf.read(f'sfx/{n}.ogg'); f_, p_ = welch(x, SR, nperseg=2048); t_ = p_.sum()
        res[n + '_band_pct'] = {k: round(100 * float(p_[(f_ >= lo) & (f_ < hi)].sum() / t_), 1) for k, (lo, hi) in {'<100': (0, 100), '100-300': (100, 300), '300-1000': (300, 1000), '>1000': (1000, 30000)}.items()}; print(n, res[n + '_band_pct'])
    # amb 循環
    x, _ = sf.read('amb/amb_wind_title.ogg'); N = 18 * SR; d = np.abs(np.diff(x, axis=0)).max(1)
    ds = np.abs(np.diff(np.concatenate([x[-2000:], x[:2000]]), axis=0)).max(1); seam = float(np.abs(x[0] - x[-1]).max())
    c = dict(samples=len(x), expected=N, len_ok=len(x) == N, stereo=x.shape[1] == 2, seam_diff=round(seam, 5), p999_diff=round(float(np.percentile(d, 99.9)), 5), max_diff=round(float(d.max()), 5),
             seam_max_diff=round(float(ds.max()), 5), seam_step_at_wrap=round(float(ds[1999]), 5), rms_first50ms=round(float(np.sqrt(np.mean(x[:2205] ** 2))), 4), rms_last50ms=round(float(np.sqrt(np.mean(x[-2205:] ** 2))), 4))
    # 解碼後 wrap 處一階差分 vs 該處「循環內部同位置」嘅典型差分（相鄰 100 個 wrap 差分嘅 RMS 對比）
    wrap_step = np.abs(x[0] - x[-1]).max(); typ = np.abs(np.diff(x[N // 2:N // 2 + 20000], axis=0)).max(1)
    c['wrap_step_vs_typical_p99'] = round(float(wrap_step / np.percentile(typ, 99)), 3)
    src = 'tmp_new/amb_wind_title_n.wav'
    if os.path.exists(src):
        s, _ = sf.read(src); g = np.dot(x.ravel()[:2 ** 20], s.ravel()[:2 ** 20]) / np.dot(s.ravel()[:2 ** 20], s.ravel()[:2 ** 20]); e = x - s * g
        rr = lambda a, b: round(float(20 * np.log10(np.sqrt(np.mean(a ** 2)) / np.sqrt(np.mean(b ** 2)))), 1)
        c.update(src_len_equal=len(s) == len(x), src_seam_diff=round(float(np.abs(s[0] - s[-1]).max()), 5), src_wrap_step_p99_ratio=round(float(np.abs(s[0] - s[-1]).max() / np.percentile(np.abs(np.diff(s[N // 2:N // 2 + 20000], axis=0)).max(1), 99)), 3),
                 codec_err_dB_head50ms=rr(e[:2205], (s * g)[:2205]), codec_err_dB_tail50ms=rr(e[-2205:], (s * g)[-2205:]), codec_err_dB_whole=rr(e, s * g))
    c['loudness_2x_loop_I'] = ebur_arr(np.concatenate([x, x]), tmpf)
    f_, p_ = welch(x.mean(1), SR, nperseg=8192); t_ = p_.sum()
    c['band_share_pct'] = {k: round(100 * float(p_[(f_ >= lo) & (f_ < hi)].sum() / t_), 2) for k, (lo, hi) in {'<150': (0, 150), '150-1000': (150, 1000), '1000-4000': (1000, 4000), '>4000': (4000, 30000)}.items()}
    # 響度穩定度：3 s 短期響度範圍（gust 起伏）
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', 'amb/amb_wind_title.ogg', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m_ = re.search(r'LRA:\s+([\d.]+) LU', o); c['LRA_LU'] = float(m_.group(1)) if m_ else None
    # 左右相關
    c['LR_corr'] = round(float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]), 3)
    res['amb_loop'] = c; print('amb_loop', c)
    if not c['len_ok'] or c['wrap_step_vs_typical_p99'] > 1.5: bad.append('amb loop')
    res['_fail'] = bad
    if bad: print('!! 超標／格式錯誤:', bad)
    else: print('全部通過')
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1, default=float)
    if bad: sys.exit(1)
if __name__ == '__main__': main()
