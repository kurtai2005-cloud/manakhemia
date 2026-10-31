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

    private enum class St { IDLE, WALK, TURN, HAPPY, DRAG, FALL, DOZE_IN, ASLEEP, WAKE }

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
        appVisible = GlimmerApp.visible
        v.visibility = if (appVisible) View.GONE else View.VISIBLE
        lastInteract = SystemClock.elapsedRealtime()
        startTicking()
        Log.i(TAG, "attached form=${atlas.form} mode=$mode scale=$scale safe=$safe")
    }

    private fun loadAtlas(form: String) {
        atlas = PetAtlas.load(this, form)
        val target = dp(try { org.json.JSONObject(PetPrefs.cap(this).getString(PetPrefs.KEY_SNAPSHOT, null) ?: "{}").optDouble("sizeDp", Double.NaN).toFloat().takeIf { it.isFinite() && it > 0f } } catch (e: Exception) { null } ?: if (form == "sprout") 52f else 72f)   // 顯示大細（dp）：evo6 snapshot v2 sizeDp 跟階段；舊 snapshot 冇 sizeDp → 舊尺寸
        scale = max(1, (target / atlas.size).roundToInt())
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
    }

    // ── ticking（≤15fps；瞌 2fps；熄屏／app 前台停） ──
    private val tickR = object : Runnable {
        override fun run() {
            if (!ticking) return
            val now = SystemClock.uptimeMillis()
            val dt = ((now - lastTick).coerceIn(0, 250)) / 1000f
            lastTick = now
            tick(dt)
            h.postDelayed(this, if (st == St.ASLEEP) 500L else 67L)
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
        if (vis) { hideMenu(); v.visibility = View.GONE; stopTicking() }
        else {
            // 返嚟可能已轉形態／改模式
            val f = PetPrefs.snapshotForm(this)
            if (needSwap(f)) swapForm(f)
            val m = PetPrefs.mode(this); if (m != mode) applyMode(m)
            v.visibility = View.VISIBLE; startTicking()
        }
    }

    private val snapRx = SharedPreferences.OnSharedPreferenceChangeListener { _, key ->
        if (key == PetPrefs.KEY_SNAPSHOT) h.post { val f = PetPrefs.snapshotForm(this); if (view != null && needSwap(f)) swapForm(f) }
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
        when (st) {
            St.IDLE -> {
                stTimer -= dt
                if (SystemClock.elapsedRealtime() - lastInteract > dozeMs) { doze(); return }
                if (stTimer <= 0 && mode != PetPrefs.MODE_PIN) startWalk()
                else if (stTimer <= 0) stTimer = 3f
            }
            St.WALK -> {
                if (SystemClock.elapsedRealtime() - lastInteract > dozeMs) { doze(); return }
                val speed = 20f * scale     // 12px／6 幀 @10fps ≈ 20 art px/s
                val dx = tgtX - feetX; val dy = tgtY - feetY; val d = hypot(dx, dy)
                if (d <= speed * dt || d < 1f) {
                    feetX = tgtX; feetY = tgtY; toIdle(Random.nextDouble(2.0, 5.0).toFloat())
                } else {
                    feetX += dx / d * speed * dt; feetY += dy / d * speed * dt
                    if (abs(dx) > 2f) facingLeft = dx < 0
                }
            }
            St.TURN -> if (clipDone()) { st = St.HAPPY; play("emo_happy"); stTimer = 1.0f }
            St.HAPPY -> { stTimer -= dt; if (stTimer <= 0) toIdle(1.5f) }
            St.DRAG -> if (clip?.name == "picked_up_enter" && clipDone()) play("picked_up")
            St.FALL -> {
                vy += dp(2200f) * dt
                feetY += vy * dt
                if (feetY >= groundY) {
                    feetY = groundY
                    if (bounces == 0 && vy > dp(250f)) { vy = -vy * 0.35f; bounces++ }
                    else landed()
                }
            }
            St.DOZE_IN -> if (clipDone()) { st = St.ASLEEP; play("sleep_loop"); Log.i(TAG, "asleep (2fps)") }
            St.ASLEEP -> {}
            St.WAKE -> if (clipDone()) toIdle(1.5f)
        }
        place()
    }

    private fun toIdle(t: Float) { st = St.IDLE; play("idle"); stTimer = t }

    private fun startWalk() {
        when (mode) {
            PetPrefs.MODE_EDGE -> {
                feetY = groundEdge()
                val span = maxFeetX() - minFeetX()
                var x = minFeetX() + Random.nextFloat() * span
                if (abs(x - feetX) < dp(40f)) x = if (feetX > (minFeetX() + maxFeetX()) / 2) feetX - dp(80f) else feetX + dp(80f)
                tgtX = x.coerceIn(minFeetX(), maxFeetX()); tgtY = feetY
            }
            PetPrefs.MODE_FREE -> {
                tgtX = minFeetX() + Random.nextFloat() * (maxFeetX() - minFeetX())
                tgtY = minFeetY() + Random.nextFloat() * (maxFeetY() - minFeetY())
                // 每段唔好行太遠
                val dx = tgtX - feetX; val dy = tgtY - feetY; val d = hypot(dx, dy); val lim = dp(220f)
                if (d > lim) { tgtX = feetX + dx / d * lim; tgtY = feetY + dy / d * lim }
            }
            else -> return
        }
        st = St.WALK; play("walk")
    }

    private fun doze() { hideMenu(); st = St.DOZE_IN; play("fall_asleep"); Log.i(TAG, "dozing (no interaction ${PetPrefs.dozeMinutes(this)} min)") }

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
                downX = e.rawX; downY = e.rawY; dragging = false; longFired = false
                hideMenu()
                h.postDelayed(longR, ViewConfiguration.getLongPressTimeout().toLong())
            }
            MotionEvent.ACTION_MOVE -> {
                if (!dragging && !longFired && hypot(e.rawX - downX, e.rawY - downY) > slop) {
                    h.removeCallbacks(longR); startDrag(e.rawX, e.rawY)
                }
                if (dragging) { fingerX = e.rawX; fingerY = e.rawY; clampFinger(); place() }
            }
            MotionEvent.ACTION_UP -> {
                h.removeCallbacks(longR)
                when {
                    dragging -> endDrag()
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

    private fun endDrag() {
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
        st = St.FALL; play("idle"); vy = 0f; bounces = 0
        PetPrefs.appendQueue(this, "drag")
        Log.i(TAG, "drag end → fall to $groundY")
    }

    private fun onSingleTap() {
        interact()
        when (st) {
            St.ASLEEP, St.DOZE_IN -> { st = St.WAKE; play("wake"); PetPrefs.appendQueue(this, "wake"); Log.i(TAG, "wake") }
            St.DRAG, St.FALL -> {}
            else -> { st = St.TURN; play("turn_back"); PetPrefs.appendQueue(this, "tap"); Log.i(TAG, "tap → turn_back") }
        }
        place()
    }

    private fun onDoubleTap() {
        interact()
        Log.i(TAG, "double tap → open game")
        startActivity(Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT))
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
