#!/usr/bin/env bash
# 《微光小圃》H3 雨層：細雨環境聲 2 檔（amb/）。喺 audio/ 執行：PY=python3 bash tools/build_rain.sh
# 固定亂數種子＋ -fflags +bitexact → 重跑 byte 一致。
set -e
PY=${PY:-python3}
export PYTHONPATH=tools
mkdir -p tmp amb
$PY tools/gen_amb_rain.py                    # amb/amb_rain_light_loop.ogg（7 小節無縫）＋ amb/amb_rain_light_short.ogg（6 s 淡入淡出）
$PY tools/measure_amb.py amb/amb_rain_*.ogg  # 樣本數／LUFS／TP／頻帶比／重心／接縫／淡入淡出
