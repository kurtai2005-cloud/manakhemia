#!/usr/bin/env bash
# 方案 A ④：環境互動音（2 檔）。喺 audio/ 執行：PY=python3 bash tools/build_env.sh
set -e
PY=${PY:-python3}; FF=${FF:-ffmpeg}
rm -rf tmp && mkdir -p tmp sfx
export PYTHONPATH=tools
$PY tools/gen_sfx_env.py
$PY tools/norm_pet2.py sfx_env_flowerpot_bump:-17 sfx_env_sunbathe_loop:-23     # 純增益；峰值上限 -2 dBFS
for f in tmp/sfx_env_*_n.wav; do b=$(basename $f _n.wav); $FF -y -v error -i $f -ac 1 -ar 44100 -c:a libvorbis -q:a 3 sfx/$b.ogg; done
rm -rf tmp
