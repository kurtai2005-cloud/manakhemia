#!/usr/bin/env bash
# 重現《風野競走》音訊草稿：賽中（BGM×2、stinger×3、SFX×12）＋晨苔鎮／冒險層（城鎮 BGM×1、SFX×24）＋cue 表新增（stinger／jingle×3、SFX×3、環境風聲×1）。喺 windrun-audio/ 目錄執行：
#   PY=python3 FF=ffmpeg FP=ffprobe bash tools/build_all.sh
# 需要：python3 + numpy/scipy/soundfile、ffmpeg/ffprobe（含 libvorbis）。固定亂數種子，結果可重現。
set -e
export PY=${PY:-python3} FF=${FF:-ffmpeg} FP=${FP:-ffprobe} PYTHONPATH=tools
rm -rf tmp bgm sfx amb; mkdir -p tmp bgm sfx amb
$PY tools/gen_bgm_race.py                # bgm/bgm_race_loop.ogg、bgm_race_final_loop.ogg（-16 LUFS 迭代增益）
bash tools/build_sfx.sh                  # sfx/*.ogg（12 SFX＋finish／win／lose）
bash tools/build_town_sfx.sh             # sfx/ 內 24 個晨苔鎮 SFX（只清 tmp，唔刪 sfx/）
$PY tools/gen_bgm_town.py                # bgm/bgm_town_morningmoss_loop.ogg（75 BPM、24 小節、-16 LUFS 迭代增益；tmp/ 留編碼前 wav 俾 verify_town 對比）
$PY tools/verify.py                      # 驗證（賽中）：格式／長度／響度／峰值／起音／循環接縫／切換試聽檔（亦會列出城鎮檔）
$PY tools/verify_town.py                 # 驗證（晨苔鎮）：格式／長度／響度／TP／起音／BGM 循環／頻譜／blip 15/s、腳步實用響度
bash tools/build_new.sh                  # cue 表新增 7 個：sfx/ 內 stinger_entry、sfx_countdown_tick、jingle_capture、jingle_levelup、sfx_stamina_warn、sfx_stamina_empty＋amb/amb_wind_title（用自己嘅 tmp_new/，唔影響上面）
rm -rf tmp
