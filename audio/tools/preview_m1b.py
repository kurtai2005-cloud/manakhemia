"""試聽合輯（PREVIEW，唔入遊戲）：sfx/_preview_m1b.ogg
＝全部 M1b 新 SFX（固定次序）每個之間 0.45 s 靜音。"""
import os, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
ORDER = [
    "sfx_post_letter_send", "sfx_post_letter_receive",
    "sfx_kitchen_cook_start", "sfx_kitchen_stir", "sfx_kitchen_cook_done",
    "sfx_codex_page_flip_a", "sfx_codex_page_flip_b", "sfx_codex_new_entry",
    "sfx_furn_pickup", "sfx_furn_place_a", "sfx_furn_place_b", "sfx_furn_buy",
    "sfx_hunt_pounce_a", "sfx_hunt_pounce_b", "sfx_hunt_enter",
]
SR = 44100
gap = np.zeros(int(0.45 * SR))
parts = []
for k in ORDER:
    p = ROOT / "sfx" / f"{k}.ogg"
    x, sr = sf.read(str(p))
    if x.ndim > 1:
        x = np.mean(x, axis=1)
    parts += [x, gap]
wav = "/tmp/_preview_m1b.wav"
out = ROOT / "sfx" / "_preview_m1b.ogg"
sf.write(wav, np.concatenate(parts[:-1]), SR, subtype="FLOAT")
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-i", wav,
     "-ac", "1", "-ar", "44100", "-c:a", "libvorbis", "-q:a", "4",
     "-fflags", "+bitexact", "-flags:a", "+bitexact", str(out)],
    check=True,
)
print("preview", sum(len(p) for p in parts[:-1]) / SR, "s", "->", out)
