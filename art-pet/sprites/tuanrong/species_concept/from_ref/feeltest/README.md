# feeltest：from_ref/tuned × 《微光小圃》HD-2D 場景手感測試

- 直接開 `index.html`（自足：`assets/` 已抄 H1–H4 場景層同 24 隻 idle strip，`data.js` 係設定）。
- 美術格 195×422，整數倍放大（Nearest）；疊層跟 `scenes/hd2d/FORMAT.md` §2（sky/far/mid → 寵物（petTint×ambientTint）→ fore → lightmap multiply → light_add／emissive_blur lighter → 燈泡 radial glow → 粒子 → fog → vignette）。
- 寵物腳底 art (97,292)、pivot (32,61)；idle bob 0.9s、眨眼 ~3.3s；換寵物有細跳＋光點。
- 操作：輕按畫面／▶ 下一隻、◀ 上一隻、「時段」換 H1→H4、「48px」掣輪換 48→64→80→96；鍵盤 ←／→、t、s。
- URL 參數：`?pet=C1&scene=H2&t=0.5`（t 固定時間，截圖用）、`ui=0` 收 UI、`size=48`（預設 48＝正式版 [pt98u]，返舊寵尺寸；48／64／80／96，pivot 跟尺寸：(24,45)／(32,61)／(40,77)／(48,93)）。
- 截圖：`shots/*.png`（headless Chrome 390×844）、`shots_sheet.png` 2×2。
- 重建：`python3 tools/build_from_ref_tuned.py all [--size 80|96] && python3 tools/build_from_ref_feeltest.py（assets/pets64、pets80、pets96）`
- 正式版：48px（`../tuned_48/ENGINE_48.md`，Kurt [pt98u]「用舊既size」）。`shots48/`＋`shots48_sheet.png`＝48 截圖；`shots/` 係舊 80 截圖（留作對照）。
- 48 重建：`python3 tools/build_from_ref_px48.py && python3 tools/build_from_ref_px48_out.py && python3 tools/build_from_ref_feeltest.py`
