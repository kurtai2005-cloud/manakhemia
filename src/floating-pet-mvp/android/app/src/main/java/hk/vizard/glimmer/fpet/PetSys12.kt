package hk.vizard.glimmer.fpet

import org.json.JSONArray
import org.json.JSONObject
import java.util.Calendar

/**
 * systems12 第 1 批（懸浮側）純邏輯：snapshot.sys12 解析、心聲（系統 6）、小驚喜（系統 12：星星碎／飲水／早瞓）計時。
 * 照抄 glimmer src/systems.js 嘅 voiceTry／dropNext／waterDue／sleepDue（數值全部由 snapshot 嚟，唔 hardcode）。
 * JS 係唯一記帳者：懸浮只係 queue {k:'drop'|'voice'|'set'|'remind'}，返 app 由 sys12Apply 入帳（每日上限喺 JS 再計一次）。
 */
object PetSys12 {
    val SURP_KEYS = listOf("drop", "water", "sleep")

    data class Voice(val chance: Double, val cooldownSec: Int, val showSec: Int, val newestTierPct: Int, val lastAt: Long, val lines: List<List<String>>)
    data class Surp(val on: Map<String, Boolean>, val waterH: Int, val sleepAt: String, val ts: Long,
                    val dropMinH: Double, val dropMaxH: Double, val perDay: Int, val dropShowSec: Int, val day: String, val room: Int,
                    val waterFromH: Int, val waterToH: Int, val sleepWinMin: Int, val showSec: Int, val lines: Map<String, List<String>>)
    data class Snap(val egg: Boolean, val bond: Int, val tier: Int, val voice: Voice, val surp: Surp, val shards: Int)

    /** 有效設定（snapshot vs 懸浮本地改動：後改贏）。 */
    data class Settings(val on: Map<String, Boolean>, val waterH: Int, val sleepAt: String, val ts: Long)

    private fun strs(a: JSONArray?): List<String> = if (a == null) emptyList() else (0 until a.length()).mapNotNull { a.opt(it) as? String }

    fun parse(o: JSONObject?): Snap? = try {
        if (o == null) null else {
            val v = o.getJSONObject("voice"); val s = o.getJSONObject("surp"); val b = o.optJSONObject("bond")
            val la = v.optJSONArray("lines"); val lines = if (la == null) emptyList() else (0 until la.length()).map { strs(la.optJSONArray(it)) }
            val on = s.optJSONObject("on"); val d = s.getJSONObject("drop"); val w = s.optJSONObject("water"); val ln = s.optJSONObject("lines")
            Snap(o.optBoolean("egg", false), b?.optInt("v", 0) ?: 0, b?.optInt("tier", 0) ?: 0,
                Voice(v.optDouble("chance", 0.0), v.optInt("cooldownSec", 600), v.optInt("showSec", 4), v.optInt("newestTierPct", 50), v.optLong("lastAt", 0L), lines),
                Surp(SURP_KEYS.associateWith { on?.optBoolean(it, false) ?: false }, s.optInt("waterH", 2), s.optString("sleepAt", "23:00"), s.optLong("ts", 0L),
                    d.optDouble("minH", 2.0), d.optDouble("maxH", 4.0), d.optInt("perDay", 0), d.optInt("showSec", 30), d.optString("day", ""), d.optInt("room", 0),
                    w?.optInt("fromH", 9) ?: 9, w?.optInt("toH", 22) ?: 22, s.optInt("sleepWinMin", 60), s.optInt("showSec", 6),
                    SURP_KEYS.associateWith { strs(ln?.optJSONArray(it)) }),
                o.optInt("shards", 0))
        }
    } catch (e: Exception) { null }

    fun settings(s: Surp?, local: Settings?): Settings? {
        val snap = s?.let { Settings(it.on, it.waterH, it.sleepAt, it.ts) }
        return when { snap == null -> local; local == null -> snap; local.ts > snap.ts -> local; else -> snap }
    }

    /** 心聲：cooldown 由 max(snapshot lastAt, 懸浮本地 last) 計；r1 擲 chance，r2 揀段（newestTierPct% 最新段），r3 揀句。 */
    fun voiceTry(s: Snap?, nowMs: Long, localLast: Long, r1: Double, r2: Double, r3: Double, r4: Double = r3): String? {
        if (s == null || s.egg) return null
        val v = s.voice; val L = v.lines.filter { it.isNotEmpty() }; if (L.isEmpty()) return null
        if (nowMs - maxOf(v.lastAt, localLast) < v.cooldownSec * 1000L) return null
        if (r1 >= v.chance) return null
        val tier = if (r2 * 100 < v.newestTierPct) L.size - 1 else (r4 * L.size).toInt().coerceIn(0, L.size - 1)
        val arr = L[tier]; return arr[(r3 * arr.size).toInt().coerceIn(0, arr.size - 1)]
    }

    fun dropNext(lastMs: Long, r: Double, minH: Double, maxH: Double): Long = lastMs + ((minH + r * (maxH - minH)) * 3600e3).toLong()

    private fun cal(ms: Long) = Calendar.getInstance().apply { timeInMillis = ms }
    fun dayKey(ms: Long): String { val c = cal(ms); return "%04d-%02d-%02d".format(c.get(Calendar.YEAR), c.get(Calendar.MONTH) + 1, c.get(Calendar.DAY_OF_MONTH)) }

    /** 今日仲可以掉幾多粒：本地每日 perDay；snapshot 係今日 → 再受 JS room（otherCap／30 上限）限，減去 snapshot 之後已執嘅。 */
    fun dropRoom(s: Surp, nowMs: Long, collected: List<Long>): Int {
        val today = dayKey(nowMs); val mine = collected.count { dayKey(it) == today }
        val local = s.perDay - mine
        val js = if (s.day == today) s.room - collected.count { it > s.ts && dayKey(it) == today } else s.perDay
        return maxOf(0, minOf(local, js))
    }

    fun waterDue(lastMs: Long, waterH: Int, nowMs: Long, fromH: Int, toH: Int): Boolean {
        val h = cal(nowMs).get(Calendar.HOUR_OF_DAY); return h >= fromH && h < toH && nowMs - lastMs >= waterH * 3600e3
    }

    fun parseHM(t: String): Int { val m = Regex("^(\\d\\d):(\\d\\d)$").find(t) ?: return 0; return m.groupValues[1].toInt() * 60 + m.groupValues[2].toInt() }

    /** 早瞓：sleepAt 起 winMin 分鐘內、今晚未出過 → 出；00:00 屬前一晚。回傳 (due, nightKey)。 */
    fun sleepDue(sleepAt: String, lastNight: String?, nowMs: Long, winMin: Int): Pair<Boolean, String?> {
        val c = cal(nowMs); val m = c.get(Calendar.HOUR_OF_DAY) * 60 + c.get(Calendar.MINUTE); val at = parseHM(sleepAt)
        val t = (m - at + 1440) % 1440
        if (t >= winMin) return Pair(false, null)
        val night = dayKey(nowMs - if (at < 720 && m < 720) 86_400_000L else 0L)
        return Pair(night != lastNight, night)
    }

    fun line(s: Surp?, what: String, r: Double): String? = s?.lines?.get(what)?.takeIf { it.isNotEmpty() }?.let { it[(r * it.size).toInt().coerceIn(0, it.size - 1)] }
}
