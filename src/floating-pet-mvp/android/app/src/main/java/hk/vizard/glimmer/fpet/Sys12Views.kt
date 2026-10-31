package hk.vizard.glimmer.fpet

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.text.Layout
import android.text.StaticLayout
import android.text.TextPaint
import android.view.View

/** systems12 懸浮素材（遊美 b1：assets/pet/sys12 下嘅 png；心聲泡 9-slice＋尾、星星碎、提醒 icon）。冇圖都唔會壞（fallback 圓角框）。 */
class Sys12Art(c: Context) {
    private fun load(c: Context, n: String): Bitmap? = try { c.assets.open("pet/sys12/$n.png").use { BitmapFactory.decodeStream(it) } } catch (e: Exception) { null }
    val bubble = load(c, "bubble_thought_9s"); val tail = load(c, "bubble_thought_tail")
    val shard16 = load(c, "icon_star_shard_16"); val shard32 = load(c, "icon_star_shard_32")
    val water = load(c, "icon_remind_water"); val sleep = load(c, "icon_remind_sleep")
    fun icon(what: String): Bitmap? = when (what) { "water" -> water; "sleep" -> sleep; "drop" -> shard16; else -> null }
}

private val pixel = Paint().apply { isFilterBitmap = false; isAntiAlias = false; isDither = false }

/** 9-slice（inset＝art px，k＝放大倍數；nearest）。 */
fun drawNine(c: Canvas, b: Bitmap, inset: Int, k: Int, l: Int, t: Int, r: Int, btm: Int) {
    val w = b.width; val h = b.height; val i = inset; val d = inset * k
    val sx = intArrayOf(0, i, w - i, w); val sy = intArrayOf(0, i, h - i, h)
    val dx = intArrayOf(l, l + d, r - d, r); val dy = intArrayOf(t, t + d, btm - d, btm)
    val s = Rect(); val o = Rect()
    for (yy in 0..2) for (xx in 0..2) { s.set(sx[xx], sy[yy], sx[xx + 1], sy[yy + 1]); o.set(dx[xx], dy[yy], dx[xx + 1], dy[yy + 1]); if (o.width() > 0 && o.height() > 0) c.drawBitmap(b, s, o, pixel) }
}

/** 頭頂講嘢泡（心聲／提醒／執到星星碎）：bubble_thought_9s＋尾＋（icon）＋字。唔收觸控。 */
@SuppressLint("ViewConstructor")
class SayView(ctx: Context, private val art: Sys12Art, private val k: Int, private val maxW: Int) : View(ctx) {
    private val tp = TextPaint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(80, 55, 40); textSize = 13f * ctx.resources.displayMetrics.scaledDensity }
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(240, 255, 250, 240) }
    private var lay: StaticLayout? = null; private var icon: Bitmap? = null
    var text: String = ""; private set
    private val pad get() = 7 * k
    private val iconPx get() = 16 * k
    private val tailH get() = (art.tail?.height ?: 7) * k / 2

    fun set(t: String, ic: Bitmap?) {
        text = t; icon = ic
        val tw = maxW - pad * 2 - (if (ic != null) iconPx + 3 * k else 0)
        @Suppress("DEPRECATION")
        lay = StaticLayout(t, tp, maxOf(40, tw), Layout.Alignment.ALIGN_NORMAL, 1.1f, 0f, false)
        requestLayout(); invalidate()
    }
    fun want(): Pair<Int, Int> {
        val L = lay ?: return Pair(0, 0)
        var lw = 0f; for (i in 0 until L.lineCount) lw = maxOf(lw, L.getLineWidth(i))
        val iw = if (icon != null) iconPx + 3 * k else 0
        val w = (lw.toInt() + iw + pad * 2).coerceAtLeast(22 * k)
        val h = maxOf(L.height, if (icon != null) iconPx else 0) + pad * 2 + tailH
        return Pair(w, h)
    }
    override fun onMeasure(a: Int, b: Int) { val (w, h) = want(); setMeasuredDimension(w, h) }
    override fun onDraw(c: Canvas) {
        val L = lay ?: return; val bh = height - tailH
        val b = art.bubble
        if (b != null) drawNine(c, b, 11, k, 0, 0, width, bh) else c.drawRoundRect(0f, 0f, width.toFloat(), bh.toFloat(), 8f * k, 8f * k, fill)
        art.tail?.let { t -> val tw = t.width * k / 2; val th = t.height * k / 2; val x = width / 2 - tw / 2; c.drawBitmap(t, Rect(0, 0, t.width, t.height), Rect(x, bh - k, x + tw, bh - k + th), pixel) }
        var x = pad
        icon?.let { ic -> val y = (bh - iconPx) / 2; c.drawBitmap(ic, Rect(0, 0, ic.width, ic.height), Rect(x, y, x + iconPx, y + iconPx), pixel); x += iconPx + 3 * k }
        c.save(); c.translate(x.toFloat(), ((bh - L.height) / 2).toFloat()); L.draw(c); c.restore()
    }
}

/** 星星碎（撳得：執起 → queue drop）。輕輕上下浮。 */
@SuppressLint("ViewConstructor")
class ShardView(ctx: Context, private val bmp: Bitmap?, private val px: Int) : View(ctx) {
    var bob = 0f; set(v) { field = v; invalidate() }
    private val glow = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(70, 255, 236, 150) }
    override fun onMeasure(a: Int, b: Int) = setMeasuredDimension(px, px)
    override fun onDraw(c: Canvas) {
        val off = (bob * px / 10f).toInt()
        c.drawCircle(px / 2f, px / 2f + off, px * 0.42f, glow)
        if (bmp != null) c.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height), Rect(px / 8, px / 8 + off, px - px / 8, px - px / 8 + off), pixel)
        else c.drawCircle(px / 2f, px / 2f + off, px * 0.25f, Paint().apply { color = Color.rgb(255, 220, 90) })
    }
}
