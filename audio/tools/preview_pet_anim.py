"""試聽合輯（PREVIEW，唔係遊戲資源）：sfx/_preview_pet_anim.ogg
＝ anim 動作音（新 foley ＋本次用到嘅現有檔）固定次序，每個之間 0.4 s 靜音。"""
import subprocess, numpy as np, soundfile as sf
ORDER = [
    "sfx_pet_step_walk_a", "sfx_pet_step_walk_b",
    "sfx_pet_jump_a", "sfx_pet_jump_b",
    "sfx_pet_step_hop_a", "sfx_pet_step_hop_b",
    "sfx_pet_grass_rustle_a", "sfx_pet_grass_rustle_b",
    "sfx_pet_letter_drop_a", "sfx_pet_letter_drop_b",
    "sfx_pet_clap_a", "sfx_pet_clap_b",
    "sfx_pet_pickup_a", "sfx_pet_pickup_b",
    "sfx_pet_place_a", "sfx_pet_place_b",
    "sfx_pet_reach_a", "sfx_pet_reach_b",
    "sfx_pet_stretch_a", "sfx_pet_stretch_b",
    "sfx_pet_proud_a", "sfx_pet_proud_b",
    "sfx_pet_point_a", "sfx_pet_point_b",
    "sfx_pet_scratch_a", "sfx_pet_scratch_b",
    "sfx_pet_happy", "sfx_pet_yawn",
    "sfx_critter_startle_a", "sfx_critter_startle_b",
    "sfx_critter_shake_a", "sfx_critter_shake_b",
    "sfx_critter_transform_a", "sfx_critter_transform_b",
    "sfx_critter_roll_a", "sfx_critter_roll_b",
    "sfx_visitor_offer_letter", "sfx_visitor_offer_seed",
    "sfx_visitor_nod_a", "sfx_visitor_nod_b",
    "sfx_visitor_rattle_a", "sfx_visitor_rattle_b",
]
gap = np.zeros(int(.4 * 44100)); parts = []
for k in ORDER:
    x, sr = sf.read(f"sfx/{k}.ogg")
    if x.ndim > 1:
        x = x.mean(1)
    parts += [x, gap]
sf.write("/tmp/_prev_pet_anim.wav", np.concatenate(parts[:-1]), 44100, subtype="FLOAT")
subprocess.run(
    ["ffmpeg", "-y", "-v", "error", "-i", "/tmp/_prev_pet_anim.wav",
     "-ac", "1", "-c:a", "libvorbis", "-q:a", "3", "-fflags", "+bitexact", "-flags:a", "+bitexact",
     "sfx/_preview_pet_anim.ogg"],
    check=True,
)
print("preview", sum(len(p) for p in parts[:-1]) / 44100, "s", "n=", len(ORDER))
