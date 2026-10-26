# audio/ — 《微光小圃》音效與配樂

負責：遊音。依據 `docs-gdd/pet-one-pager.md`（Kurt 已批准）：溫柔、治癒嘅夜間小園圃，4 項需求（餵食／玩耍／清潔／睡眠）、3 個迷你遊戲、5 個階段（光卵→芽崽→跳跳期→守夜者→靜光）。

**MVP 範圍**：1 首照顧 BGM（`bgm_care_loop.ogg`）＋ 餵食／玩耍／清潔／睡眠／迷你遊戲基本 SFX ＋ 孵化／進化／化光 3 個 jingle。其餘列為「待做」，唔阻 MVP。

## 1. 檔案規格

| 類別 | 格式 | 取樣／聲道 | 響度 | 峰值 | 長度 | 命名 |
|---|---|---|---|---|---|---|
| BGM | ogg（Vorbis） | 44.1 kHz，立體聲 | -16 LUFS（integrated） | true peak ≤ -1 dBTP | 見第 2 節，完整小節，必須無縫循環 | `bgm_<scene>_loop.ogg` |
| SFX | ogg（Vorbis） | 44.1 kHz，單聲道 | 約 -12 LUFS 為參考；頻密出現嘅音刻意更細聲（見第 3 節實測） | sample peak ≤ -1 dBFS | 0.1–2 秒 | `sfx_<name>.ogg` |
| Jingle（孵化／進化／化光／搖籃曲） | 同 SFX | 同 SFX | 同 SFX | 同 SFX | **例外：最長 3 秒** | `sfx_<name>.ogg` |

- 命名只用 `a-z`、`0-9`、`_`（snake_case）。
- 響度量度：BGM 直接量整首；SFX 短過 0.4 秒，gated 響度計唔穩定，所以用「重複播放約 4 秒（每次間隔 0.1 秒）」量度，係近似值。全部數值喺解碼後嘅 ogg 上用 `ffmpeg ebur128=peak=true` 量，唔係估算。
- **程式整合提示**：BGM 用 sample-accurate loop（唔好用有 gap 嘅串流／MP3）。ogg 已確認解碼後樣本數 = 循環長度（3,112,941 samples），接縫處連續。場景切換建議 1–2 秒 crossfade。`sfx_mg_catch` 連擊可用 playbackRate 1.0／1.189／1.335／1.587（+0／3／5／8 半音），音高仍喺五聲音階內。

## 2. BGM 方向

| 場景 | 檔名 | 風格方向 | 速度 | 循環長度 | 狀態 |
|---|---|---|---|---|---|
| 照顧（日夜通用） | `bgm_care_loop.ogg` | 微光夜園。柔和 pad、音樂盒／鐘琴旋律（附點回音）、豎琴撥弦琶音、輕微空氣聲同遠處蟋蟀；C 大調五聲音階，和弦 Cmaj7–Am7–Fmaj7–G6（中段 F–G–Em7–Am7） | 68 BPM，4/4 | 20 小節 = 70.588 s | **已做** |
| 照顧（夜間版） | `bgm_care_night_loop.ogg` | 同上，更疏、少琶音、多蟋蟀，配睡眠／深夜 | 60–64 BPM | 60–90 s | 待做 |
| 主選單／孵化 | `bgm_menu_loop.ogg`、`bgm_hatch_loop.ogg` | 空曠、期待。孵化版漸強嘅光點感，旋律更少 | 60–66 BPM | 30–45 s | 待做 |
| 接星屑（45 s） | `bgm_mg_catch_loop.ogg` | 輕盈、流動。撥弦同鐘琴上行音型，清爽唔搶 SFX | 90–100 BPM | 整數小節，約 24–48 s，遊戲內循環 | 待做 |
| 點燈節拍（40 s） | `bgm_mg_rhythm_loop.ogg` | 節拍清楚（柔和 pluck＋輕 tick），留位畀點擊音 | **固定 96 BPM**（一拍 0.625 s；16 小節 = 40.0 s），程式可按拍子同步 | 40.0 s | 待做 |
| 螢火記憶（60 s） | `bgm_mg_memory_loop.ogg` | 平靜、疏落。少音符，大量留白，pad 為主 | 72 BPM（18 小節 = 60.0 s） | 60.0 s | 待做 |
| 搖籃曲 | `sfx_sleep_lullaby.ogg` | 睡眠短搖籃旋律（jingle） | 60 BPM | 3–5 s（jingle 例外，另議） | 待做 |

