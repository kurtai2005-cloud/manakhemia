#!/usr/bin/env bash
# 重現 12 個 SFX＋3 個 stinger：喺 windrun-audio/ 目錄執行  bash tools/build_sfx.sh
set -e
PY=${PY:-python3}; FF=${FF:-ffmpeg}
rm -rf tmp && mkdir -p tmp sfx
export PYTHONPATH=tools
$PY tools/gen_sfx_race.py > /dev/null
# 瞬態重／crest factor 大嘅短音：前置增益＋前瞻限幅器（--limit，限幅量 ≤9 dB），目標按「頻密度」：腳步最細、技能／換棒較大
$PY tools/norm.py --limit sfx_baton_out:-13 sfx_baton_in:-13 sfx_skill_charge:-13 sfx_skill_burst_gale:-13 sfx_skill_trip_grass:-14 \
   sfx_skill_recover:-13 sfx_skill_wind_shield:-13 sfx_hit_stop_impact:-13 sfx_step_moss:-14 sfx_step_gravel:-14 \
   sfx_step_shallow_water:-14 sfx_countdown_go:-13 sfx_finish_line:-14
# 長尾、響度已經夠：純增益
$PY tools/norm.py --linear sfx_stinger_win:-14 sfx_stinger_lose:-15
$PY tools/encode_sfx.py                   # 編碼後量度解碼 peak／TP，必要時降增益（≤ -1 dB）
