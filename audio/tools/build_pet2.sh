#!/usr/bin/env bash
# 方案 A 週1：寵物聲（11 檔）＋事件提示音（8 檔）。喺 audio/ 執行：PY=python3 bash tools/build_pet2.sh
set -e
PY=${PY:-python3}; FF=${FF:-ffmpeg}
rm -rf tmp && mkdir -p tmp sfx
export PYTHONPATH=tools
$PY tools/gen_sfx_pet2.py
# 純增益，目標響度（頻密出現嘅聲更細聲）；峰值上限 -2 dBFS
$PY tools/norm_pet2.py sfx_pet_happy:-18 sfx_pet_content:-18 sfx_pet_hungry:-18 sfx_pet_sleepy:-18 sfx_pet_uncomfortable:-18 \
   sfx_pet_curious:-18 sfx_pet_yawn:-18 sfx_pet_sleep_breath_loop:-22 sfx_pet_touch_a:-19 sfx_pet_touch_b:-19 sfx_pet_grumpy:-18 \
   sfx_event_gift_return:-15 sfx_event_butterfly_visit:-16 sfx_event_meteor_night:-15 sfx_event_rainbow:-15 \
   sfx_event_dream_talk:-16 sfx_event_sulk:-15 sfx_event_treasure_hunt:-15 sfx_event_shiny_day:-14
for f in tmp/sfx_pet_*_n.wav tmp/sfx_event_*_n.wav; do b=$(basename $f _n.wav); $FF -y -v error -i $f -ac 1 -ar 44100 -c:a libvorbis -q:a 3 sfx/$b.ogg; done
rm -rf tmp
