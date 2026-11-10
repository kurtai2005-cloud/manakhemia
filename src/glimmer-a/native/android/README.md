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

# 6d 原生 — Share6d plugin（朋友碼）

## 檔案
- `Share6dPlugin.kt` → `android/app/src/main/java/hk/vizard/glimmer/fpet/Share6dPlugin.kt`
- `MainActivity.java`：`registerPlugin(RealWorldPlugin.class);` 之後加 `registerPlugin(Share6dPlugin.class);`
- 唔使改 AndroidManifest：**冇新權限**；分享用現有 `${applicationId}.fileprovider`（`res/xml/file_paths.xml` 已有 `cache-path`）。
- `app/build.gradle`：versionCode 4、versionName "1.3"（6d）。
- 6d.1：versionCode 5、versionName "1.3.1"（同一張 release cert；keystore／密碼唔入 repo）。
- 6d.2：versionCode 6、versionName "1.3.2"（同一張 release cert；keystore／密碼唔入 repo）。
- 3d-h1（#89 3D 花園 H1 試點）：versionCode 7、versionName "1.4.0-3d"（同一張 release cert；keystore／密碼唔入 repo；唔 merge）。
- 3d-h1.1：versionCode 8、versionName "1.4.1-3d"（同一張 release cert；keystore／密碼唔入 repo；唔 merge）。
- 3d-h1.2：versionCode 9、versionName "1.4.2-3d"（同一張 release cert；keystore／密碼唔入 repo；唔 merge）。可見區構圖、跟拍建立鏡頭、日影／夜空、網格預設關、3D 行速 20；行為 hook 掛 PARAMS.beh。

## JS 介面（`Capacitor.Plugins.Share6d`，src/long6dui.js 用；冇 plugin → 瀏覽器 clipboard／下載／Web Share）
| 方法 | 做咩 |
|---|---|
| `copy({ text })` | 朋友碼放入剪貼簿 |
| `paste()` | `{ text }` 讀剪貼簿純文字 |
| `saveImage({ data: base64 PNG, name })` | API 29+ → MediaStore `Pictures/微光小圃`（`{ uri, gallery: true }`）；API 26–28 → app 自己 Pictures 資料夾（`{ path, gallery: false }`，唔使 WRITE_EXTERNAL_STORAGE） |
| `share({ data, name, text })` | PNG 寫 `cache/share6d/` → FileProvider → ACTION_SEND（圖＋碼文字） |

PNG 上限 8 MB（495×756 分享圖約 100–200 KB）。冇網絡、冇讀相簿（揀相用 WebView `<input type=file>` 系統揀相器）。
