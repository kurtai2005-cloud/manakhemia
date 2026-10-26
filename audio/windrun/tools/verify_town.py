"""驗證晨苔鎮音訊（解碼後 ogg）：格式、長度、LUFS／TP／sample peak、起音、BGM 循環接縫（有 tmp/ 編碼前 wav 時加對比）、頻譜分佈、
blip 15/s 同腳步 2 步/秒 嘅實用響度。用法（喺 windrun-audio/）：PYTHONPATH=tools python tools/verify_town.py [--json out.json]
需要 tmp/bgm_town_morningmoss_loop.wav（gen_bgm_town.py 產生）先會做「編碼前後對比」；冇就略過該項。"""
import glob, os, sys, json, re, subprocess, tempfile, numpy as np, soundfile as sf
from scipy.signal import welch
from measure import measure
from verify import onset
FF = os.environ.get('FF', 'ffmpeg'); SR = 44100
BGM = 'bgm/bgm_town_morningmoss_loop.ogg'; BPM = 75; NBAR = 24
TOWN_SFX = ([f'sfx_step_{n}_{k}' for n in ('town_cobble', 'grass_path', 'wood_floor') for k in 'abc'] + [f'sfx_dialog_blip_{k}' for k in 'abc'] +
            ['sfx_dialog_open', 'sfx_dialog_next', 'sfx_dialog_close', 'sfx_interact_confirm', 'sfx_interact_door', 'sfx_menu_move',
             'sfx_register_open', 'sfx_register_confirm', 'sfx_register_denied', 'sfx_leafcoin_get', 'sfx_item_get', 'sfx_zone_enter'])
def ebur_arr(x, tmp):
    sf.write(tmp, x, SR, subtype='FLOAT')
    o = subprocess.run([FF, '-hide_banner', '-nostats', '-i', tmp, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
def train(clips, times, dur):
    y = np.zeros(int(dur * SR))
    for c, t in zip(clips, times):
        i = int(t * SR); y[i:i + len(c)] += c[:len(y) - i]
    return y
def main():
    res = {}; tmpf = tempfile.mktemp(suffix='.wav')
    fmt = '{file:32s} {codec} {sr} ch={ch} {dur:7.3f}s {size:7d}B  I={LUFS:6.1f} LUFS  TP={TP:5.1f} dBTP  samplePeak={peak:6.2f} dBFS  onset={onset_ms:5.1f}ms'
    bad = []
    for n in [BGM] + [f'sfx/{k}.ogg' for k in TOWN_SFX]:
        m = measure(n); x, _ = sf.read(n); on, pk = onset(x); m.update(onset_ms=round(on, 2), peak_ms=round(pk, 1)); res[m['file']] = m; print(fmt.format(**m))
        if m['peak'] > -1.0 or m['TP'] > -1.0: bad.append(m['file'])
        if n != BGM and (m['ch'] != 1 or m['sr'] != 44100 or m['codec'] != 'vorbis'): bad.append(m['file'] + ' format')
    if bad: print('!! 超標／格式錯誤:', bad)
    res['_fail'] = bad
    x, sr = sf.read(BGM); N = NBAR * 4 * 44100 * 60 // BPM; m = x.mean(1); d = np.abs(np.diff(x, axis=0)).max(1)
    ds = np.abs(np.diff(np.concatenate([x[-2000:], x[:2000]]), axis=0)).max(1)
    c = dict(samples=len(x), expected=N, len_ok=len(x) == N, stereo=x.shape[1] == 2, seam_diff=round(float(np.abs(x[0] - x[-1]).max()), 4), p999_diff=round(float(np.percentile(d, 99.9)), 4),
             max_diff=round(float(d.max()), 4), seam_max_diff=round(float(ds.max()), 4), rms_first50ms=round(float(np.sqrt(np.mean(x[:2205] ** 2))), 4), rms_last50ms=round(float(np.sqrt(np.mean(x[-2205:] ** 2))), 4))
    src = 'tmp/bgm_town_morningmoss_loop.wav'
    if os.path.exists(src):
        s, _ = sf.read(src); g = np.dot(x.ravel()[:2 ** 20], s.ravel()[:2 ** 20]) / np.dot(s.ravel()[:2 ** 20], s.ravel()[:2 ** 20]); e = (x - s * g)
        rr = lambda a, b: round(float(20 * np.log10(np.sqrt(np.mean(a ** 2)) / np.sqrt(np.mean(b ** 2)))), 1)
        c.update(src_len_equal=len(s) == len(x), codec_err_dB_head50ms=rr(e[:2205], (s * g)[:2205]), codec_err_dB_tail50ms=rr(e[-2205:], (s * g)[-2205:]),
                 codec_err_dB_whole=rr(e, s * g), src_seam_diff=round(float(np.abs(s[0] - s[-1]).max()), 4))
    c['loudness_2x_loop_I'] = ebur_arr(np.concatenate([x, x]), tmpf)
    f, p = welch(m, SR, nperseg=8192); tt_ = p.sum()
    c['band_share_pct'] = {k: round(100 * float(p[(f >= lo) & (f < hi)].sum() / tt_), 2) for k, (lo, hi) in {'<150': (0, 150), '150-1000': (150, 1000), '1000-4000': (1000, 4000), '4000-8000': (4000, 8000), '>8000': (8000, 30000)}.items()}
    res['bgm_loop'] = c; print('bgm_loop', c)
    use = {}
    for k in 'abc':
        b, _ = sf.read(f'sfx/sfx_dialog_blip_{k}.ogg'); use[f'blip_{k}_15ps_I'] = round(ebur_arr(train([b] * 60, np.arange(60) / 15.0, 4.2), tmpf), 1)
    rng = np.random.default_rng(1)
    for n in ('town_cobble', 'grass_path', 'wood_floor'):
        cl = [sf.read(f'sfx/sfx_step_{n}_{k}.ogg')[0] for k in 'abc']; seqc = [cl[i] for i in rng.integers(0, 3, 12)]
        use[f'step_{n}_2ps_I'] = round(ebur_arr(train(seqc, np.arange(12) * 0.5, 6.1), tmpf), 1)
    res['usage_loudness'] = use; print('usage', use)
    res['_total_bytes'] = sum(os.path.getsize(p) for p in glob.glob('**/*', recursive=True) if os.path.isfile(p) and not p.startswith('tmp')); print('dir total bytes (excl tmp)', res['_total_bytes'])
    if '--json' in sys.argv: json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1, default=float)
    if bad or not c['len_ok']: sys.exit(1)
if __name__ == '__main__': main()