孵化、進化、化光 jingle 見第 3 節（已做）。方向：溫柔、帶感動，唔係傷感。

## 3. SFX 清單

量度值（解碼 ogg 後，ffmpeg ebur128）：I = integrated（SFX 為重複量度近似值）、TP = true peak。

| 檔名 | 觸發 | 長度 | I (LUFS) | TP (dBTP) | 備註 | 狀態 |
|---|---|---|---|---|---|---|
| `sfx_feed_snack` | 餵小點 | 0.55 s | -16.2 | -1.9 | 兩下圓潤「噠咀」＋細鈴，頻密，刻意細聲 | 已做 |
| `sfx_feed_meal` | 餵正餐 | 1.45 s | -15.1 | -2.0 | 三下咀嚼＋上行三音鈴聲，滿足感 | 已做 |
| `sfx_play_tease` | 逗玩 | 0.60 s | -14.0 | -3.4 | 兩個上揚俏皮顫音滑音 | 已做 |
| `sfx_clean_wash` | 沖洗 | 1.40 s | -16.2 | -2.4 | 柔和水沙＋氣泡，噪音偏中高頻、無尖刺 | 已做 |
| `sfx_clean_poop` | 清走便便 | 0.78 s | -16.5 | -1.8 | 一抹＋「啵」＋兩粒閃光 | 已做 |
| `sfx_sleep_on` | 關燈入睡 | 1.90 s | -14.0 | -2.5 | 三音下行搖籃音，低頻慢慢暗下 | 已做 |
| `sfx_sleep_off` | 睡醒開燈 | ~1 s | — | — | 上行兩音，輕柔 | 待做 |
| `sfx_pet_happy` | 寵物開心 | ~0.5 s | — | — | 輕快兩音 chirp（頻密，要細聲） | 待做 |
| `sfx_pet_uncomfortable` | 寵物不適 | ~0.6 s | — | — | 低緩下滑「嗚」，不嚇人 | 待做 |
| `sfx_need_warning` | 需求 <30 提示 | ~0.8 s | — | — | 兩下柔和單音，唔急促 | 待做 |
| `sfx_mg_start` | 迷你遊戲開始 | 0.95 s | -15.0 | -2.1 | 兩下短鈴＋上行鈴聲 | 已做 |
| `sfx_mg_catch` | 接到星屑 | 0.20 s | -16.0 | -2.5 | 極短鈴聲 E6，每秒可能多次，最細聲；連擊可變調 | 已做 |
| `sfx_mg_miss` | 接失／碰暗石 | 0.28 s | -15.0 | -2.8 | 柔和低沉「噗」，唔刺耳 | 已做 |
| `sfx_mg_combo` | 連擊里程碑 | ~0.5 s | — | — | 上行閃爍 | 待做 |
| `sfx_mg_win` | 迷你遊戲完成 | 1.95 s | -14.0 | -2.2 | 五音上行鈴聲收長和弦 | 已做 |
| `sfx_reward_orb` | 獲得光粒 | 0.98 s | -15.0 | -1.4 | 三音閃亮上行 | 已做 |
| `sfx_tap` | UI 點擊 | 0.12 s | -14.1 | -1.8 | 通用，沿用 | 已做 |
| `sfx_confirm` | UI 確認 | 0.32 s | -13.1 | -3.0 | 通用，沿用 | 已做 |
| `sfx_cancel` | UI 取消 | 0.29 s | -13.5 | -2.8 | 通用，沿用 | 已做 |
| `sfx_error` | UI 無效操作 | 0.33 s | -13.2 | -4.9 | 通用，沿用 | 已做 |
| `sfx_hatch` | 孵化（光卵→芽崽） | 2.90 s | -15.6 | -1.9 | Jingle：輕微裂開 tick → 光點漸強 → 鈴聲綻放 | 已做 |
| `sfx_evolve` | 進化 | 2.90 s | -15.0 | -1.8 | Jingle：五聲音階上行 → 閃亮長和弦 | 已做 |
| `sfx_fade_light` | 化光（靜光→光卵） | 3.00 s | -14.6 | -2.1 | Jingle：溫暖暖和弦＋下行旋律，之後光粒上升；溫柔、感動，非悲傷 | 已做 |
| `sfx_coin` `sfx_hit` `sfx_win` `sfx_lose` | 舊通用音效（風野競走時期） | 0.18–1.64 s | -12.8 至 -13.4 | -1.6 至 -2.6 | 微光小圃暫不使用，保留備用 | 已做 |

