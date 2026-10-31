package hk.vizard.glimmer.fpet

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Rect
import org.json.JSONObject

class PetFrame(val src: Rect, val px: Int, val py: Int)
class PetClip(val name: String, val fps: Float, val loop: Boolean, val grabPivot: Boolean, val frames: List<PetFrame>) {
    val duration get() = frames.size / fps
}

/** 預烤 atlas（tools/bake_overlay_atlas.py：noface＋faceov＋bulb_base）。全部朝右畫。 */
class PetAtlas(val form: String, val size: Int, val bitmap: Bitmap, val clips: Map<String, PetClip>) {
    fun clip(name: String): PetClip = clips[name] ?: clips.getValue("idle")
    companion object {
        fun load(ctx: Context, form: String): PetAtlas {
            val json = ctx.assets.open("pet/pet_$form.json").bufferedReader().use { it.readText() }
            val o = JSONObject(json)
            val size = o.getInt("frameSize")
            val opts = BitmapFactory.Options().apply { inScaled = false; inPreferredConfig = Bitmap.Config.ARGB_8888 }
            val bmp = ctx.assets.open("pet/pet_$form.png").use { BitmapFactory.decodeStream(it, null, opts)!! }
            val cl = o.getJSONObject("clips"); val map = HashMap<String, PetClip>()
            for (k in cl.keys()) {
                val c = cl.getJSONObject(k); val fa = c.getJSONArray("frames"); val fr = ArrayList<PetFrame>()
                for (i in 0 until fa.length()) {
                    val f = fa.getJSONObject(i); val x = f.getInt("x"); val y = f.getInt("y")
                    fr.add(PetFrame(Rect(x, y, x + size, y + size), f.getInt("px"), f.getInt("py")))
                }
                map[k] = PetClip(k, c.getDouble("fps").toFloat(), c.getBoolean("loop"), c.optString("pivot") == "grab", fr)
            }
            return PetAtlas(form, size, bmp, map)
        }
    }
}
