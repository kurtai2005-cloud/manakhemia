package hk.vizard.glimmer.fpet

import android.annotation.SuppressLint
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.SharedPreferences
import android.content.pm.ServiceInfo
import android.content.res.Configuration
import android.graphics.Color
import android.graphics.PixelFormat
import android.graphics.Rect
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.SystemClock
import android.provider.Settings
import android.util.Log
import android.util.TypedValue
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewConfiguration
import android.view.WindowInsets
import android.view.WindowManager
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import kotlin.math.abs
import kotlin.math.hypot
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.random.Random

/**
 * 前景服務＋TYPE_APPLICATION_OVERLAY。團絨視窗只包住一格，用 updateViewLayout 搬。
 * 模式：沿底邊行（預設）／全畫面自由行／定點。≤15fps，熄屏停，瞌時 2fps。
 */
class PetOverlayService : Service() {
    companion object {
        const val TAG = "FloatingPet"
        const val ACTION_START = "hk.vizard.glimmer.fpet.START"
        const val ACTION_STOP = "hk.vizard.glimmer.fpet.STOP"
        const val ACTION_SET_MODE = "hk.vizard.glimmer.fpet.SET_MODE"
        const val ACTION_DEBUG_DOZE = "hk.vizard.glimmer.fpet.DEBUG_DOZE"
        const val ACTION_DEBUG_PLAY = "hk.vizard.glimmer.fpet.DEBUG_PLAY"   // 測試：即刻去玩圖示
        const val ACTION_SET_GRID = "hk.vizard.glimmer.fpet.SET_GRID"
        const val EXTRA_MODE = "mode"
        const val CHANNEL = "fpet"
        const val NOTIF_ID = 4201
        @Volatile var running = false

        fun start(c: Context, action: String = ACTION_START, mode: String? = null) {
            val i = Intent(c, PetOverlayService::class.java).setAction(action)
            if (mode != null) i.putExtra(EXTRA_MODE, mode)
            if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i) else c.startService(i)
        }
        fun send(c: Context, action: String, mode: String? = null) {
            if (!running) return
            val i = Intent(c, PetOverlayService::class.java).setAction(action)
            if (mode != null) i.putExtra(EXTRA_MODE, mode)
            c.startService(i)
        }
    }

    // EMOTE＝播一段 clip（心情／需求／玩圖示動作）；GO_ICON＝行去 icon 格；FLING＝自由行／定點模式拋出滑行（冇重力）
    private enum class St { IDLE, WALK, TURN, HAPPY, DRAG, FALL, DOZE_IN, ASLEEP, WAKE, EMOTE, GO_ICON, FLING }

    private val h = Handler(Looper.getMainLooper())
    private lateinit var wm: WindowManager
    private var view: PetView? = null
    private var lp: WindowManager.LayoutParams? = null
    private var menu: View? = null
    private lateinit var atlas: PetAtlas
    private var scale = 3
    private val safe = Rect()
    private val screen = Rect()

    // 狀態（螢幕 px，feet＝腳底 pivot；拖動時 anchor＝手指＝grab）
    private var st = St.IDLE
    private var feetX = 0f; private var feetY = 0f
    private var fingerX = 0f; private var fingerY = 0f
    private var tgtX = 0f; private var tgtY = 0f
    private var vy = 0f; private var groundY = 0f; private var bounces = 0
    private var facingLeft = false
    private var clip: PetClip? = null
    private var clipT = 0f
    private var stTimer = 0f
    private var lastInteract = SystemClock.elapsedRealtime()
    private var lastTick = 0L
    private var screenOn = true
    private var appVisible = false
    private var ticking = false
    private var mode = PetPrefs.MODE_EDGE

    // ── 同步遊戲狀況（snapshot v3）＋頭頂圖示 ──
    private var snap: PetStatus.Snap? = null
    private var status = PetStatus.Status.NONE
    private var statusAt = 0L
    private var dozeByGame = false
    private var fxAtlas: PetAtlas? = null
    private var fx: FxView? = null
    private var fxLp: WindowManager.LayoutParams? = null
    private var fxT = 0f
    private var tapFx: String? = null; private var tapFxT = 0f
    private var headTop = 0; private var headRight = 0   // idle 第 1 幀實際像素 bbox（頭頂／右緣，art px）
    // ── 懸浮互動 ──
    private var vx = 0f
    private var emoteNext: (() -> Unit)? = null
    private var playAct: String? = null
    private var nextPlayAt = SystemClock.elapsedRealtime() + 20_000L
    // 拋出速度：自己記最近幾個 (t,x,y)（raw 座標，因為視窗跟手指郁）；唔用 VelocityTracker，佢遇到 >40ms 嘅間隔會當停咗手
    private val vT = LongArray(8); private val vX = FloatArray(8); private val vY = FloatArray(8); private var vN = 0

    private fun dp(v: Float) = TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, resources.displayMetrics)

    // ── lifecycle ──
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        wm = getSystemService(WINDOW_SERVICE) as WindowManager
        val f = IntentFilter().apply { addAction(Intent.ACTION_SCREEN_OFF); addAction(Intent.ACTION_SCREEN_ON); addAction(Intent.ACTION_USER_PRESENT) }
        registerReceiver(screenRx, f)
        PetPrefs.cap(this).registerOnSharedPreferenceChangeListener(snapRx)
        GlimmerApp.visibilityListener = { vis -> h.post { setAppVisible(vis) } }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        try {
            if (Build.VERSION.SDK_INT >= 29) ServiceCompat.startForeground(this, NOTIF_ID, buildNotif(),
                if (Build.VERSION.SDK_INT >= 34) ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE else 0)
            else startForeground(NOTIF_ID, buildNotif())
        } catch (e: Exception) {
            Log.w(TAG, "startForeground failed: $e"); stopSelf(); return START_NOT_STICKY
        }
        if (!Settings.canDrawOverlays(this)) { Log.w(TAG, "no overlay permission"); PetPrefs.setEnabled(this, false); stopSelf(); return START_NOT_STICKY }
        when (intent?.action) {
            ACTION_STOP -> { PetPrefs.setEnabled(this, false); stopSelf(); return START_NOT_STICKY }
            ACTION_SET_MODE -> intent.getStringExtra(EXTRA_MODE)?.let { PetPrefs.setMode(this, it); if (view != null) applyMode(it) }
            ACTION_DEBUG_DOZE -> if (view != null) { lastInteract = 0; if (st != St.DRAG) doze() }
            ACTION_DEBUG_PLAY -> if (view != null && st != St.DRAG) { nextPlayAt = 0; startIconPlay() }
            ACTION_SET_GRID -> intent.getStringExtra(EXTRA_MODE)?.let { PetPrefs.setGrid(this, it) }
        }
        PetPrefs.setEnabled(this, true)
        running = true
        if (view == null) attach()
        return START_STICKY
    }

    override fun onDestroy() {
        running = false
        h.removeCallbacksAndMessages(null)
        try { unregisterReceiver(screenRx) } catch (_: Exception) {}
        PetPrefs.cap(this).unregisterOnSharedPreferenceChangeListener(snapRx)
        GlimmerApp.visibilityListener = null
        hideMenu()
        view?.let { try { wm.removeView(it) } catch (_: Exception) {} }
        view = null
        fx?.let { try { wm.removeView(it) } catch (_: Exception) {} }
        fx = null
        super.onDestroy()
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        super.onConfigurationChanged(newConfig)
        h.postDelayed({ computeBounds(); clampAfterBounds(); place() }, 300)
    }

    // ── notification ──
    private fun buildNotif(): Notification {
        val nm = getSystemService(NOTIFICATION_SERVICE) as NotificationManager
        if (Build.VERSION.SDK_INT >= 26 && nm.getNotificationChannel(CHANNEL) == null)
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "浮動團絨", NotificationManager.IMPORTANCE_LOW).apply { setShowBadge(false) })
        val pf = PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        val open = PendingIntent.getActivity(this, 0, Intent(this, SettingsActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK), pf)
        val stop = PendingIntent.getService(this, 1, Intent(this, PetOverlayService::class.java).setAction(ACTION_STOP), pf)
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(R.drawable.ic_stat_pet)
            .setContentTitle("團絨喺外面散步緊")
            .setContentText("撳呢度改設定")
            .setOngoing(true).setSilent(true)
            .setContentIntent(open)
            .addAction(0, "收起團絨", stop)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    // ── window ──
    @SuppressLint("ClickableViewAccessibility")
    private fun attach() {
        mode = PetPrefs.mode(this)
        loadAtlas(PetPrefs.snapshotForm(this))
        computeBounds()
        val v = PetView(this) { e -> onPetTouch(e) }
        v.atlas = atlas; v.scale = scale
        val px = atlas.size * scale
        val p = WindowManager.LayoutParams(px, px,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT)
        p.gravity = Gravity.TOP or Gravity.START
        if (Build.VERSION.SDK_INT >= 28) p.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        if (Build.VERSION.SDK_INT >= 30) p.setFitInsetsTypes(0)
        p.title = "FloatingPet"
        // 初始位置
        val pin = PetPrefs.pin(this)
        feetX = (safe.left + safe.right) / 2f
        feetY = groundEdge()
        if (mode == PetPrefs.MODE_PIN && pin != null) { feetX = pin.first; feetY = pin.second }
        clampFeet()
        view = v; lp = p
        play("idle"); st = St.IDLE; stTimer = 1.5f
        frameToView()
        p.x = winX(); p.y = winY()
        wm.addView(v, p)
        attachFx()
        appVisible = GlimmerApp.visible
        v.visibility = if (appVisible) View.GONE else View.VISIBLE
        fx?.visibility = v.visibility
        refreshStatus(true)
        lastInteract = SystemClock.elapsedRealtime()
        startTicking()
        Log.i(TAG, "attached form=${atlas.form} mode=$mode scale=$scale safe=$safe")
    }

    private fun loadAtlas(form: String) {
        atlas = PetAtlas.load(this, form)
        val target = dp(try { org.json.JSONObject(PetPrefs.cap(this).getString(PetPrefs.KEY_SNAPSHOT, null) ?: "{}").optDouble("sizeDp", Double.NaN).toFloat().takeIf { it.isFinite() && it > 0f } } catch (e: Exception) { null } ?: if (form == "sprout") 52f else 72f)   // 顯示大細（dp）：evo6 snapshot v2 sizeDp 跟階段；舊 snapshot 冇 sizeDp → 舊尺寸
        scale = max(1, (target / atlas.size).roundToInt())
        // 頭頂圖示位：idle 第 1 幀實際像素 bbox
        val f0 = atlas.clip("idle").frames[0]; var top = atlas.size; var right = 0
        for (y in 0 until atlas.size) for (x in 0 until atlas.size) if ((atlas.bitmap.getPixel(f0.src.left + x, f0.src.top + y) ushr 24) > 40) { if (y < top) top = y; if (x > right) right = x }
        headTop = if (top >= atlas.size) atlas.size / 3 else top; headRight = if (right == 0) atlas.size * 3 / 4 else right
    }

    // 懸浮窗即時變大細（Kurt 10-31 批）：form 唔同，或者同 form 但 snapshot sizeDp 計出嘅 scale 唔同 → 都要 swapForm（同 loadAtlas 一樣計法）
    private fun needSwap(form: String): Boolean {
        if (form != atlas.form) return true
        val target = dp(try { org.json.JSONObject(PetPrefs.cap(this).getString(PetPrefs.KEY_SNAPSHOT, null) ?: "{}").optDouble("sizeDp", Double.NaN).toFloat().takeIf { it.isFinite() && it > 0f } } catch (e: Exception) { null } ?: if (form == "sprout") 52f else 72f)
        val s = max(1, (target / atlas.size).roundToInt())
        if (s != scale) Log.i(TAG, "resize form=$form scale $scale → $s")
        return s != scale
    }

    private fun computeBounds() {
        if (Build.VERSION.SDK_INT >= 30) {
            val m = wm.currentWindowMetrics
            screen.set(m.bounds)
            val ins = m.windowInsets.getInsetsIgnoringVisibility(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout())
            safe.set(screen.left + ins.left, screen.top + ins.top, screen.right - ins.right, screen.bottom - ins.bottom)
        } else {
            val dm = android.util.DisplayMetrics()
            @Suppress("DEPRECATION") wm.defaultDisplay.getRealMetrics(dm)
            screen.set(0, 0, dm.widthPixels, dm.heightPixels)
            fun dim(n: String): Int { val id = resources.getIdentifier(n, "dimen", "android"); return if (id > 0) resources.getDimensionPixelSize(id) else 0 }
            safe.set(0, dim("status_bar_height"), dm.widthPixels, dm.heightPixels - dim("navigation_bar_height"))
        }
    }

    // 腳底 pivot（idle 第 1 幀）
    private val footPx get() = atlas.clip("idle").frames[0].px
    private val footPy get() = atlas.clip("idle").frames[0].py
    private fun minFeetX() = safe.left + footPx * scale.toFloat()
    private fun maxFeetX() = safe.right - (atlas.size - footPx) * scale.toFloat()
    private fun minFeetY() = safe.top + footPy * scale.toFloat()
    private fun maxFeetY() = safe.bottom - (atlas.size - footPy) * scale.toFloat()
    private fun groundEdge() = maxFeetY()
    private fun clampFeet() {
        feetX = feetX.coerceIn(minFeetX(), max(minFeetX(), maxFeetX()))
        feetY = feetY.coerceIn(minFeetY(), max(minFeetY(), maxFeetY()))
    }
    private fun clampAfterBounds() {
        clampFeet()
        if (mode == PetPrefs.MODE_EDGE && st != St.DRAG && st != St.FALL) feetY = groundEdge()
    }

    private fun curFrame(): PetFrame {
        val c = clip ?: atlas.clip("idle")
        var i = (clipT * c.fps).toInt()
        i = if (c.loop) i % c.frames.size else min(i, c.frames.size - 1)
        return c.frames[i]
    }
    private fun clipDone() = clip?.let { !it.loop && clipT >= it.duration } ?: true
    private fun play(name: String) { clip = atlas.clip(name); clipT = 0f }

    private fun winX(): Int {
        val f = curFrame()
        val ax = if (st == St.DRAG) fingerX else feetX
        return (ax - f.px * scale).roundToInt()
    }
    private fun winY(): Int {
        val f = curFrame()
        val ay = if (st == St.DRAG) fingerY else feetY
        return (ay - f.py * scale).roundToInt()
    }
    private fun frameToView() { view?.show(curFrame(), facingLeft) }
    private fun place() {
        val v = view ?: return; val p = lp ?: return
        frameToView()
        val nx = winX(); val ny = winY()
        if (nx != p.x || ny != p.y) { p.x = nx; p.y = ny; try { wm.updateViewLayout(v, p) } catch (_: Exception) {} }
        placeFx()
    }

    // ── ticking（≤15fps；瞌 2fps；熄屏／app 前台停） ──
    private val tickR = object : Runnable {
        override fun run() {
            if (!ticking) return
            val now = SystemClock.uptimeMillis()
            val dt = ((now - lastTick).coerceIn(0, 250)) / 1000f
            lastTick = now
            tick(dt)
            h.postDelayed(this, tickDelay())   // 省電：瞓 2fps、企定／坐 ≈7fps、郁緊 15fps
        }
    }
    private fun startTicking() {
        if (ticking || !screenOn || appVisible || view == null) return
        ticking = true; lastTick = SystemClock.uptimeMillis(); h.post(tickR)
    }
    private fun stopTicking() { ticking = false; h.removeCallbacks(tickR) }

    private val screenRx = object : BroadcastReceiver() {
        override fun onReceive(c: Context, i: Intent) {
            when (i.action) {
                Intent.ACTION_SCREEN_OFF -> { screenOn = false; stopTicking(); Log.i(TAG, "screen off → stop drawing") }
                else -> { screenOn = true; startTicking() }
            }
        }
    }

    private fun setAppVisible(vis: Boolean) {
        appVisible = vis
        val v = view ?: return
        if (vis) { hideMenu(); v.visibility = View.GONE; fx?.visibility = View.GONE; stopTicking() }
        else {
            // 返嚟可能已轉形態／改模式
            val f = PetPrefs.snapshotForm(this)
            if (needSwap(f)) swapForm(f)
            val m = PetPrefs.mode(this); if (m != mode) applyMode(m)
            refreshStatus(true)
            v.visibility = View.VISIBLE; fx?.visibility = View.VISIBLE; startTicking()
        }
    }

    private val snapRx = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key == PetPrefs.KEY_SNAPSHOT) h.post { val f = PetPrefs.snapshotForm(this); if (view != null && needSwap(f)) swapForm(f); refreshStatus(true) }
    }

    private fun swapForm(form: String) {
        val v = view ?: return; val p = lp ?: return
        loadAtlas(form)
        v.atlas = atlas; v.scale = scale
        p.width = atlas.size * scale; p.height = atlas.size * scale
        clip = atlas.clip(clip?.name ?: "idle")
        clampAfterBounds()
        try { wm.updateViewLayout(v, p) } catch (_: Exception) {}
        place(); v.invalidate()
        Log.i(TAG, "form → $form")
    }

    private fun tick(dt: Float) {
        clipT += dt
        val dozeMs = PetPrefs.dozeMinutes(this) * 60_000L
        refreshStatus(false)
        val now = SystemClock.elapsedRealtime()
        // 遊戲入面瞓緊 → 團絨都瞓（撚醒佢會醒一陣，6 秒冇郁又再瞓）；遊戲醒咗 → 跟住醒
        if (status.sleeping && (st == St.IDLE || st == St.WALK || st == St.EMOTE) && now - lastInteract > 6000) { doze(); dozeByGame = true; Log.i(TAG, "game sleeping → doze"); return }
        if (!status.sleeping && dozeByGame && (st == St.ASLEEP || st == St.DOZE_IN)) { dozeByGame = false; st = St.WAKE; play("wake"); Log.i(TAG, "game woke → wake") }
        when (st) {
            St.IDLE -> {
                stTimer -= dt
                if (now - lastInteract > dozeMs) { doze(); return }
                if (stTimer <= 0) idleNext()
            }
            St.EMOTE -> { stTimer -= dt; if (stTimer <= 0 && (clip?.loop == true || clipDone())) { val n = emoteNext; emoteNext = null; if (n != null) n() else toIdle(1.5f) } }
            St.GO_ICON -> {
                val speed = 26f * scale
                val dx = tgtX - feetX; val dy = tgtY - feetY; val d = hypot(dx, dy)
                if (d <= speed * dt || d < 1f) { feetX = tgtX; feetY = tgtY; doIconAct() }
                else { feetX += dx / d * speed * dt; feetY += dy / d * speed * dt; if (abs(dx) > 2f) facingLeft = dx < 0 }
            }
            St.FLING -> {
                // 自由行／定點：拋出滑行（摩擦減速），撞四邊彈返
                feetX += vx * dt; feetY += vy * dt
                val k = Math.exp(-2.6 * dt).toFloat(); vx *= k; vy *= k
                if (feetX < minFeetX()) { feetX = minFeetX(); vx = abs(vx) * 0.6f } else if (feetX > maxFeetX()) { feetX = maxFeetX(); vx = -abs(vx) * 0.6f }
                if (feetY < minFeetY()) { feetY = minFeetY(); vy = abs(vy) * 0.6f } else if (feetY > maxFeetY()) { feetY = maxFeetY(); vy = -abs(vy) * 0.6f }
                if (hypot(vx, vy) < dp(40f)) { vx = 0f; vy = 0f; landed() }
            }
            St.WALK -> {
                if (now - lastInteract > dozeMs) { doze(); return }
                val speed = 20f * scale     // 12px／6 幀 @10fps ≈ 20 art px/s
                val dx = tgtX - feetX; val dy = tgtY - feetY; val d = hypot(dx, dy)
                if (d <= speed * dt || d < 1f) {
                    feetX = tgtX; feetY = tgtY
                    if (sideSit) { sideSit = false; facingLeft = feetX > (minFeetX() + maxFeetX()) / 2; toIdle(Random.nextDouble(5.0, 9.0).toFloat()) }   // 坐喺邊，面向入面
                    else toIdle(Random.nextDouble(2.0, 5.0).toFloat())
                } else {
                    feetX += dx / d * speed * dt; feetY += dy / d * speed * dt
                    if (abs(dx) > 2f) facingLeft = dx < 0
                }
            }
            St.TURN -> if (clipDone()) {
                // 撚佢反應跟心情：開心＝emo_happy＋心心；唔開心＝droop＋汗；有需求＝氣泡（照舊回頭先）
                if (status.moodBand == "sad") { st = St.HAPPY; play(if (atlas.clips.containsKey("droop")) "droop" else "emo_happy"); stTimer = 1.6f; showTapFx("sweat") }
                else { st = St.HAPPY; play("emo_happy"); stTimer = 1.0f; showTapFx("heart") }
            }
            St.HAPPY -> { stTimer -= dt; if (stTimer <= 0) toIdle(1.5f) }
            St.DRAG -> if (clip?.name == "picked_up_enter" && clipDone()) play("picked_up")
            St.FALL -> {
                vy += dp(2200f) * dt
                feetY += vy * dt
                // 拋出（沿底邊行模式）：有橫向慣性，撞左右／頂邊彈返
                if (vx != 0f) {
                    feetX += vx * dt
                    if (feetX < minFeetX()) { feetX = minFeetX(); vx = abs(vx) * 0.55f } else if (feetX > maxFeetX()) { feetX = maxFeetX(); vx = -abs(vx) * 0.55f }
                    if (abs(vx) > 2f) facingLeft = vx < 0
                }
                if (feetY < minFeetY()) { feetY = minFeetY(); vy = abs(vy) * 0.5f }
                if (feetY >= groundY) {
                    feetY = groundY
                    if (bounces < (if (vx != 0f) 3 else 1) && vy > dp(250f)) { vy = -vy * 0.35f; bounces++; vx *= 0.7f }
                    else { vx = 0f; landed() }
                }
            }
            St.DOZE_IN -> if (clipDone()) { st = St.ASLEEP; play("sleep_loop"); Log.i(TAG, "asleep (2fps)") }
            St.ASLEEP -> {}
            St.WAKE -> if (clipDone()) toIdle(1.5f)
        }
        place()
        tickFx(dt)
    }

    private fun toIdle(t: Float) { st = St.IDLE; play("idle"); stTimer = t }

    private var sideSit = false
    private fun startWalk() {
        sideSit = false
        when (mode) {
            PetPrefs.MODE_EDGE -> {
                feetY = groundEdge()
                if (Random.nextFloat() < 0.25f) {   // 沿底邊行去左／右角，坐喺邊
                    sideSit = true; tgtX = if (feetX > (minFeetX() + maxFeetX()) / 2) minFeetX() else maxFeetX(); tgtY = feetY
                    st = St.WALK; play("walk"); return
                }
                val span = maxFeetX() - minFeetX()
                var x = minFeetX() + Random.nextFloat() * span
                if (abs(x - feetX) < dp(40f)) x = if (feetX > (minFeetX() + maxFeetX()) / 2) feetX - dp(80f) else feetX + dp(80f)
                tgtX = x.coerceIn(minFeetX(), maxFeetX()); tgtY = feetY
            }
            PetPrefs.MODE_FREE -> {
                tgtX = minFeetX() + Random.nextFloat() * (maxFeetX() - minFeetX())
                tgtY = minFeetY() + Random.nextFloat() * (maxFeetY() - minFeetY())
                if (Random.nextFloat() < 0.2f) { sideSit = true; tgtX = if (feetX > (minFeetX() + maxFeetX()) / 2) maxFeetX() else minFeetX() }   // 行去左／右邊坐
                // 每段唔好行太遠
                val dx = tgtX - feetX; val dy = tgtY - feetY; val d = hypot(dx, dy); val lim = dp(220f)
                if (d > lim) { tgtX = feetX + dx / d * lim; tgtY = feetY + dy / d * lim }
            }
            else -> return
        }
        st = St.WALK; play("walk")
    }

    private fun doze() { hideMenu(); dozeByGame = false; st = St.DOZE_IN; play("fall_asleep"); Log.i(TAG, "dozing (no interaction ${PetPrefs.dozeMinutes(this)} min)") }

    private fun landed() {
        bounces = 0; vy = 0f
        if (mode == PetPrefs.MODE_PIN) PetPrefs.setPin(this, feetX, feetY)
        toIdle(if (mode == PetPrefs.MODE_PIN) 3f else 1.2f)
    }

    private fun applyMode(m: String) {
        mode = m; PetPrefs.setMode(this, m)
        Log.i(TAG, "mode → $m")
        if (st == St.DRAG) return
        when (m) {
            PetPrefs.MODE_EDGE -> if (feetY < groundEdge() - 1) { st = St.FALL; play("idle"); groundY = groundEdge(); vy = 0f; bounces = 0 } else toIdle(0.8f)
            PetPrefs.MODE_PIN -> { PetPrefs.setPin(this, feetX, feetY); toIdle(3f) }
            else -> toIdle(0.8f)
        }
    }

    // ── 觸控：撚一下回頭（等 250ms 雙擊判定）、撚兩下開 game、拖動、長按選單 ──
    private var downX = 0f; private var downY = 0f
    private var dragging = false; private var longFired = false; private var tapPending = false
    private val slop by lazy { ViewConfiguration.get(this).scaledTouchSlop.toFloat() }
    private val longR = Runnable { longFired = true; interact(); showMenu() }
    private val singleTapR = Runnable { tapPending = false; onSingleTap() }

    private fun onPetTouch(e: MotionEvent): Boolean {
        when (e.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                vN = 0; trackV(e)
                downX = e.rawX; downY = e.rawY; dragging = false; longFired = false
                hideMenu()
                h.postDelayed(longR, ViewConfiguration.getLongPressTimeout().toLong())
            }
            MotionEvent.ACTION_MOVE -> {
                trackV(e)
                if (!dragging && !longFired && hypot(e.rawX - downX, e.rawY - downY) > slop) {
                    h.removeCallbacks(longR); startDrag(e.rawX, e.rawY)
                }
                if (dragging) { fingerX = e.rawX; fingerY = e.rawY; clampFinger(); place() }
            }
            MotionEvent.ACTION_UP -> {
                h.removeCallbacks(longR)
                when {
                    dragging -> { val v = flingV(e.eventTime); endDrag(v.first, v.second) }
                    longFired -> {}
                    tapPending -> { h.removeCallbacks(singleTapR); tapPending = false; onDoubleTap() }
                    else -> { tapPending = true; h.postDelayed(singleTapR, 250) }
                }
            }
            MotionEvent.ACTION_CANCEL -> { h.removeCallbacks(longR); if (dragging) endDrag() }
        }
        return true
    }

    private fun interact() { lastInteract = SystemClock.elapsedRealtime() }
    // 視窗跟手指郁，所以用 raw 座標計速度
    private fun trackV(e: MotionEvent) {
        if (vN == vT.size) { System.arraycopy(vT, 1, vT, 0, vN - 1); System.arraycopy(vX, 1, vX, 0, vN - 1); System.arraycopy(vY, 1, vY, 0, vN - 1); vN-- }
        vT[vN] = e.eventTime; vX[vN] = e.rawX; vY[vN] = e.rawY; vN++
    }
    /** 放手時速度 px/s：用最後 ~100ms 嘅位移；放手前停咗 >150ms 當冇拋 */
    private fun flingV(upT: Long): Pair<Float, Float> {
        if (vN < 2) return Pair(0f, 0f)
        val last = vN - 1
        if (upT - vT[last] > 150) return Pair(0f, 0f)
        var i = last - 1
        while (i > 0 && vT[last] - vT[i - 1] <= 100) i--
        val dt = (vT[last] - vT[i]).coerceAtLeast(8L) / 1000f
        return Pair((vX[last] - vX[i]) / dt, (vY[last] - vY[i]) / dt)
    }

    private fun clampFinger() {
        val f = curFrame()
        fingerX = fingerX.coerceIn(screen.left + f.px * scale.toFloat(), screen.right - (atlas.size - f.px) * scale.toFloat())
        fingerY = fingerY.coerceIn(screen.top + f.py * scale.toFloat(), screen.bottom - (atlas.size - f.py) * scale.toFloat())
    }

    private fun startDrag(x: Float, y: Float) {
        dragging = true; interact()
        st = St.DRAG; play(if (atlas.clips.containsKey("picked_up_enter")) "picked_up_enter" else "picked_up")   // faceOnEnter：第一個循環 surprised
        fingerX = x; fingerY = y; clampFinger()   // sprite 位置 = 手指 − grab
        place()
        Log.i(TAG, "drag start (picked_up, pivot=grab)")
    }

    private fun endDrag(flingX: Float = 0f, flingY: Float = 0f) {
        dragging = false; interact()
        val g = curFrame()
        // 由 grab 轉返腳底 pivot
        feetX = fingerX - g.px * scale + footPx * scale
        feetY = fingerY - g.py * scale + footPy * scale
        clampFeet()
        groundY = when (mode) {
            PetPrefs.MODE_EDGE -> groundEdge()
            else -> min(feetY + dp(14f), maxFeetY())
        }
        st = St.FALL; play("idle"); vy = 0f; vx = 0f; bounces = 0
        // 拋出（Kurt 10-31 批）：快速拖放有慣性；慢放照舊直跌
        val cap = dp(2600f); val fx0 = flingX.coerceIn(-cap, cap); val fy0 = flingY.coerceIn(-cap, cap)
        if (hypot(fx0, fy0) > dp(350f)) {
            if (mode == PetPrefs.MODE_EDGE) { vx = fx0; vy = fy0; groundY = groundEdge() }
            else { st = St.FLING; vx = fx0; vy = fy0 }
            Log.i(TAG, "fling v=(${fx0.roundToInt()},${fy0.roundToInt()}) px/s")
        } else Log.i(TAG, "drop v=(${fx0.roundToInt()},${fy0.roundToInt()}) px/s (慢放，直跌)")
        PetPrefs.appendQueue(this, "drag")
        Log.i(TAG, "drag end → fall to $groundY")
    }

    private fun onSingleTap() {
        interact()
        when (st) {
            St.ASLEEP, St.DOZE_IN -> { st = St.WAKE; play("wake"); emoteNext = null; PetPrefs.appendQueue(this, "wake"); Log.i(TAG, "wake") }
            St.DRAG, St.FALL, St.FLING -> {}
            else -> { st = St.TURN; play("turn_back"); PetPrefs.appendQueue(this, "tap"); Log.i(TAG, "tap → turn_back") }
        }
        place()
    }

    private fun onDoubleTap() {
        interact()
        Log.i(TAG, "double tap → open game")
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT))
    }

    // ── 心情／需求／玩圖示 ──
    private fun refreshStatus(force: Boolean) {
        val now = SystemClock.elapsedRealtime()
        if (!force && now - statusAt < 5000) return
        statusAt = now
        snap = PetPrefs.snapshotStatus(this)
        val n = PetStatus.project(snap, System.currentTimeMillis())
        if (n.moodBand != status.moodBand || n.sleeping != status.sleeping || n.urgent != status.urgent) Log.i(TAG, "status mood=${n.moodBand} sleeping=${n.sleeping} urgent=${n.urgent}")
        // 遊戲瞓緊／啱啱醒，而團絨已經瞓緊（例如自己瞌咗）→ 交俾遊戲狀態控制，遊戲一醒就跟住醒
        if ((n.sleeping || status.sleeping) && (st == St.ASLEEP || st == St.DOZE_IN)) dozeByGame = true
        status = n
    }

    private fun emote(name: String, minT: Float, next: (() -> Unit)? = null) {
        st = St.EMOTE; play(if (atlas.clips.containsKey(name)) name else "emo_happy"); stTimer = minT; emoteNext = next
    }

    private fun idleNext() {
        if (mode == PetPrefs.MODE_EDGE && feetY < groundEdge() - 1) { st = St.FALL; play("idle"); groundY = groundEdge(); vy = 0f; vx = 0f; bounces = 0; return }   // 玩圖示途中被打斷 → 跌返落底
        val r = Random.nextFloat()
        val now = SystemClock.elapsedRealtime()
        when {
            status.urgent != null && r < 0.35f -> emote(if (status.urgent == "hunger") "emo_hungry" else "droop", 3f)
            status.moodBand == "sad" && r < 0.35f -> emote("droop", 3f)
            status.moodBand == "happy" && r < 0.12f -> emote("cheer_jump", 0f) { emote("cheer_jump", 0f) }
            mode != PetPrefs.MODE_PIN && now >= nextPlayAt && r < 0.6f && PetPrefs.grid(this) != "off" -> startIconPlay()
            mode != PetPrefs.MODE_PIN -> startWalk()
            else -> stTimer = 3f
        }
    }

    /** 估主畫面 icon 格中心（col×row，dock 預留一行）。只係幾何估算，唔讀其他 app。 */
    private fun iconCells(): List<Pair<Float, Float>> {
        val g = PetPrefs.grid(this); if (g == "off") return emptyList()
        val (c, r) = g.split("x").map { it.toInt() }
        val w = safe.width().toFloat(); val hh = safe.height().toFloat()
        val top = safe.top + hh * 0.04f; val bottom = safe.bottom - hh / (r + 1.5f)
        val cw = w / c; val ch = (bottom - top) / r
        val out = ArrayList<Pair<Float, Float>>()
        for (j in 0 until r) for (i in 0 until c) out.add(Pair(safe.left + cw * (i + 0.5f), top + ch * (j + 0.5f)))
        return out
    }

    private fun startIconPlay() {
        nextPlayAt = SystemClock.elapsedRealtime() + Random.nextLong(45_000L, 120_000L)
        val cells = iconCells(); if (cells.isEmpty() || mode == PetPrefs.MODE_PIN) { startWalk(); return }
        val (cx, cy) = cells[Random.nextInt(cells.size)]
        val icon = min(safe.width() / 4f, dp(60f)) * 0.9f
        tgtX = cx.coerceIn(minFeetX(), max(minFeetX(), maxFeetX()))
        tgtY = (cy - icon * 0.45f).coerceIn(minFeetY(), max(minFeetY(), maxFeetY()))   // 腳底踩喺 icon 頂
        playAct = listOf("sit", "sniff", "swat", "hop")[Random.nextInt(4)]
        st = St.GO_ICON; play("walk")
        Log.i(TAG, "icon play → (${cx.roundToInt()},${cy.roundToInt()}) $playAct grid=${PetPrefs.grid(this)}")
    }

    private fun doIconAct() {
        val after: () -> Unit = {
            if (mode == PetPrefs.MODE_EDGE && feetY < groundEdge() - 1) { st = St.FALL; play("idle"); groundY = groundEdge(); vy = 0f; vx = 0f; bounces = 0 }   // 玩完跳返落底
            else toIdle(1.5f)
        }
        when (playAct) {
            "sniff" -> emote("sniff", 0f) { emote("sniff", 0f) { emote("idle", 1.5f, after) } }
            "swat" -> emote("swat", 0f) { emote("swat", 0f) { emote("idle", 1.2f, after) } }
            "hop" -> emote("cheer_jump", 0f) { emote("cheer_jump", 0f) { emote("idle", 1.2f, after) } }
            else -> emote("idle", Random.nextDouble(5.0, 9.0).toFloat(), after)   // 坐喺 icon 上面
        }
        Log.i(TAG, "icon act $playAct")
    }

    private fun tickDelay(): Long = when (st) {
        St.ASLEEP -> 500L
        St.IDLE -> 150L
        St.EMOTE -> if (clip?.name == "idle") 150L else max(67L, min(150L, (1000f / (clip?.fps ?: 6f)).toLong()))
        else -> 67L
    }

    // ── 頭頂圖示 overlay（唔收觸控） ──
    private fun fxScale() = max(2, dp(1.15f).roundToInt())
    private fun attachFx() {
        val a = try { PetAtlas.load(this, "fx") } catch (e: Exception) { Log.w(TAG, "fx atlas: $e"); null } ?: return
        fxAtlas = a
        val v = FxView(this, a).apply { scale = fxScale(); visibility = View.GONE }
        val px = a.size * v.scale
        val p = WindowManager.LayoutParams(px, px, WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN or WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            PixelFormat.TRANSLUCENT)
        p.gravity = Gravity.TOP or Gravity.START
        if (Build.VERSION.SDK_INT >= 28) p.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        if (Build.VERSION.SDK_INT >= 30) p.setFitInsetsTypes(0)
        p.title = "FloatingPetFx"
        try { wm.addView(v, p); fx = v; fxLp = p } catch (e: Exception) { Log.w(TAG, "fx window: $e") }
    }

    private fun showTapFx(name: String) { tapFx = name; tapFxT = 2.2f }

    private fun wantFx(): Pair<String, Boolean>? {
        if (st == St.ASLEEP || st == St.DOZE_IN) return Pair("zzz", false)
        if (st == St.DRAG || st == St.FALL || st == St.FLING) return null
        if (tapFxT > 0f) tapFx?.let { return Pair(it, false) }
        status.urgent?.let { if (fxT % 8f < 4.5f) return Pair("need_$it", true) }
        if (status.moodBand == "sad" && fxT % 7f < 3f) return Pair("sweat", false)
        if (st == St.EMOTE && clip?.name == "cheer_jump") return Pair("heart", false)
        return null
    }

    private fun tickFx(dt: Float) {
        val v = fx ?: return; val a = fxAtlas ?: return
        fxT += dt; if (tapFxT > 0f) tapFxT -= dt
        val w = if (view?.visibility == View.VISIBLE) wantFx() else null
        if (w == null) { if (v.visibility != View.GONE) v.visibility = View.GONE; return }
        val c = a.clip(w.first); val fr = c.frames[((fxT * c.fps).toInt()) % c.frames.size]
        v.show(fr, w.second)
        if (v.visibility != View.VISIBLE) v.visibility = View.VISIBLE
        placeFx()
    }

    private fun placeFx() {
        val v = fx ?: return; val p = fxLp ?: return; val l = lp ?: return; val f = v.frame ?: return
        if (v.visibility != View.VISIBLE) return
        val fs = v.scale; val cell = (fxAtlas?.size ?: 24) * fs
        val headY = l.y + headTop * scale
        val nx: Int; val ny: Int
        if (v.bubble) { nx = l.x + atlas.size * scale / 2 - cell / 2; ny = headY - cell + 2 * fs }   // 氣泡：頭頂正中，尾尖指住個頭
        else {
            val hx = if (facingLeft) l.x + (atlas.size - 1 - headRight) * scale else l.x + headRight * scale
            nx = hx - f.px * fs; ny = headY + 3 * scale - f.py * fs
        }
        val cx = nx.coerceIn(screen.left, max(screen.left, screen.right - cell)); val cy = ny.coerceIn(screen.top, max(screen.top, screen.bottom - cell))
        if (cx != p.x || cy != p.y) { p.x = cx; p.y = cy; try { wm.updateViewLayout(v, p) } catch (_: Exception) {} }
    }

    // ── 長按小選單（獨立 overlay 視窗，撳外面收） ──
    @SuppressLint("ClickableViewAccessibility")
    private fun showMenu() {
        hideMenu()
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val pad = dp(6f).toInt(); setPadding(pad, pad, pad, pad)
            background = GradientDrawable().apply { setColor(Color.argb(240, 255, 250, 240)); cornerRadius = dp(14f); setStroke(dp(1f).toInt(), Color.rgb(230, 200, 160)) }
            elevation = dp(6f)
        }
        fun item(label: String, on: () -> Unit) {
            box.addView(TextView(this).apply {
                text = label; textSize = 15f; setTextColor(Color.rgb(90, 60, 40))
                val pv = dp(9f).toInt(); val ph = dp(14f).toInt(); setPadding(ph, pv, ph, pv)
                minHeight = dp(44f).toInt(); gravity = Gravity.CENTER_VERTICAL
                setOnClickListener { hideMenu(); on() }
            })
        }
        fun mk(m: String, l: String) = (if (mode == m) "✓ " else "　 ") + l
        item(mk(PetPrefs.MODE_EDGE, "沿底邊行")) { applyMode(PetPrefs.MODE_EDGE) }
        item(mk(PetPrefs.MODE_FREE, "全畫面自由行")) { applyMode(PetPrefs.MODE_FREE) }
        item(mk(PetPrefs.MODE_PIN, "定點")) { applyMode(PetPrefs.MODE_PIN) }
        item("　 開返遊戲") { onDoubleTap() }
        item("　 收起團絨") { PetPrefs.setEnabled(this, false); stopSelf() }
        box.setOnTouchListener { _, e -> if (e.actionMasked == MotionEvent.ACTION_OUTSIDE) { hideMenu(); true } else false }
        val p = WindowManager.LayoutParams(WindowManager.LayoutParams.WRAP_CONTENT, WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH or WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
            PixelFormat.TRANSLUCENT)
        p.gravity = Gravity.TOP or Gravity.START
        box.measure(View.MeasureSpec.UNSPECIFIED, View.MeasureSpec.UNSPECIFIED)
        val mw = box.measuredWidth; val mh = box.measuredHeight
        val l = lp!!
        val cell = atlas.size * scale
        p.x = (l.x + cell / 2 - mw / 2).coerceIn(safe.left, max(safe.left, safe.right - mw))
        p.y = (if (l.y - mh - dp(4f) >= safe.top) l.y - mh - dp(4f).toInt() else l.y + cell).coerceIn(safe.top, max(safe.top, safe.bottom - mh))
        p.title = "FloatingPetMenu"
        wm.addView(box, p); menu = box
        Log.i(TAG, "long press → menu")
    }
    private fun hideMenu() { menu?.let { try { wm.removeView(it) } catch (_: Exception) {} }; menu = null }
}
