package hk.vizard.glimmer.fpet

import android.Manifest
import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.util.TypedValue
import android.view.Gravity
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.RadioButton
import android.widget.RadioGroup
import android.widget.ScrollView
import android.widget.TextView

/** 浮動團絨設定頁：開／關、模式（沿底邊行／全畫面自由行／定點）、權限引導。 */
class SettingsActivity : Activity() {
    private lateinit var status: TextView
    private var wantStart = false
    private fun dp(v: Float) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, resources.displayMetrics).toInt()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        title = "浮動團絨"
        val col = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(20f), dp(24f), dp(20f), dp(24f)); setBackgroundColor(Color.rgb(255, 250, 240)) }
        fun text(s: String, size: Float = 15f, bold: Boolean = false) = TextView(this).apply {
            text = s; textSize = size; setTextColor(Color.rgb(80, 55, 40)); if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
            setPadding(0, dp(6f), 0, dp(6f)) }
        fun btn(s: String, on: () -> Unit) = Button(this).apply { text = s; isAllCaps = false; minHeight = dp(48f); setOnClickListener { on() } }
        col.addView(text("浮動團絨（測試版）", 22f, true))
        col.addView(text("團絨會喺其他 app／桌面上面行。撚一下回頭，撚兩下開返遊戲，拖動可以拎起，長按出選單。返入遊戲時會自動收埋。", 14f))
        status = text("", 14f); col.addView(status)
        col.addView(btn("開浮動團絨") { requestStart() })
        col.addView(text("活動模式", 17f, true))
        val rg = RadioGroup(this)
        val modes = listOf(PetPrefs.MODE_EDGE to "沿底邊行（預設）", PetPrefs.MODE_FREE to "全畫面自由行（避開狀態列／導航列）", PetPrefs.MODE_PIN to "定點（企定）")
        val cur = PetPrefs.mode(this)
        modes.forEachIndexed { i, (m, l) ->
            rg.addView(RadioButton(this).apply { id = 100 + i; text = l; textSize = 15f; minHeight = dp(44f); isChecked = m == cur })
        }
        rg.setOnCheckedChangeListener { _, id ->
            val m = modes[id - 100].first
            PetPrefs.setMode(this, m)
            PetOverlayService.send(this, PetOverlayService.ACTION_SET_MODE, m)
        }
        col.addView(rg)
        col.addView(btn("關閉浮動團絨") { PetPrefs.setEnabled(this, false); PetOverlayService.send(this, PetOverlayService.ACTION_STOP); refresh() })
        col.addView(btn("自啟動／省電白名單設定") { startActivity(Intent(this, PowerGuideActivity::class.java)) })
        col.addView(text("測試", 17f, true))
        col.addView(btn("即刻瞌（模擬 60 分鐘冇互動）") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_DOZE) })
        col.addView(btn("返遊戲") { finish() })
        setContentView(ScrollView(this).apply { addView(col, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)) })
    }

    override fun onResume() {
        super.onResume()
        if (wantStart && Settings.canDrawOverlays(this)) { wantStart = false; doStart() }
        refresh()
    }

    private fun refresh() {
        val ov = Settings.canDrawOverlays(this)
        val notif = Build.VERSION.SDK_INT < 33 || checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        status.text = "懸浮窗權限：${if (ov) "✓ 已授權" else "✗ 未授權"}\n通知權限：${if (notif) "✓" else "✗（唔影響團絨，只係睇唔到常駐通知）"}\n狀態：${if (PetOverlayService.running) "運行中" else "未開"}　形態：${PetPrefs.snapshotForm(this)}"
    }

    private fun requestStart() {
        if (!Settings.canDrawOverlays(this)) {
            AlertDialog.Builder(this).setTitle("需要「顯示喺其他 app 上面」")
                .setMessage("團絨要喺桌面同其他 app 上面行，請喺下一頁搵「微光小圃」，開「允許顯示喺其他應用程式上面」，然後撳返回。")
                .setPositiveButton("去設定") { _, _ ->
                    wantStart = true
                    startActivity(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
                }.setNegativeButton("取消", null).show()
            return
        }
        doStart()
    }

    private fun doStart() {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED)
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 7)
        PetOverlayService.start(this)
        status.postDelayed({ refresh() }, 400)
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) { refresh() }
}
