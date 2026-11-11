package hk.vizard.glimmer.fpet

import android.content.Context
import android.content.SharedPreferences
import org.json.JSONArray
import org.json.JSONObject

/** 設定＋同步 key。game（JS）係唯一模擬者：snapshot 由 JS 寫，queue 由 overlay 寫、JS drain。 */
object PetPrefs {
    const val FILE = "fpet"
    const val CAP = "CapacitorStorage"          // @capacitor/preferences 預設 group
    const val KEY_SNAPSHOT = "glimmer.snapshot" // {v,form,mood,ts}＋v2 sizeDp…＋v3 moodBand／sleeping／needs（JS 寫）
    const val KEY_QUEUE = "fpet.queue"          // [{t,k}]（overlay 寫，JS 經 FloatingPet.drainQueue 取走）
    const val MODE_EDGE = "edge"
    const val MODE_FREE = "free"
    const val MODE_PIN = "pin"
    val FORMS = PetForm.LEGACY
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

    /** 懸浮用邊套 atlas：snapshot evoForm → evo atlas（同遊戲一樣）；v1／唔認得 → 舊 form（PetForm.pick）。 */
    fun snapshotForm(c: Context): String = try {
        val s = cap(c).getString(KEY_SNAPSHOT, null)
        if (s == null) "soft" else { val o = JSONObject(s)
            PetForm.pick(if (o.has("evoForm")) o.optString("evoForm") else null, o.optString("form", "soft"), evoAvail(c)) }
    } catch (e: Exception) { "soft" }

    @Volatile private var evoAvailCache: Set<String>? = null
    /** APK assets/pet/evo 入面實際有嘅 evo atlas（pet_<evoForm>.json＋圖都要有）。 */
    fun evoAvail(c: Context): Set<String> = evoAvailCache ?: try {
        val names = c.assets.list("pet/evo")?.toSet() ?: emptySet()
        PetForm.EVO.filter { "pet_$it.json" in names && ("pet_$it.webp" in names || "pet_$it.png" in names) }.toSet()
    } catch (e: Exception) { emptySet<String>() }.also { evoAvailCache = it }

    // 玩圖示（Kurt 10-31 批）：主畫面 icon 格「行×列」（col×row，預設 4×6）；"off"＝唔玩。只係估格位中心，唔讀其他 app（冇敏感權限）。
    val GRIDS = listOf("4x6", "4x5", "5x5", "5x6", "off")
    fun grid(c: Context): String = prefs(c).getString("grid", "4x6").let { if (it in GRIDS) it!! else "4x6" }
    fun setGrid(c: Context, g: String) = prefs(c).edit().putString("grid", g).apply()

    /** snapshot v3（心情／瞌覺／需求）；v1／v2 → Snap(v<3) → PetStatus.project 會當 neutral。 */
    fun snapshotStatus(c: Context): PetStatus.Snap? = try {
        val s = cap(c).getString(KEY_SNAPSHOT, null)
        if (s == null) null else {
            val o = JSONObject(s); val n = o.optJSONObject("needs")
            fun mp(k: String): Map<String, Double>? = n?.optJSONObject(k)?.let { j -> PetStatus.KEYS.associateWith { j.optDouble(it, Double.NaN) }.takeIf { m -> m.values.all { it.isFinite() } } }
            PetStatus.Snap(o.optInt("v", 1), o.optLong("ts", System.currentTimeMillis()), o.optBoolean("egg", false),
                if (o.has("moodBand")) o.optString("moodBand") else null, o.optBoolean("sleeping", false),
                n?.optString("urgent")?.takeIf { it in PetStatus.KEYS }, n?.optDouble("warnAt", 30.0) ?: 30.0,
                mp("vals"), mp("rate"), mp("rateAwake"), n?.optDouble("floor", 20.0) ?: 20.0, n?.optDouble("wakeAt", 100.0) ?: 100.0)
        }
    } catch (e: Exception) { null }

