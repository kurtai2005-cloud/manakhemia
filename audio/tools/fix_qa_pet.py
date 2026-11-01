"""依遊測審查 2026-10-26 修正（QA/audio-review-pet-sfx.md §3、§4）。純增益＋grumpy 起音淡入，無 limiter／失真。
喺 audio/ 執行：PYTHONPATH=tools python3 tools/fix_qa_pet.py
① sfx_event_dream_talk  -7 dB      ② sfx_pet_grumpy  每下「噗」起音 13 ms 餘弦淡入＋整體 -1.5 dB
③ sfx_tap/confirm/hit/cancel/error  純增益至循環等效 ≈ -13.5 LUFS（≤ -13.3＝全 SFX 中位數 -15.3 +2 LU）
舊檔先備份到 _prev/（只備份一次；之後一律由 _prev/ 讀入，所以重跑結果相同）。其他檔（含 shiny_day、uncomfortable）不動。"""
import os, shutil, subprocess, numpy as np, soundfile as sf
from measure import measure, ebur
def lufs20(path):
    """遊測「循環等效 LUFS」：解碼後無間隔重複 20 次再 ebur128（全 SFX 中位數 -15.3 LUFS 就係用呢個方法量）。"""
    x, sr = sf.read(path); sf.write('/tmp/_q20.wav', np.tile(x, 20), sr, subtype='FLOAT'); return ebur('/tmp/_q20.wav')[0]
FF = os.environ.get('FF', 'ffmpeg'); SR = 44100
os.makedirs('_prev', exist_ok=True); os.makedirs('tmp', exist_ok=True)
TARGET_UI = -13.5
def onsets(x, thr=10 ** (-60 / 20), gap=int(.02 * SR)):
    """靜音（<-60 dBFS 連續 ≥20 ms）之後嘅第一個有聲樣本；檔頭亦計。"""
    on = [0]; quiet = 0; i = 0; a = np.abs(x)
    while i < len(x):
        if a[i] < thr: quiet += 1
        else:
            if quiet >= gap: on.append(i)
            quiet = 0
        i += 1
    return on
def rms2(x, w=int(.002 * SR)):
    return np.sqrt(np.convolve(x ** 2, np.ones(w) / w, 'same'))
def fade_in(x, ms=13, pre=3, floor=.1):
    """每下「噗」嘅「響亮起升」前 pre ms 起，加 ms 長嘅餘弦淡入（增益 floor→1）。
    舊檔每下 pulse 前有一段約 -30 dBFS 嘅 puff 前奏，之後先喺約 10 ms 內升到滿位（9 ms 起音）；淡入放喺呢段起升上面，
    起升前嘅前奏只係按 floor（-20 dB）細聲，增益連續、冇 click。起升點＝2 ms RMS 首次到該下 pulse 峰值 20%（前奏約 12–15%，唔會誤判）。"""
    y = x.copy(); n = int(round(ms / 1000 * SR)); r = rms2(x); ons = onsets(x) + [len(x)]
    for k in range(len(ons) - 1):
        o, e = ons[k], ons[k + 1]
        pk = r[o:e].max(); t10 = o + int(np.argmax(r[o:e] >= .2 * pk)); ts = max(o, t10 - int(pre / 1000 * SR))
        g = np.ones(e - o); g[:ts - o] = floor
        m = min(n, e - ts); g[ts - o:ts - o + m] = floor + (1 - floor) * (0.5 - 0.5 * np.cos(np.pi * np.arange(m) / n))
        y[o:e] = x[o:e] * g
    return y
def enc(x, name):
    sf.write(f'tmp/{name}_f.wav', x, SR, subtype='FLOAT')
    subprocess.run([FF, '-y', '-v', 'error', '-i', f'tmp/{name}_f.wav', '-ac', '1', '-ar', '44100', '-c:a', 'libvorbis', '-q:a', '3', f'sfx/{name}.ogg'], check=True)
def load(name):
    if not os.path.exists(f'_prev/{name}.ogg'): shutil.copy(f'sfx/{name}.ogg', f'_prev/{name}.ogg')
    x, sr = sf.read(f'_prev/{name}.ogg'); assert sr == SR; return x
db = lambda d: 10 ** (d / 20)
log = []
def run(name, make, target=None):
    old = measure(f'_prev/{name}.ogg') if os.path.exists(f'_prev/{name}.ogg') else measure(f'sfx/{name}.ogg')
    x = load(name); y = make(x); extra = 0.0
    for _ in range(4):                       # 純增益微調（ogg 重編碼令響度差 ≤0.1 LU）
        enc(y * db(extra), name); new = measure(f'sfx/{name}.ogg'); new['L20'] = lufs20(f'sfx/{name}.ogg')
        if target is None or abs(new['L20'] - target) <= 0.15: break
        extra += target - new['L20']
    old['L20'] = lufs20(f'_prev/{name}.ogg'); log.append((name, old, new)); return new
run('sfx_event_dream_talk', lambda x: x * db(-7))
run('sfx_pet_grumpy', lambda x: fade_in(x, 13) * db(-1.5))
for n in ['sfx_tap', 'sfx_confirm', 'sfx_hit', 'sfx_cancel', 'sfx_error']:
    load(n); I0 = lufs20(f'_prev/{n}.ogg')
    g = TARGET_UI - I0; run(n, lambda x, g=g: x * db(g), TARGET_UI)
shutil.rmtree('tmp', ignore_errors=True)
print('LUFS20＝遊測循環等效（20×無間隔）；LUFS4s＝measure_pet2 方法（重複約 4 s、間隔 0.1 s）')
print(f'{"file":24s} {"dur":>13s} {"LUFS20":>13s} {"LUFS4s":>13s} {"TP":>13s} {"peak":>13s}')
for n, o, w in log:
    print(f'{n:24s} {o["dur"]:6.3f}->{w["dur"]:6.3f} {o["L20"]:6.1f}->{w["L20"]:6.1f} {o["LUFS"]:6.1f}->{w["LUFS"]:6.1f} {o["TP"]:6.1f}->{w["TP"]:6.1f} {o["peak"]:6.2f}->{w["peak"]:6.2f}  Δ{w["L20"] - o["L20"]:+.2f} LU')
