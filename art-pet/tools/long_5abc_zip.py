# 打包 staging zip：python3 tools/long_5abc_zip.py 5a|5b|5c   → /workspace/series2-<part>-staging.zip（格式同 4b）
import hashlib, os, sys, time, zipfile
GD = "/workspace/game-design"; ART = GD + "/art-pet"
TOOLS = {"5a": ["long_5abc_lib.py", "long_5abc_ui.py", "long_5c_patterns.py", "long_5a_rooms.py", "long_5a_build.py", "long_5a_ui.py", "long_5a_preview.py", "validate_long_5abc.py", "long_5abc_zip.py"],
         "5b": ["long_5abc_lib.py", "long_5abc_ui.py", "long_5c_patterns.py", "long_5a_ui.py", "long_5b_build.py", "long_5b_ui.py", "long_5b_preview.py", "validate_long_5abc.py", "long_5abc_zip.py"],
         "5c": ["long_5abc_lib.py", "long_5abc_ui.py", "long_5c_patterns.py", "long_5c_build.py", "long_5c_ui.py", "long_5c_preview.py", "validate_long_5abc.py", "long_5abc_zip.py"]}
DESC = {"5a": "長線 5a 家族同屋擴建（interact 打招呼 × 59 形態、擴房 3 間日夜、HD-2D 家族 Lv／升級／揀蛋二揀一／做主養／切房／族譜＋金色族譜）",
        "5b": "長線 5b 遠足同工作（出發／返屋 × 成年 25（靜光 9＋細佬 S5/S6 16）、手信 10（HD icon＋1x pixel）、工作帽 4 款 × 4 級（Lv1–2／3–4／5／6）overlay × 25；需要先有 5a、工作 icon＋Lv 章、HD-2D 揀行程／日記／返屋 toast）",
        "5c": "長線 5c 遺傳（花紋 8 款 overlay × 59 形態＋蛋、上一代染色表、教錯招式、HD-2D 揀上一代／遺傳預覽）"}
RERUN = {"5a": "python3 tools/long_5a_build.py && python3 tools/long_5a_ui.py && python3 tools/long_5a_preview.py",
         "5b": "python3 tools/long_5b_build.py && python3 tools/long_5b_ui.py && python3 tools/long_5b_preview.py",
         "5c": "python3 tools/long_5c_build.py && python3 tools/long_5c_ui.py && python3 tools/long_5c_preview.py"}
def main(part):
    files = ["art-pet/sprites/series2_long/LONG_5ABC.md"]
    for root, ds, fs in os.walk(f"{ART}/sprites/series2_long/{part}"):
        ds[:] = sorted(d for d in ds if d != "_backups" and not d.startswith("."))
        for f in sorted(fs): files.append(os.path.relpath(os.path.join(root, f), GD))
    files += [f"art-pet/tools/{t}" for t in TOOLS[part]]
    lines = [f"batch{part} staging — {DESC[part]}",
             f"生成：{time.strftime('%Y-%m-%d %H:%M')}（HKT）；純 Pillow/numpy 程序生成，冇 AI 圖。解壓到 /workspace/game-design/ 覆蓋同路徑即可。",
             f"重跑：cd art-pet && {RERUN[part]}", f"驗證：python3 tools/validate_long_5abc.py {part} → PASS",
             "說明：art-pet/sprites/series2_long/LONG_5ABC.md；UI 只做 HD-2D；4a/4b 檔冇改（house.json 用遊策新版：葉仔床預設、商店 7 件 165 碎）",
             "冇 push／merge；冇 _backups。", "sha1(12)  bytes  path"]
    for f in files:
        b = open(os.path.join(GD, f), "rb").read(); lines.append(f"{hashlib.sha1(b).hexdigest()[:12]}  {len(b):8d}  {f}")
    out = f"/workspace/series2-{part}-staging.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"MANIFEST_{part}.txt", "\n".join(lines) + "\n")
        for f in files: z.write(os.path.join(GD, f), f)
    print(out, len(files) + 1, "files", os.path.getsize(out), "bytes")
if __name__ == "__main__": main(sys.argv[1])
