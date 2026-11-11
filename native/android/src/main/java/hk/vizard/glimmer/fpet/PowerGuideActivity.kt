package hk.vizard.glimmer.fpet

import android.app.Activity
import android.content.ComponentName
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.PowerManager
import android.provider.Settings
import android.util.Log
import android.util.TypedValue
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast

/** 自啟動／省電白名單引導（按 Build.MANUFACTURER）。 */
class PowerGuideActivity : Activity() {
    private fun dp(v: Float) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, resources.displayMetrics).toInt()
    private val brand = Build.MANUFACTURER.lowercase()

    private fun vendor(): String = when {
        brand.contains("xiaomi") || brand.contains("redmi") || brand.contains("poco") -> "xiaomi"
        brand.contains("honor") -> "honor"
        brand.contains("huawei") -> "huawei"
        brand.contains("oppo") || brand.contains("realme") || brand.contains("oneplus") -> "oppo"
        brand.contains("vivo") || brand.contains("iqoo") -> "vivo"
        else -> "other"
    }

    private fun steps(): String = when (vendor()) {
        "xiaomi" -> "小米／Redmi（MIUI／HyperOS）：\n1. 撳「開自啟動設定」→ 搵「微光小圃」→ 開「自啟動」。\n2. 返 app 資料頁 → 省電策略 → 揀「無限制」。\n3. 其他權限 → 開「顯示懸浮窗」同「後台彈出界面」。\n4. 最近任務長按微光小圃 → 撳🔒鎖住。"
        "huawei" -> "華為（EMUI／HarmonyOS）：\n1. 撳「開自啟動設定」（應用啟動管理）→ 搵「微光小圃」→ 熄「自動管理」→ 開晒「允許自啟動／關聯啟動／後台活動」。\n2. 電池 → 更多電池設定 → 開「休眠時始終保持網絡連接」（如有）。\n3. 最近任務落鎖。"
        "honor" -> "榮耀（MagicOS）：\n1. 撳「開自啟動設定」（應用啟動管理）→ 搵「微光小圃」→ 改手動管理，開晒三個開關。\n2. 最近任務落鎖。"
        "oppo" -> "OPPO／realme／OnePlus（ColorOS）：\n1. 撳「開自啟動設定」→ 開「微光小圃」自啟動。\n2. app 資料頁 → 耗電管理 → 開「允許後台運行」。\n3. 最近任務長按落鎖。"
        "vivo" -> "vivo／iQOO（OriginOS／Funtouch）：\n1. 撳「開自啟動設定」（後台啟動管理）→ 開「微光小圃」。\n2. 電池 → 後台耗電管理 → 微光小圃 → 「允許後台高耗電」。\n3. 最近任務落鎖。"
        else -> "一般 Android（${Build.MANUFACTURER}）：\n1. 撳下面「忽略電池最佳化」→ 允許。\n2. 如團絨過一陣唔見咗：app 資料頁 → 電池 → 揀「無限制」。"
    }

    private fun candidates(): List<Intent> {
        fun c(p: String, cls: String) = Intent().setComponent(ComponentName(p, cls))
        return when (vendor()) {
            "xiaomi" -> listOf(c("com.miui.securitycenter", "com.miui.permcenter.autostart.AutoStartManagementActivity"),
                Intent("miui.intent.action.APP_PERM_EDITOR").putExtra("extra_pkgname", packageName))
            "huawei" -> listOf(c("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
                c("com.huawei.systemmanager", "com.huawei.systemmanager.optimize.process.ProtectActivity"),
                c("com.huawei.systemmanager", "com.huawei.systemmanager.appcontrol.activity.StartupAppControlActivity"))
            "honor" -> listOf(c("com.hihonor.systemmanager", "com.hihonor.systemmanager.startupmgr.ui.StartupNormalAppListActivity"),
                c("com.huawei.systemmanager", "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"))
            "oppo" -> listOf(c("com.coloros.safecenter", "com.coloros.safecenter.permission.startup.StartupAppListActivity"),
                c("com.coloros.safecenter", "com.coloros.safecenter.startupapp.StartupAppListActivity"),
                c("com.oplus.safecenter", "com.oplus.safecenter.permission.startup.StartupAppListActivity"),
                c("com.oppo.safe", "com.oppo.safe.permission.startup.StartupAppListActivity"))
            "vivo" -> listOf(c("com.vivo.permissionmanager", "com.vivo.permissionmanager.activity.BgStartUpManagerActivity"),
                c("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.BgStartUpManager"),
                c("com.iqoo.secure", "com.iqoo.secure.ui.phoneoptimize.AddWhiteListActivity"))
            else -> emptyList()
        }
    }

    private fun appDetails() = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName"))

    private fun tryStart(list: List<Intent>): Boolean {
        for (i in list) {
            try { startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); Log.i("FloatingPet", "power guide opened ${i.component ?: i.action}"); return true }
            catch (e: Exception) { Log.i("FloatingPet", "power guide fail ${i.component ?: i.action}: ${e.javaClass.simpleName}") }
        }
        return false
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = "自啟動／省電白名單"
        val col = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20f), dp(24f), dp(20f), dp(24f)); setBackgroundColor(Color.rgb(255, 250, 240)) }
        fun text(s: String, size: Float = 15f) = TextView(this).apply { text = s; textSize = size; setTextColor(Color.rgb(80, 55, 40)); setPadding(0, dp(6f), 0, dp(6f)) }
        fun btn(s: String, on: () -> Unit) = Button(this).apply { text = s; isAllCaps = false; minHeight = dp(48f); setOnClickListener { on() } }
        col.addView(text("自啟動／省電白名單", 22f))
        col.addView(text("部分手機會喺背景殺咗團絨。跟以下步驟設定一次就得。\n裝置：${Build.MANUFACTURER} ${Build.MODEL}（Android ${Build.VERSION.RELEASE}）", 14f))
        col.addView(text(steps()))
        col.addView(btn("開自啟動設定") {
            if (!tryStart(candidates())) { Toast.makeText(this, "呢部機冇專用頁，開 app 資料頁", Toast.LENGTH_SHORT).show(); tryStart(listOf(appDetails())) }
        })
        val pm = getSystemService(POWER_SERVICE) as PowerManager
        col.addView(btn(if (pm.isIgnoringBatteryOptimizations(packageName)) "忽略電池最佳化（✓ 已開）" else "忽略電池最佳化") {
            @Suppress("BatteryLife")
            val ok = tryStart(listOf(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, Uri.parse("package:$packageName")),
                Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)))
            if (!ok) tryStart(listOf(appDetails()))
        })
        col.addView(btn("App 資料頁") { tryStart(listOf(appDetails())) })
        col.addView(btn("返回") { finish() })
        setContentView(ScrollView(this).apply { addView(col, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)) })
    }
}
