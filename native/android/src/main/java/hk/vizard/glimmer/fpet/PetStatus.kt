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

    // ── snapshot v4：長按選單顯示遊戲狀態（Kurt 10-31 22:50）──
    /** overlayStatus().info（只讀）；v1–v3 冇 → null。 */
    data class Info(
        val name: String, val gen: Int, val stage: String?, val stageName: String?, val sub: String?, val formName: String?,
        val evoForm: String?, val progress: Double?, val leftH: Double?, val ageSec: Long?, val days: Int?, val unwell: Boolean, val fadeReady: Boolean,
    )

    val STAGE_NAME = mapOf("egg" to "光卵", "newborn" to "絨點", "sprout" to "芽崽", "juvenile" to "跳跳期", "adult" to "守夜者", "elder" to "靜光")   // = data.js STAGE_NAME
    val NEED_LABEL = mapOf("hunger" to "飽腹", "mood" to "心情", "clean" to "清潔", "energy" to "精力")                                         // = data.js NEED_LABEL
    val MOOD_LABEL = mapOf("happy" to "開心", "ok" to "平靜", "sad" to "唔開心")

    /** 遊戲 HUD 需求條顏色（index.html .fill：>60 warm #ffd36a／30–60 warm2 #f59a4a／<30 warn #ff6a6a）。 */
    fun barColor(v: Double): Int = if (v > 60) 0xFFFFD36A.toInt() else if (v >= 30) 0xFFF59A4A.toInt() else 0xFFFF6A6A.toInt()

    data class NeedRow(val key: String, val label: String, val value: Int, val color: Int)
    data class Menu(val title: String, val sub: String?, val moodLine: String, val needs: List<NeedRow>, val progress: Double?, val progressText: String?)

    fun ageText(ageSec: Long?, days: Int?): String? {
        val d = days ?: ageSec?.let { (it / 86400).toInt() } ?: return null
        return if (d >= 1) "$d 日大" else ageSec?.let { val h = (it / 3600).toInt(); if (h >= 1) "$h 小時大" else "啱啱出世" } ?: "未夠 1 日"
    }

    /** 長按選單狀態區（純資料，JUnit）。info＝v4；冇就用 snapshot stage（v2+）／vals（v3）盡量顯示。 */
    fun menu(info: Info?, snapStage: String?, snap: Snap?, st: Status): Menu {
        val stage = info?.stage ?: snapStage
        val egg = snap?.egg == true || stage == "egg"
        val stageName = info?.stageName ?: stage?.let { STAGE_NAME[it] }
        val title = (info?.name ?: "團絨") + (stageName?.let { "・$it" } ?: "")
        val subParts = ArrayList<String>()
        if (info?.sub != null && info.sub.isNotEmpty() && info.sub != stageName) subParts.add(info.sub)
        if (info?.gen != null && info.gen > 1) subParts.add("第 ${info.gen} 代")
        ageText(info?.ageSec, info?.days)?.let { subParts.add(it) }
        val sub = subParts.joinToString(" · ").ifEmpty { null }
        val moodLine = when {
            egg -> "光卵：未孵化"
            snap == null || snap.v < 3 -> "（開返遊戲同步狀態）"
            else -> "心情：" + (MOOD_LABEL[st.moodBand] ?: "平靜") + "　" + (if (st.sleeping) "瞓緊 zZ" else "醒緊") + (if (info?.unwell == true) "　不適" else "")
        }
        val vals = if (egg) null else st.vals ?: snap?.vals
        val needs = vals?.let { v -> KEYS.mapNotNull { k -> v[k]?.let { NeedRow(k, NEED_LABEL.getValue(k), it.roundToIntSafe(), barColor(it)) } } } ?: emptyList()
        val pg = info?.progress?.coerceIn(0.0, 1.0)
        val pt = when {
            pg == null -> null
            info.fadeReady -> "準備化光"
            else -> "階段 ${(pg * 100).toInt()}%" + (info.leftH?.let { h -> if (h <= 0.0) "" else if (h >= 48) "・仲有 ${(h / 24).toInt()} 日" else if (h >= 1) "・仲有 ${h.toInt()} 小時" else "・就快" } ?: "")
        }
        return Menu(title, sub, moodLine, needs, pg, pt)
    }

    private fun Double.roundToIntSafe(): Int = if (isFinite()) Math.round(this).toInt().coerceIn(0, 100) else 0
}
