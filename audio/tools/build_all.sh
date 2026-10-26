#!/usr/bin/env bash
# 重現《微光小圃》全部 MVP 音訊。喺 audio/ 目錄執行：PY=python3 bash tools/build_all.sh
# 需要：python3 + numpy/scipy/soundfile、ffmpeg/ffprobe。固定亂數種子，結果可重現。
set -e
export PY=${PY:-python3} PYTHONPATH=tools
bash tools/build_sfx.sh                      # sfx/*.ogg（微光小圃 14 個；通用 UI 8 個保留現有檔）
$PY tools/gen_bgm_care.py                    # bgm/bgm_care_loop.ogg（-16 LUFS 迭代增益）
rm -rf tmp
$PY tools/measure.py bgm/*.ogg sfx/*.ogg     # 驗證格式／長度／響度／峰值