量度（BGM）：`bgm_care_loop.ogg` vorbis 44.1 kHz 立體聲，70.588 s，**-16.0 LUFS，TP -4.2 dBTP**，1,056,089 bytes。全部音訊總共約 1.28 MB。

規格偏差（如實）：
1. 新 SFX 嘅響度係 -14.0 至 -16.5 LUFS（重複量度），低過參考 -12：喺 sample peak ≤ -2 dBFS 嘅限制下，柔和嘅鈴聲／水聲冇壓縮就唔會更大聲，我刻意唔加 limiter／失真去追響度，換取唔刺耳；頻密嘅音（feed_snack、mg_catch、clean_*）更細聲。需要加大可喺程式用音量調整。
2. Jingle 長度 2.9–3.0 s，超過 SFX 嘅 2 秒（已獲准例外，上限 3 s）。`sfx_mg_win` 1.95 s 貼近上限。
3. 舊通用 SFX 實測約 -12.8 至 -14.1 LUFS，之前文件寫「約 -12」並唔準確，已更正。

## 4. 無縫循環做法（BGM）

全部聲音先渲染到「循環長度＋7 秒尾巴」，尾巴疊返落開頭（overlap-add）；殘響、空氣聲濾波用 FFT 圓周運算，所以尾端自然接回開頭。驗證（解碼後 ogg）：總樣本數剛好 = 20 小節；接縫處樣本差（0.011／0.020）細過全曲 99.9 百分位差（0.033／0.029）；接縫前後 50 ms RMS 冇突變。

## 5. 重現方式（`tools/`）

```
cd audio
PY=python3 bash tools/build_all.sh      # 需要 numpy、scipy、soundfile、ffmpeg
```

| 腳本 | 用途 |
|---|---|
| `dsp.py` | 共用合成工具（鐘琴、撥弦、滑音、噪音、殘響） |
| `gen_sfx_pet.py` | 14 個微光小圃 SFX／jingle（固定亂數種子） |
| `gen_bgm_care.py` | `bgm_care_loop.ogg`：合成、無縫疊尾、迭代增益至 -16 LUFS、ogg 編碼 |
| `norm.py` | SFX 響度：`--linear name:目標LUFS`（純增益，峰值上限 -2 dBFS）；舊模式為 tanh 軟飽和 |
| `build_sfx.sh` / `build_all.sh` | 一鍵生成＋編碼＋量度 |
| `measure.py` | ffprobe／ebur128 驗證：格式、長度、LUFS、true peak |
| `gen_sfx.py` | 舊通用 UI SFX（預設唔重生，`GENERIC=1` 先重生） |

SFX 編碼：`ffmpeg -ac 1 -ar 44100 -c:a libvorbis -q:a 3`；BGM：`-ac 2 -c:a libvorbis -q:a 5`。

## 6. 版權與私隱

- 所有音訊都係**原創、程式合成**（numpy／scipy 波形運算），冇用任何取樣、音色庫或第三方受版權保護嘅素材，亦冇參考任何現有作品嘅旋律或音效。
- 唔包含個人資料（包括人聲錄音、真實姓名、位置等）。
- 呢個係公開 repo，加入新音檔前請先確認符合以上兩點。
