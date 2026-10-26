#!/usr/bin/env bash
# 重現 cue 表新增 7 個音訊（P1：stinger_entry、sfx_countdown_tick、jingle_capture；P2：jingle_levelup、sfx_stamina_warn、sfx_stamina_empty、amb_wind_title）：
# 喺 windrun-audio/ 目錄執行  bash tools/build_new.sh
# 只清 tmp_new/，唔會刪 bgm/、sfx/ 內已有檔案；輸出到 sfx/（6 個）同 amb/（1 個）。
set -e
export PY=${PY:-python3} FF=${FF:-ffmpeg} FP=${FP:-ffprobe} PYTHONPATH=tools
rm -rf tmp_new && mkdir -p tmp_new sfx amb
$PY tools/gen_new_audio.py > /dev/null     # 合成 → tmp_new/<name>.wav
$PY tools/norm_new.py                      # 設響度（短音重複量度近似；amb 直接量 -24 LUFS）
$PY tools/encode_new.py                    # 編碼 ogg q5；解碼後 peak／TP ≤ -1 dB；amb 解碼後響度微調到 -24 ±0.25
$PY tools/verify_new.py                    # 驗證（格式／長度／LUFS／TP／tick 音高／amb 樣本精確循環）
rm -rf tmp_new
