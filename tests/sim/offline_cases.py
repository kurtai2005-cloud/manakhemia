#!/usr/bin/env python3
"""offline_cases.py — 《微光小圃》離線推算「參考答案」生成器（對應 test-plan 第 1 節）
按 pet-one-pager 第 7 節：E = min(T,8h)×100% + min(max(T−8h,0),16h)×25%；超過 24h 不計；保底 20；便便按 E 計（每 3h +1，上限 3，每個令清潔衰減 +1/h）。
假設：離線全程「清醒」（唔考慮睡眠 ×0.3）；起始便便 0；全部需求喺保底前線性衰減。
用法：python3 offline_cases.py  → 印出 Markdown 表（驗收時對比實機／單元測試輸出，容差 ±1）
"""
D = dict(hunger=6.0, mood=4.0, clean=3.0, energy=5.0)
FLOOR, POOP_EVERY, POOP_CAP, POOP_EXTRA = 20.0, 3.0, 3, 1.0

def eff(T):
    if T <= 0: return 0.0
    return min(T, 8.0) + 0.25 * min(max(T - 8.0, 0.0), 16.0)

def apply(start, T, decay=D, floor=FLOOR, poops0=0):
    E = eff(T); s = dict(start); poops = poops0; t = 0.0; step = 0.01
    pt = 0.0
    while t < E - 1e-9:
        dt = min(step, E - t)
        old = dict(s)
        for k in s:
            r = decay[k] + (POOP_EXTRA * poops if k == 'clean' else 0)
            s[k] = max(s[k] - r * dt, min(old[k], floor))
        pt += dt
        if pt >= POOP_EVERY: pt -= POOP_EVERY; poops = min(POOP_CAP, poops + 1)
        t += dt
    return E, s, poops

CASES = [0, 1, 4, 8, 9, 12, 24, 25, 72, 24 * 30]
if __name__ == '__main__':
    full = dict(hunger=100, mood=100, clean=100, energy=100)
    low = dict(hunger=40, mood=40, clean=40, energy=40)
    for name, st in (('起始全 100', full), ('起始全 40（驗保底）', low)):
        print('\n**%s**\n' % name)
        print('| 離線 T | 有效 E | 飽腹 | 心情 | 清潔 | 精力 | 便便 |\n|---|---|---|---|---|---|---|')
        for T in CASES:
            E, s, p = apply(st, T)
            print('| %gh | %.2fh | %.0f | %.0f | %.0f | %.0f | %d |' % (T, E, s['hunger'], s['mood'], s['clean'], s['energy'], p))
    print('\n**成長值（離線 50%）**：E×50% → T=24h 時 = 6.0 小時等值；T=72h 同 24h 一樣\n')
