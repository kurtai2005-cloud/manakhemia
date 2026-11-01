#!/usr/bin/env bash
# 萌系 8bit／16bit UI v2（sfx_ui8_*，19 檔，按 MOTION.md v2 對拍）＋團絨重步（sfx_pet_step_plod_a/b）＋試聽合輯（只供試聽，唔入遊戲）。
# 喺 audio/ 執行：PY=/workspace/audio-venv/bin/python bash tools/build_ui8.sh
set -e
PY=${PY:-python3}; export PYTHONPATH=tools
$PY tools/gen_sfx_ui8.py
$PY tools/gen_sfx_plod.py
$PY tools/preview_ui8.py
$PY tools/measure_life.py sfx/sfx_ui8_*.ogg sfx/sfx_pet_step_plod_{a,b}.ogg
