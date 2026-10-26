#!/usr/bin/env bash
# 重現所有 SFX：在 audio/ 目錄執行  bash tools/build_sfx.sh
set -e
PY=${PY:-python3}; FF=${FF:-ffmpeg}
rm -rf tmp && mkdir -p tmp sfx && cd tmp/.. 
export PYTHONPATH=tools
$PY tools/gen_sfx_pet.py                  # 微光小圃 SFX 同 jingle
# 通用 UI SFX（8 個）：已定稿，預設唔重生（舊檔經人手調校）。需要時  GENERIC=1 bash tools/build_sfx.sh
if [ -n "$GENERIC" ]; then $PY tools/gen_sfx.py; $PY tools/norm.py sfx_tap sfx_confirm sfx_cancel sfx_coin sfx_hit sfx_win sfx_lose sfx_error; fi
# 微光小圃：純增益，按「頻密度」設目標響度（越常出現越細聲）
$PY tools/norm.py --linear sfx_feed_snack:-15 sfx_feed_meal:-13 sfx_play_tease:-14 sfx_clean_wash:-15 sfx_clean_poop:-14 \
   sfx_sleep_on:-14 sfx_mg_start:-13 sfx_mg_catch:-16 sfx_mg_miss:-15 sfx_mg_win:-12 sfx_reward_orb:-14 \
   sfx_hatch:-13 sfx_evolve:-13 sfx_fade_light:-14
for f in tmp/sfx_*_n.wav; do b=$(basename $f _n.wav); $FF -y -v error -i $f -ac 1 -ar 44100 -c:a libvorbis -q:a 3 sfx/$b.ogg; done
rm -rf tmp
