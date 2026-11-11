#!/usr/bin/env bash
# M1b 功能音（郵局／廚房／圖鑑／家具／狩獵）＋狩獵 BGM＋試聽合輯（唔入遊戲）＋ QA。
# 喺 audio/ 執行：PY=/workspace/audio-venv/bin/python bash tools/build_m1b.sh
set -e
PY=${PY:-python3}; export PYTHONPATH=tools
$PY tools/gen_sfx_m1b.py
$PY tools/gen_bgm_hunt.py
$PY tools/preview_m1b.py
$PY tools/qa_audio.py --map m1b_sfx_map.json \
  sfx/sfx_post_letter_send.ogg sfx/sfx_post_letter_receive.ogg \
  sfx/sfx_kitchen_cook_start.ogg sfx/sfx_kitchen_cook_done.ogg sfx/sfx_kitchen_stir.ogg \
  sfx/sfx_codex_page_flip_a.ogg sfx/sfx_codex_page_flip_b.ogg sfx/sfx_codex_new_entry.ogg \
  sfx/sfx_furn_pickup.ogg sfx/sfx_furn_place_a.ogg sfx/sfx_furn_place_b.ogg sfx/sfx_furn_buy.ogg \
  sfx/sfx_hunt_pounce_a.ogg sfx/sfx_hunt_pounce_b.ogg sfx/sfx_hunt_enter.ogg \
  bgm/bgm_hunt_loop.ogg
