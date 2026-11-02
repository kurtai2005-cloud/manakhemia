# 6b 原生（Android，Capacitor 6）— RealWorld plugin

APK 工程喺 repo 外（`/workspace/fpet-hd2d`，唔係 git）；呢度留一份可 review 嘅副本。

## 檔案
- `RealWorldPlugin.kt` → `android/app/src/main/java/hk/vizard/glimmer/fpet/RealWorldPlugin.kt`
- `MainActivity.java`：`registerPlugin(FloatingPetPlugin.class);` 之後加 `registerPlugin(RealWorldPlugin.class);`
- `AndroidManifest.xml`（加喺現有 permissions 後面）：
```xml
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-feature android:name="android.hardware.sensor.stepcounter" android:required="false" />
<uses-feature android:name="android.hardware.location" android:required="false" />
<uses-feature android:name="android.hardware.location.network" android:required="false" />
```
（`INTERNET` 已經有。冇加 `ACCESS_FINE_LOCATION`、冇背景位置、冇 foreground service、冇 Health Connect。）

## JS 介面（`Capacitor.Plugins.RealWorld`，src/long6bui.js 用）
| 方法 | 回傳 |
|---|---|
| `status()` | `{ steps, location: 'granted'|'denied'|'prompt'|'prompt-with-rationale', sensor: bool, sdk }` |
| `requestSteps()` | `{ steps }`（API 26–28 唔使問，直接 granted） |
| `requestLocation()` | `{ location }` |
| `steps()` | `{ steps（開機至今總數）, bootMs }`；reject `permission`／`nosensor`／`timeout` |
| `location()` | `{ lat, lon }`（四捨五入 0.1°）；reject `permission`／`noloc`／`timeout` |

## 冇權限點降級
- 唔畀計步（或部機冇 TYPE_STEP_COUNTER）→ 開關保持「閂」、提示「照舊玩」；冇步數、冇散步碎；其他全部照舊。
- 唔畀位置／冇網／Open-Meteo 失敗 → 用遊戲每日擲天氣＋原本晝夜（真天氣讀數 6 小時後過期都係咁）。
- 計步只喺 app 喺前台時讀（開 app、返前台、每 60 秒）；app 閂咗期間嘅步數，下次讀嗰陣一次過計（TYPE_STEP_COUNTER 係開機至今總數）；重開機由新計數計。
