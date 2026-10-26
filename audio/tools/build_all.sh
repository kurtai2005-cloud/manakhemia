#!/usr/bin/env bash
# 重現《微光小圃》全部 MVP 音訊。喺 audio/ 目錄執行：PY=python3 bash tools/build_all.sh
# 需要：python3 + numpy/scipy/soundfile、ffmpeg/ffprobe。固定亂數種子，結果可重現。
set -e
export PY=${PY:-python3} PYTHONPATH=tools
bash tools/build_sfx.sh                      # sfx/*.ogg（微光小圃 14 個；通用 UI 8 個保留現有檔）
bash tools/build_pet2.sh                     # 方案 A 週1：sfx_pet_*（11）＋ sfx_event_*（8）
$PY tools/gen_bgm_care.py                    # bgm/bgm_care_loop.ogg（-16 LUFS 迭代增益）
$PY tools/gen_bgm_tod.py                     # 方案 A ③：bgm_care_{morning,evening,night}_loop.ogg（-16／-16／-22 LUFS）
bash tools/build_env.sh                      # 方案 A ④：sfx_env_flowerpot_bump／sfx_env_sunbathe_loop
$PY tools/fix_qa_pet.py                      # 依遊測審查 2026-10-26：dream_talk -7 dB、grumpy 起音淡入 -1.5 dB、UI 5 音降到 ≤ -13.3 LUFS20（需先有 _prev/ 備份；首次執行自動由現有 sfx/ 備份；重生全部時先 rm -rf _prev）
rm -rf tmp
$PY tools/measure.py bgm/*.ogg sfx/*.ogg     # 驗證格式／長度／響度／峰值
$PY tools/measure_pet2.py sfx/sfx_pet_*.ogg sfx/sfx_event_*.ogg sfx/sfx_env_*.ogg   # 方案 A 新檔（含循環接縫檢查）
$PY tools/measure_tod.py bgm/bgm_care_*_loop.ogg   # 時段 BGM（立體聲）：樣本數＝整數小節、接縫
