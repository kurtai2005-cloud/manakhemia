package hk.vizard.glimmer.fpet

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.Rect
import android.graphics.RectF
import android.view.View

/** 頭頂狀態圖示（Zzz／心心／汗／需求氣泡）。獨立 overlay 視窗、唔收觸控；圖示全部嚟自 pet_fx atlas（遊戲現有素材）。 */
@SuppressLint("ViewConstructor")
class FxView(ctx: Context, val atlas: PetAtlas) : View(ctx) {
    var scale = 3
    var frame: PetFrame? = null
    var bubble = false
    private val paint = Paint().apply { isFilterBitmap = false; isAntiAlias = false; isDither = false }
    private val fill = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.argb(240, 255, 250, 240); style = Paint.Style.FILL }
    private val stroke = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(200, 150, 110); style = Paint.Style.STROKE }
    private val dst = Rect(); private val rf = RectF(); private val tail = Path()

    fun show(f: PetFrame?, withBubble: Boolean) { if (f !== frame || withBubble != bubble) { frame = f; bubble = withBubble; invalidate() } }

    override fun onDraw(canvas: Canvas) {
        val f = frame ?: return
        val s = atlas.size * scale
        if (bubble) {
            // 簡單氣泡：圓角方＋向下細尾（尾尖喺視窗底中）
            val pad = scale * 2f; stroke.strokeWidth = scale.toFloat()
            rf.set(pad, pad, s - pad, s - scale * 6f)
            canvas.drawRoundRect(rf, scale * 5f, scale * 5f, fill); canvas.drawRoundRect(rf, scale * 5f, scale * 5f, stroke)
            tail.reset(); tail.moveTo(s / 2f - scale * 3, rf.bottom - scale); tail.lineTo(s / 2f, s - scale * 1.5f); tail.lineTo(s / 2f + scale * 3, rf.bottom - scale); tail.close()
            canvas.drawPath(tail, fill)
            canvas.drawLine(s / 2f - scale * 3, rf.bottom, s / 2f, s - scale * 1.5f, stroke); canvas.drawLine(s / 2f + scale * 3, rf.bottom, s / 2f, s - scale * 1.5f, stroke)
            // icon（10×10，喺 24 格底部）放氣泡正中
            val icon = 10 * scale; val cx = (s - icon) / 2; val cy = ((rf.top + rf.bottom) / 2 - icon / 2f).toInt()
            val src = Rect(f.src.left + 7, f.src.bottom - 11, f.src.left + 17, f.src.bottom - 1)
            dst.set(cx, cy, cx + icon, cy + icon); canvas.drawBitmap(atlas.bitmap, src, dst, paint)
        } else {
            dst.set(0, 0, s, s); canvas.drawBitmap(atlas.bitmap, f.src, dst, paint)
        }
    }
}
