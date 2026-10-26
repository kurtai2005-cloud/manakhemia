#!/usr/bin/env bash
# 重現晨苔鎮 SFX×24：喺 windrun-audio/ 目錄執行  bash tools/build_town_sfx.sh
# 注意：只清 tmp/，唔會刪 sfx/ 內已有（賽中）檔案，只新增／覆寫 sfx_step_town_*、sfx_step_grass_path_*、sfx_step_wood_floor_*、sfx_dialog_*、sfx_interact_*、sfx_menu_move、sfx_register_*、sfx_leafcoin_get、sfx_item_get、sfx_zone_enter。
set -e
PY=${PY:-python3}; export PYTHONPATH=tools
rm -rf tmp && mkdir -p tmp sfx
$PY tools/gen_sfx_town.py > /dev/null
$PY tools/norm_town.py
$PY tools/encode_sfx.py                   # 編碼後量度解碼 peak／TP，必要時降增益（≤ -1 dB）；單聲道
