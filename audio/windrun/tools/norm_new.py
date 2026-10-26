"""新增 7 個音訊設響度：tmp_new/<name>.wav → tmp_new/<name>_n.wav。
短音（stinger／jingle／sfx）用「重複播放約 4 秒（間隔 0.1 s）」量度（同 norm.py 一致，近似值）；amb_wind_title（18 s）直接量整條。
先用純增益對準目標；若純增益令 sample peak > -1.5 dBFS，就用前置增益＋2 ms 前瞻限幅器（限幅量 ≤ 6 dB），到唔到目標如實印出。"""
import subprocess, re, numpy as np, soundfile as sf
from norm import lufs, limiter, CEIL, FFM
TARGETS = {'stinger_entry': -15.0, 'jingle_capture': -15.0, 'jingle_levelup': -15.0,
           'sfx_countdown_tick': -17.0, 'sfx_stamina_warn': -20.0, 'sfx_stamina_empty': -20.0, 'amb_wind_title': -24.0}
MAXGR = 6.0
def lufs_direct(path):
    o = subprocess.run([FFM, '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', o)[-1])
if __name__ == '__main__':
    for k, T in TARGETS.items():
        x, sr = sf.read(f'tmp_new/{k}.wav'); x = x - np.mean(x, axis=0); x0 = x / np.max(np.abs(x)); gr = 0.0
        meas = lufs_direct if k.startswith('amb_') else lufs
        sf.write('tmp_new/_t.wav', x0 * CEIL, sr, subtype='FLOAT'); L = meas('tmp_new/_t.wav')
        if L >= T: y = x0 * CEIL * 10 ** ((T - L) / 20)
        else:
            pre = 1.0
            for it in range(40):
                y, gr = limiter(x0 * CEIL * pre, sr=sr); sf.write('tmp_new/_t.wav', y, sr, subtype='FLOAT'); L2 = meas('tmp_new/_t.wav')
                if gr > MAXGR or L2 >= T - 0.2: break
                pre *= 10 ** (0.5 / 20)
        sf.write(f'tmp_new/{k}_n.wav', y, sr, subtype='FLOAT')
        print(k, 'target', T, 'LUFS', round(meas(f'tmp_new/{k}_n.wav'), 1), 'limiter GR dB', round(gr, 1), 'peak', round(20 * np.log10(np.max(np.abs(y))), 2))
