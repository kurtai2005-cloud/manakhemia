#!/usr/bin/env bash
# 寵物／訪客／小動物動作音（按 anim_timing.json 對拍）＋試聽合輯（只供試聽，唔入遊戲）＋ QA。
# 喺 audio/ 執行：PY=/workspace/audio-venv/bin/python bash tools/build_anim.sh
set -e
PY=${PY:-python3}; export PYTHONPATH=tools
TIMING=${TIMING:-/tmp/anim-timing/art-pet/anim_timing.json}
$PY tools/gen_sfx_anim.py --timing "$TIMING"
$PY tools/preview_pet_anim.py
$PY tools/qa_audio.py --map anim_sfx_map.json
