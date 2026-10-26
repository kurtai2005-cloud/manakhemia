"""晨苔鎮 SFX 設響度：tmp/<name>.wav → tmp/<name>_n.wav。每個檔一個目標 LUFS（重複播放約 4 秒、間隔 0.1 s 量度，近似值；同 norm.py 一致）。
同 norm.py 唔同：呢度**可以降細聲**（norm.py --limit 只升唔降）。先用純增益對準目標；若純增益要求 sample peak > -1.5 dBFS，
就用前置增益＋2 ms 前瞻限幅器（限幅量 ≤ 6 dB），到唔到目標如實印出實測值。用法：norm_town.py（目標寫喺 TARGETS）"""
import numpy as np, soundfile as sf
from norm import lufs, limiter, CEIL
TARGETS = {}
for k in 'abc':
    TARGETS.update({f'sfx_step_town_cobble_{k}': -24, f'sfx_step_grass_path_{k}': -25, f'sfx_step_wood_floor_{k}': -24, f'sfx_dialog_blip_{k}': -24})
TARGETS.update({'sfx_menu_move': -23, 'sfx_dialog_next': -22, 'sfx_dialog_open': -20, 'sfx_dialog_close': -20, 'sfx_interact_confirm': -20, 'sfx_interact_door': -19,
                'sfx_register_open': -19, 'sfx_register_confirm': -17, 'sfx_register_denied': -20, 'sfx_leafcoin_get': -19, 'sfx_item_get': -18, 'sfx_zone_enter': -19})
MAXGR = 6.0
if __name__ == '__main__':
    for k, T in TARGETS.items():
        x, sr = sf.read(f'tmp/{k}.wav'); x0 = x / np.max(np.abs(x)); gr = 0.0
        sf.write('tmp/_t.wav', x0 * CEIL, sr, subtype='FLOAT'); L = lufs('tmp/_t.wav')          # 峰值 -1.5 dBFS 時嘅響度
        if L >= T: y = x0 * CEIL * 10 ** ((T - L) / 20)                                           # 純增益（降細聲）
        else:
            pre = 1.0
            for it in range(30):
                y, gr = limiter(x0 * CEIL * pre, sr=sr); sf.write('tmp/_t.wav', y, sr, subtype='FLOAT'); L2 = lufs('tmp/_t.wav')
                if gr > MAXGR or L2 >= T - 0.2: break
                pre *= 10 ** (0.5 / 20)
        sf.write(f'tmp/{k}_n.wav', y, sr, subtype='FLOAT'); sf.write('tmp/_t.wav', y, sr, subtype='FLOAT')
        print(k, 'target', T, 'LUFS(repeat) ', round(lufs('tmp/_t.wav'), 1), 'limiter GR dB', round(gr, 1), 'peak', round(20 * np.log10(np.max(np.abs(y))), 2))
