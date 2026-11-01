"""試聽合輯（PREVIEW，唔係遊戲資源）：sfx/_preview_ui8_all.ogg ＝ 全部 sfx_ui8_*（固定次序）每個之間 0.4 s 靜音。"""
import subprocess, numpy as np, soundfile as sf
ORDER = ['tap_a', 'tap_b', 'tab_switch_a', 'tab_switch_b', 'btn_press_a', 'btn_press_b', 'btn_sparkle', 'popup_open', 'popup_close', 'toast_in', 'coin', 'badge_wiggle',
         'transition_heart_close', 'transition_heart_open', 'confirm', 'cancel', 'error', 'toggle_on', 'toggle_off']
gap = np.zeros(int(.4 * 44100)); parts = []
for k in ORDER: x, sr = sf.read(f'sfx/sfx_ui8_{k}.ogg'); parts += [x, gap]
sf.write('/tmp/_prev_ui8.wav', np.concatenate(parts[:-1]), 44100, subtype='FLOAT')
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', '/tmp/_prev_ui8.wav', '-ac', '1', '-c:a', 'libvorbis', '-q:a', '4', '-fflags', '+bitexact', '-flags:a', '+bitexact', 'sfx/_preview_ui8_all.ogg'], check=True)
print('preview', sum(len(p) for p in parts[:-1]) / 44100, 's')
