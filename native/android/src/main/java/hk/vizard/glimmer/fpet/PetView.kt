package hk.vizard.glimmer.fpet

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Paint
import android.graphics.Rect
import android.view.MotionEvent
import android.view.View

/** 原生 Canvas 畫一格 atlas（Nearest，整數倍）。視窗＝一格大細，其餘位置觸控穿透。 */
@SuppressLint("ViewConstructor")
class PetView(ctx: Context, private val onTouch: (MotionEvent) -> Boolean) : View(ctx) {
    var atlas: PetAtlas? = null
    var frame: PetFrame? = null
    var flip = false
    var scale = 3
    private val paint = Paint().apply { isFilterBitmap = false; isAntiAlias = false; isDither = false }
    private val dst = Rect()

    fun show(f: PetFrame, flipX: Boolean) {
        if (f !== frame || flipX != flip) { frame = f; flip = flipX; invalidate() }
    }

    override fun onDraw(canvas: Canvas) {
        val a = atlas ?: return; val f = frame ?: return
        val s = a.size * scale
        dst.set(0, 0, s, s)
        canvas.save()
        if (flip) canvas.scale(-1f, 1f, s / 2f, 0f)   // 成個合成以中線（pivot x＝S/2）翻轉
        canvas.drawBitmap(a.bitmap, f.src, dst, paint)
        canvas.restore()
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(e: MotionEvent) = onTouch(e)
}
