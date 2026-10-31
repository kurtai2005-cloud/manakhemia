package hk.vizard.glimmer.fpet

import kotlin.math.max
import kotlin.math.min

/**
 * 懸浮窗同步遊戲狀況（Kurt 10-31 批）：snapshot v3 = 心情／瞌覺／需求。
 * app 喺背景時 JS 唔行，所以用 snapshot 入面嘅 rate（每小時）由 ts 推算到而家（同 sim.step 一樣：瞓到 wakeAt 自動醒、離線保底 floor）。
 * v1／v2（冇 moodBand）→ 一律 neutral、冇提示（照舊行為）。純 Kotlin，唔掂 Android → 可 JUnit。
 */
object PetStatus {
    val KEYS = listOf("hunger", "mood", "clean", "energy")

    class Snap(
        val v: Int, val ts: Long, val egg: Boolean, val moodBand: String?, val sleeping: Boolean,
        val urgent: String?, val warnAt: Double,
        val vals: Map<String, Double>?, val rate: Map<String, Double>?, val rateAwake: Map<String, Double>?,
        val floor: Double, val wakeAt: Double,
    )

    data class Status(val moodBand: String, val sleeping: Boolean, val urgent: String?, val vals: Map<String, Double>?) {
        companion object { val NONE = Status("ok", false, null, null) }
    }

    fun band(mood: Double) = if (mood > 60) "happy" else if (mood < 30) "sad" else "ok"

    fun project(s: Snap?, nowMs: Long): Status {
        if (s == null || s.v < 3 || s.egg) return Status.NONE
        val v0 = s.vals; val r = s.rate
        if (v0 == null || r == null || KEYS.any { v0[it] == null || r[it] == null }) return Status(s.moodBand ?: "ok", s.sleeping, s.urgent, null)
        val hrs = max(0.0, (nowMs - s.ts) / 3_600_000.0)
        var sleeping = s.sleeping
        val cur = HashMap<String, Double>(); for (k in KEYS) cur[k] = v0.getValue(k)
        fun adv(rt: Map<String, Double>, h: Double) { for (k in KEYS) cur[k] = cur.getValue(k) + (rt[k] ?: 0.0) * h }
        if (sleeping && r.getValue("energy") > 0) {
            val tWake = max(0.0, (s.wakeAt - v0.getValue("energy")) / r.getValue("energy"))
            if (hrs < tWake) adv(r, hrs)
            else { adv(r, tWake); cur["energy"] = 100.0; sleeping = false; adv(s.rateAwake ?: r, hrs - tWake) }
        } else adv(r, hrs)
        for (k in KEYS) {
            val keep = min(v0.getValue(k), s.floor)   // 離線保底：原本高過 floor 就唔會跌穿 floor
            cur[k] = min(100.0, max(0.0, max(cur.getValue(k), keep)))
        }
        val lk = KEYS.minByOrNull { cur.getValue(it) }!!
        return Status(band(cur.getValue("mood")), sleeping, if (cur.getValue(lk) < s.warnAt) lk else null, cur)
    }
}
