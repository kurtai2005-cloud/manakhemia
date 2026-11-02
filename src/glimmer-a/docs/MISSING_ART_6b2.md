# 6b.2「UI 打磨」美術缺件清單

而家全部用 CSS／現有 ui-kit-hd2d-v2 素材頂住；冇圖嘅位置係洋紅虛線 placeholder，旁邊寫咗尺寸（`data-ph`）。全部要原創，唔用任何第三方素材、字型或者圖案。

| 用途 | 檔名建議 | 尺寸（CSS px） | @3x 出圖 | 而家點頂 |
|---|---|---|---|---|
| 工作站背景・郵差 | `art/series2_long/6b2/work_bg_post.png` | 175×120 | 525×360 | 洋紅虛線 placeholder `6b2:work_bg_post` |
| 工作站背景・園丁 | `…/work_bg_garden.png` | 175×120 | 525×360 | placeholder `6b2:work_bg_garden` |
| 工作站背景・守夜 | `…/work_bg_watch.png` | 175×120 | 525×360 | placeholder `6b2:work_bg_watch` |
| 工作站背景・廚師 | `…/work_bg_chef.png` | 175×120 | 525×360 | placeholder `6b2:work_bg_chef` |
| 專用工作動畫（每個形態 × 每份工） | `work_<job>` clip | 團絨 64×64、細佬 48×48，6–8 幀 | — | 輪住播現有 walk（2.4 秒，左右行 ±14px）同 idle（2.4 秒），10fps |
| 主 rail「工作」icon | `icon_job_rail` | 48×48 | 144×144 | 暫用 5b `icon_job_post` |
| 面板角飾／框（可選） | `panel62_corner` 9-slice | 角 16×16、框 1px 金線 | 48×48 | CSS：細金邊＋內發光＋四角漸層角飾 |
| 第一次小提示卡框（可選） | `tip62_frame` 9-slice | 角 16×16 | 48×48 | 同上 CSS 面板 |
| 散步鞋架（6b.1） | `furn_shoe_rack` | 40×32 美術單位 | — | 洋紅 placeholder |

字型：標題／HUD 照用自家 GlimmerFP12；內文同輔助字用系統 Noto Sans HK（裝置內建，唔打包）。