    /** snapshot v4 info（長按選單狀態）；v1–v3 → null。 */
    fun snapshotInfo(c: Context): PetStatus.Info? = try {
        val s = cap(c).getString(KEY_SNAPSHOT, null)
        val o = s?.let { JSONObject(it) }; val i = o?.optJSONObject("info")
        if (o == null || o.optInt("v", 1) < 4 || i == null) null else {
            fun str(k: String) = if (i.isNull(k)) null else i.optString(k, "").ifEmpty { null }
            fun dbl(k: String) = i.optDouble(k, Double.NaN).takeIf { it.isFinite() }
            PetStatus.Info(str("name") ?: "團絨", i.optInt("gen", 1), str("stage"), str("stageName"), str("sub"), str("formName"), str("evoForm"),
                dbl("progress"), dbl("leftH"), dbl("ageSec")?.toLong(), if (i.has("days") && !i.isNull("days")) i.optInt("days") else null,
                i.optBoolean("unwell", false), i.optBoolean("fadeReady", false))
        }
    } catch (e: Exception) { null }

    /** snapshot stage（v2+）；v1 → null。 */
    fun snapshotStage(c: Context): String? = try { cap(c).getString(KEY_SNAPSHOT, null)?.let { JSONObject(it).optString("stage", "").ifEmpty { null } } } catch (e: Exception) { null }

    /** snapshot v5 sys12（親密／心聲／小驚喜）；v1–v4 → null（舊 www：懸浮唔出 systems12 嘢）。 */
    fun snapshotSys12(c: Context): PetSys12.Snap? = try {
        val s = cap(c).getString(KEY_SNAPSHOT, null)
        val o = s?.let { JSONObject(it) }
        if (o == null || o.optInt("v", 1) < 5) null else PetSys12.parse(o.optJSONObject("sys12"))
    } catch (e: Exception) { null }

    // 小驚喜：懸浮設定頁改嘅（本地，ts 後改贏；同時 queue {k:'set'} 俾 JS）
    fun surpLocal(c: Context): PetSys12.Settings? {
        val p = prefs(c); val ts = p.getLong("s12.ts", 0L); if (ts <= 0L) return null
        return PetSys12.Settings(PetSys12.SURP_KEYS.associateWith { p.getBoolean("s12.on.$it", it == "drop") }, p.getInt("s12.waterH", 2), p.getString("s12.sleepAt", "23:00") ?: "23:00", ts)
    }
    /** 改一項設定：先由有效設定起底（保留其他項），寫本地＋queue set。 */
    fun setSurp(c: Context, key: String, value: Any, now: Long = System.currentTimeMillis()) {
        val cur = PetSys12.settings(snapshotSys12(c)?.surp, surpLocal(c))
        val e = prefs(c).edit()
        cur?.let { s -> s.on.forEach { (k, v) -> e.putBoolean("s12.on.$k", v) }; e.putInt("s12.waterH", s.waterH); e.putString("s12.sleepAt", s.sleepAt) }
        when (key) { in PetSys12.SURP_KEYS -> e.putBoolean("s12.on.$key", value as Boolean); "waterH" -> e.putInt("s12.waterH", value as Int); "sleepAt" -> e.putString("s12.sleepAt", value as String) }
        e.putLong("s12.ts", now).apply()
        appendQueueObj(c, JSONObject().put("t", now).put("k", "set").put("key", key).put("val", value))
    }
    fun s12Long(c: Context, k: String) = prefs(c).getLong("s12.$k", 0L)
    fun setS12Long(c: Context, k: String, v: Long) = prefs(c).edit().putLong("s12.$k", v).apply()
    fun s12Str(c: Context, k: String): String? = prefs(c).getString("s12.$k", null)
    fun setS12Str(c: Context, k: String, v: String?) = prefs(c).edit().putString("s12.$k", v).apply()

    fun appendQueue(c: Context, kind: String) = appendQueueObj(c, JSONObject().put("t", System.currentTimeMillis()).put("k", kind))

    fun appendQueueObj(c: Context, item: JSONObject) = synchronized(lock) {
        val p = cap(c)
        val arr = try { JSONArray(p.getString(KEY_QUEUE, "[]")) } catch (e: Exception) { JSONArray() }
        arr.put(item)
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
