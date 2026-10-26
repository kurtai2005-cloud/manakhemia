"""標準化：把 tmp/<name>.wav 設到目標響度，輸出 tmp/<name>_n.wav。
響度用「重複播放約 4 秒（每次間隔 0.1 秒）」量度（短音 gated 響度計唔穩定；同《微光小圃》一致，係近似值）。
用法：norm.py [--linear|--limit] name[:targetLUFS] ...
  --linear  純增益（峰值上限 -2 dBFS）。
  --limit   前置增益＋前瞻式限幅器（上限 -1.5 dBFS，lookahead 2 ms、release 40 ms，限幅量 ≤ MAXGR（9）dB）；用於瞬態重、crest factor 大嘅短音，
            唔經飽和失真（比 tanh 乾淨）。到唔到目標會如實印出實測值同限幅量。"""
import subprocess, re, sys, numpy as np, soundfile as sf
from scipy.ndimage import minimum_filter1d, uniform_filter1d
FFM = '/usr/bin/ffmpeg'
def lufs(path):
    x, sr = sf.read(path); gap = np.zeros((int(.1 * sr),) + x.shape[1:]); r = int(np.ceil(4 / (len(x) / sr + .1)))
    sf.write('/tmp/_race_rep.wav', np.concatenate([np.concatenate([x, gap])] * r), sr)
    o = subprocess.run([FFM, '-hide_banner', '-nostats', '-i', '/tmp/_race_rep.wav', '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
CEIL = 10 ** (-1.5 / 20); LCEIL = 10 ** (-2.0 / 20); MAXGR = 9.0
def limiter(x, ceil=CEIL, sr=44100, look=0.002, rel=0.04):
    a = np.abs(x) if x.ndim == 1 else np.abs(x).max(1); need = np.minimum(1.0, ceil / (a + 1e-12)); n = max(1, int(look * sr))
    g = uniform_filter1d(minimum_filter1d(need, 2 * n + 1), n + 1); g = np.minimum(g, need) if False else g
    k = 1 - np.exp(-1 / (rel * sr)); out = np.empty_like(g); prev = 1.0
    for i in range(len(g)):
        prev = min(g[i], prev + (1 - prev) * k); out[i] = prev
    y = x * (out if x.ndim == 1 else out[:, None]); return np.clip(y, -ceil, ceil), float(-20 * np.log10(out.min()))
if __name__ == "__main__":
    args = sys.argv[1:]; mode = 'linear' if args and args[0] == '--linear' else 'limit' if args and args[0] == '--limit' else None
    if mode: args = args[1:]
    mode = mode or 'linear'
    for a in args:
        k, _, tg = a.partition(':'); T = float(tg) if tg else -13.0
        x, sr = sf.read(f'tmp/{k}.wav'); x = x - np.mean(x, axis=0)
        if mode == 'linear':
            y = x / np.max(np.abs(x)) * LCEIL; sf.write('tmp/_t.wav', y, sr, subtype='FLOAT'); L = lufs('tmp/_t.wav')
            g = min(1.0, 10 ** ((T - L) / 20)); y = y * g; sf.write(f'tmp/{k}_n.wav', y, sr, subtype='FLOAT')
            print(k, 'linear target', T, 'LUFS(repeat-measured)', round(L + 20 * np.log10(g), 1), 'peak', round(20 * np.log10(np.max(np.abs(y))), 2)); continue
        x0 = x / np.max(np.abs(x)); best = None; pre = 1.0
        for it in range(30):                       # 逐步加前置增益，直到到目標或限幅量 > MAXGR
            y, gr = limiter(x0 * CEIL * pre, sr=sr); sf.write('tmp/_t.wav', y, sr, subtype='FLOAT'); L = lufs('tmp/_t.wav')
            if gr > MAXGR and best is not None: break
            best = (y, L, gr, pre)
            if L >= T - 0.3: break
            pre *= 10 ** (min(3.0, max(0.5, (T - L) * 0.6)) / 20)
        y, L, gr, pre = best; sf.write(f'tmp/{k}_n.wav', y, sr, subtype='FLOAT')
        print(k, 'limit target', T, 'LUFS(repeat-measured)', round(L, 1), 'max gain reduction dB', round(gr, 1), 'peak', round(20 * np.log10(np.max(np.abs(y))), 2))
