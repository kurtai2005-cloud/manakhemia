package hk.vizard.glimmer.fpet

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

/** 設定＋同步 key。game（JS）係唯一模擬者：snapshot 由 JS 寫，queue 由 overlay 寫、JS drain。 */
object PetPrefs {
    const val FILE = "fpet"
    const val CAP = "CapacitorStorage"          // @capacitor/preferences 預設 group
    const val KEY_SNAPSHOT = "glimmer.snapshot" // {v,form,mood,ts}（JS 寫）
    const val KEY_QUEUE = "fpet.queue"          // [{t,k}]（overlay 寫，JS 經 FloatingPet.drainQueue 取走）
    const val MODE_EDGE = "edge"
    const val MODE_FREE = "free"
    const val MODE_PIN = "pin"
    val FORMS = setOf("sprout", "radiant", "soft")
    private const val QUEUE_CAP = 50
    private val lock = Any()

    fun prefs(c: Context): SharedPreferences = c.getSharedPreferences(FILE, Context.MODE_PRIVATE)
    fun cap(c: Context): SharedPreferences = c.getSharedPreferences(CAP, Context.MODE_PRIVATE)

    fun mode(c: Context): String = prefs(c).getString("mode", MODE_EDGE) ?: MODE_EDGE
    fun setMode(c: Context, m: String) = prefs(c).edit().putString("mode", m).apply()
    fun enabled(c: Context) = prefs(c).getBoolean("enabled", false)
    fun setEnabled(c: Context, on: Boolean) = prefs(c).edit().putBoolean("enabled", on).apply()
    fun pin(c: Context): Pair<Float, Float>? {
        val p = prefs(c); val x = p.getFloat("pinX", -1f); val y = p.getFloat("pinY", -1f)
        return if (x < 0 || y < 0) null else Pair(x, y)
    }
    fun setPin(c: Context, x: Float, y: Float) = prefs(c).edit().putFloat("pinX", x).putFloat("pinY", y).apply()
    fun dozeMinutes(c: Context) = prefs(c).getInt("dozeMin", 60)

    fun snapshotForm(c: Context): String = try {
        val s = cap(c).getString(KEY_SNAPSHOT, null)
        val f = if (s == null) "soft" else JSONObject(s).optString("form", "soft")
        if (f in FORMS) f else "soft"
    } catch (e: Exception) { "soft" }

    fun appendQueue(c: Context, kind: String) = synchronized(lock) {
        val p = cap(c)
        val arr = try { JSONArray(p.getString(KEY_QUEUE, "[]")) } catch (e: Exception) { JSONArray() }
        arr.put(JSONObject().put("t", System.currentTimeMillis()).put("k", kind))
        val out = JSONArray()
        val from = maxOf(0, arr.length() - QUEUE_CAP)
        for (i in from until arr.length()) out.put(arr.get(i))
        p.edit().putString(KEY_QUEUE, out.toString()).commit()
    }

    fun drainQueue(c: Context): JSONArray = synchronized(lock) {
        val p = cap(c)
        val arr = try { JSONArray(p.getString(KEY_QUEUE, "[]")) } catch (e: Exception) { JSONArray() }
        p.edit().remove(KEY_QUEUE).commit()
        arr
    }
}
