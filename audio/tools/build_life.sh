#!/usr/bin/env bash
# 團絨生命感（精簡）：8 款 × a/b ＝ 16 個 sfx_pet_*（≤0.6 s，細聲）。喺 audio/ 執行：PY=python3 bash tools/build_life.sh
set -e
PY=${PY:-python3}; export PYTHONPATH=tools
$PY tools/gen_sfx_life.py          # 生成＋編碼 sfx/*.ogg（純增益迭代到 LUFS20 目標，峰值上限 -6 dBFS）
$PY tools/measure_life.py sfx/sfx_pet_{sneeze,scratch,step_hop,step_drag,turn_huh,nuzzle_purr,reunion_happy,bug_pat}_{a,b}.ogg
