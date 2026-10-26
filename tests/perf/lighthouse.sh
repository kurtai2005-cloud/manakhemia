#!/usr/bin/env bash
# lighthouse.sh — 載入／靜態表現基準（Lighthouse 只量「載入＋閒置」，唔量賽中 fps；賽中 fps 用 fps_probe.js）
# 用法：./lighthouse.sh http://localhost:8000/ [out目錄=out/lighthouse]
# 需要網絡（npx 下載 lighthouse）；用 Chrome headless；mobile 預設（Moto G Power 模擬＋Slow 4G＋CPU 4× 限速）
set -euo pipefail
URL="${1:-http://localhost:8000/}"; OUT="${2:-$(dirname "$0")/out/lighthouse}"; mkdir -p "$OUT"
CHROME="${CHROME_PATH:-/usr/bin/google-chrome}"
for FORM in mobile desktop; do
  npx --yes lighthouse "$URL" --chrome-path="$CHROME" \
    --chrome-flags="--headless=new --no-sandbox" \
    --preset=$([ "$FORM" = desktop ] && echo desktop || echo perf) $([ "$FORM" = mobile ] && echo "--form-factor=mobile") \
    --throttling-method=devtools --only-categories=performance,best-practices --output=json --output=html \
    --output-path="$OUT/lh-$FORM" --quiet
  node -e '
    const r=require(process.argv[1]); const a=r.audits;
    const g=k=>a[k]&&a[k].numericValue!=null?Math.round(a[k].numericValue):null;
    console.log(JSON.stringify({form:process.argv[2],perfScore:Math.round(r.categories.performance.score*100),
      FCP_ms:g("first-contentful-paint"),LCP_ms:g("largest-contentful-paint"),TBT_ms:g("total-blocking-time"),CLS:a["cumulative-layout-shift"]&&a["cumulative-layout-shift"].numericValue,
      TTI_ms:g("interactive"),totalKB:a["total-byte-weight"]&&Math.round(a["total-byte-weight"].numericValue/1024),mainThread_ms:g("mainthread-work-breakdown")}));
  ' "$OUT/lh-$FORM.report.json" "$FORM"
done
