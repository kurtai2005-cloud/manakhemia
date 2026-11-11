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
import android.widget.CheckBox
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
        col.addView(text("團絨會喺其他 app／桌面上面行。撚一下回頭，撚兩下開返遊戲，拖動可以拎起（快快拋出有慣性），長按出選單。頭頂會顯示遊戲入面嘅心情、瞓覺同需求。返入遊戲時會自動收埋。", 14f))
        status = text("", 14f); col.addView(status)
        col.addView(btn("開浮動團絨") { requestStart() })
        col.addView(text("活動模式", 17f, true))
        val rg = RadioGroup(this)
        val modes = listOf(PetPrefs.MODE_EDGE to "沿底邊行（預設）", PetPrefs.MODE_FREE to "全畫面自由行（避開狀態列／導航列）", PetPrefs.MODE_PIN to "定點（企定）")
        val cur = PetPrefs.mode(this)
        modes.forEachIndexed { i, (m, l) ->
            rg.addView(RadioButton(this).apply { id = 100 + i; text = l; textSize = 15f; minHeight = dp(48f); isChecked = m == cur })
        }
        rg.setOnCheckedChangeListener { _, id ->
            val m = modes[id - 100].first
            PetPrefs.setMode(this, m)
            PetOverlayService.send(this, PetOverlayService.ACTION_SET_MODE, m)
        }
        col.addView(rg)
        // 玩圖示（Kurt 10-31 批）：團絨偶爾走去主畫面 icon 格坐／聞／撥／彈。只估格位，唔讀其他 app。
        col.addView(text("玩圖示（主畫面 icon 格：行×列）", 17f, true))
        val gr = RadioGroup(this)
        val grids = listOf("4x6" to "4×6（預設）", "4x5" to "4×5", "5x5" to "5×5", "5x6" to "5×6", "off" to "唔玩")
        val curG = PetPrefs.grid(this)
        grids.forEachIndexed { i, (g, l) -> gr.addView(RadioButton(this).apply { id = 200 + i; text = l; textSize = 15f; minHeight = dp(48f); isChecked = g == curG }) }
        gr.setOnCheckedChangeListener { _, id -> PetPrefs.setGrid(this, grids[id - 200].first) }
        col.addView(gr)
        addSurprise(col, ::text)
        col.addView(btn("關閉浮動團絨") { PetPrefs.setEnabled(this, false); PetOverlayService.send(this, PetOverlayService.ACTION_STOP); refresh() })
        col.addView(btn("自啟動／省電白名單設定") { startActivity(Intent(this, PowerGuideActivity::class.java)) })
        col.addView(text("測試", 17f, true))
        col.addView(btn("即刻瞌（模擬 60 分鐘冇互動）") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_DOZE) })
        col.addView(btn("即刻去玩圖示") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_PLAY) })
        // systems12 測試：即刻出（唔理計時／冷卻；入帳照跟遊戲上限）
        col.addView(btn("即刻掉星星碎") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_S12, "drop") })
        col.addView(btn("即刻飲水提醒") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_S12, "water") })
        col.addView(btn("即刻早瞓提醒") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_S12, "sleep") })
        col.addView(btn("即刻講心聲") { PetOverlayService.send(this, PetOverlayService.ACTION_DEBUG_S12, "voice") })
        col.addView(btn("返遊戲") { finish() })
        setContentView(ScrollView(this).apply { addView(col, ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)) })
    }

    /** systems12 小驚喜（同遊戲設定同步：後改贏）：星星碎（預設開）、飲水提醒、早瞓提醒（預設閂）＋間隔／時間。 */
    private fun addSurprise(col: LinearLayout, tx: (String, Float, Boolean) -> TextView) {
        val sn = PetPrefs.snapshotSys12(this)
        val cur = PetSys12.settings(sn?.surp, PetPrefs.surpLocal(this)) ?: PetSys12.Settings(mapOf("drop" to true, "water" to false, "sleep" to false), 2, "23:00", 0L)
        col.addView(tx("小驚喜", 17f, true))
        if (sn == null) col.addView(tx("（開一次遊戲之後先會同步親密度同設定）", 13f, false))
        val labels = listOf("drop" to "星星碎（每 2–4 個鐘掉一粒，撳執起）", "water" to "飲水提醒", "sleep" to "早瞓提醒")
        labels.forEachIndexed { i, (k, l) ->
            col.addView(CheckBox(this).apply { id = 300 + i; text = l; textSize = 15f; minHeight = dp(48f); isChecked = cur.on[k] == true; tag = "surp-$k"
                setOnCheckedChangeListener { _, on -> PetPrefs.setSurp(this@SettingsActivity, k, on) } })
        }
        col.addView(tx("飲水提醒間隔", 15f, false))
        val wg = RadioGroup(this).apply { orientation = RadioGroup.HORIZONTAL }
        listOf(1, 2, 3).forEachIndexed { i, hh -> wg.addView(RadioButton(this).apply { id = 400 + i; text = "${hh} 個鐘"; textSize = 15f; minHeight = dp(48f); isChecked = cur.waterH == hh }) }
        wg.setOnCheckedChangeListener { _, id -> PetPrefs.setSurp(this, "waterH", listOf(1, 2, 3)[id - 400]) }
        col.addView(wg)
        col.addView(tx("早瞓提醒時間", 15f, false))
        val times = listOf("22:00", "22:30", "23:00", "23:30", "00:00")
        val sg = RadioGroup(this)
        times.forEachIndexed { i, tm -> sg.addView(RadioButton(this).apply { id = 500 + i; text = tm; textSize = 15f; minHeight = dp(48f); isChecked = cur.sleepAt == tm }) }
        sg.setOnCheckedChangeListener { _, id -> PetPrefs.setSurp(this, "sleepAt", times[id - 500]) }
        col.addView(sg)
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
