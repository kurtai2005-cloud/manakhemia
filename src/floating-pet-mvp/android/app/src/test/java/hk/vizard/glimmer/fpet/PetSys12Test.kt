package hk.vizard.glimmer.fpet

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.util.Calendar
import java.util.TimeZone

/** systems12 懸浮純邏輯（對照 glimmer systems.js voiceTry／dropNext／waterDue／sleepDue）。 */
class PetSys12Test {
    private val H = 3_600_000L
    @Before fun tz() { TimeZone.setDefault(TimeZone.getTimeZone("Asia/Hong_Kong")) }
    private fun at(y: Int, mo: Int, d: Int, h: Int, mi: Int = 0) = Calendar.getInstance().apply { clear(); set(y, mo - 1, d, h, mi) }.timeInMillis
    private val json = """{"v":1,"egg":false,"bond":{"v":46,"tier":2},
      "voice":{"chance":0.3,"cooldownSec":600,"showSec":4,"newestTierPct":50,"lastAt":0,"lines":[["a1","a2"],["b1"]]},
      "surp":{"on":{"drop":true,"water":false,"sleep":true},"waterH":2,"sleepAt":"23:00","ts":1000,
        "drop":{"minH":2,"maxH":4,"perDay":5,"showSec":30,"day":"2026-11-01","room":3},"water":{"fromH":9,"toH":22},"sleepWinMin":60,"showSec":6,
        "lines":{"drop":["d"],"water":["w1","w2"],"sleep":["s"]}},"shards":7}"""
    private fun snap() = PetSys12.parse(JSONObject(json))!!

    @Test fun parsesSnapshot() {
        val s = snap()
        assertEquals(2, s.tier); assertEquals(2, s.voice.lines.size); assertEquals(600, s.voice.cooldownSec)
        assertEquals(mapOf("drop" to true, "water" to false, "sleep" to true), s.surp.on)
        assertEquals(3, s.surp.room); assertEquals(listOf("w1", "w2"), s.surp.lines["water"]); assertEquals(7, s.shards)
        assertNull(PetSys12.parse(null)); assertNull(PetSys12.parse(JSONObject("{\"v\":1}")))
    }
    @Test fun voiceChanceCooldownAndTier() {
        val s = snap(); val now = 10_000_000L
        assertNull("擲唔中（r1 ≥ chance）", PetSys12.voiceTry(s, now, 0, 0.5, 0.0, 0.0))
        assertEquals("newestTierPct → 最新段", "b1", PetSys12.voiceTry(s, now, 0, 0.1, 0.2, 0.0))
        assertEquals("其他 → 隨機段", "a2", PetSys12.voiceTry(s, now, 0, 0.1, 0.9, 0.9, 0.0))
        assertNull("本地冷卻 10 分鐘", PetSys12.voiceTry(s, now, now - 599_000, 0.1, 0.2, 0.0))
        assertNotNull(PetSys12.voiceTry(s, now, now - 600_000, 0.1, 0.2, 0.0))
        assertNull("snapshot lastAt（主程式講過）都計冷卻", PetSys12.voiceTry(s.copy(voice = s.voice.copy(lastAt = now - 60_000)), now, 0, 0.1, 0.2, 0.0))
        assertNull("蛋唔講", PetSys12.voiceTry(s.copy(egg = true), now, 0, 0.0, 0.0, 0.0))
    }
    @Test fun dropTimingAndRoom() {
        assertEquals(2 * H, PetSys12.dropNext(0, 0.0, 2.0, 4.0)); assertEquals(3 * H, PetSys12.dropNext(0, 0.5, 2.0, 4.0))
        val s = snap().surp; val now = at(2026, 11, 1, 15)
        assertEquals("snapshot 今日 room 3", 3, PetSys12.dropRoom(s, now, emptyList()))
        assertEquals("snapshot 之後執咗 2 粒 → 1", 1, PetSys12.dropRoom(s, now, listOf(now - 1000, now - 2000)))
        val tmr = at(2026, 11, 2, 10)
        assertEquals("snapshot 舊日 → perDay 5", 5, PetSys12.dropRoom(s, tmr, listOf(now)))
        assertEquals("本地每日 5 粒上限", 0, PetSys12.dropRoom(s, tmr, List(5) { tmr - it * 1000L }))
    }
    @Test fun waterWindow() {
        val d = at(2026, 11, 1, 12)
        assertTrue(PetSys12.waterDue(d - 2 * H, 2, d, 9, 22)); assertFalse(PetSys12.waterDue(d - H, 2, d, 9, 22))
        assertFalse("22:00 後唔出", PetSys12.waterDue(0, 1, at(2026, 11, 1, 22, 10), 9, 22)); assertFalse("9:00 前唔出", PetSys12.waterDue(0, 1, at(2026, 11, 1, 8, 59), 9, 22))
    }
    @Test fun sleepOncePerNight() {
        val r = PetSys12.sleepDue("23:00", null, at(2026, 11, 1, 23, 20), 60)
        assertTrue(r.first); assertEquals("2026-11-01", r.second)
        assertFalse("同一晚唔再出", PetSys12.sleepDue("23:00", "2026-11-01", at(2026, 11, 1, 23, 40), 60).first)
        assertFalse("過咗 60 分鐘唔補", PetSys12.sleepDue("23:00", null, at(2026, 11, 2, 0, 5), 60).first)
        assertFalse("未到", PetSys12.sleepDue("23:00", null, at(2026, 11, 1, 22, 59), 60).first)
        val z = PetSys12.sleepDue("00:00", null, at(2026, 11, 2, 0, 30), 60)
        assertTrue(z.first); assertEquals("00:00 屬前一晚", "2026-11-01", z.second)
    }
    @Test fun settingsLastWriteWins() {
        val s = snap().surp
        val loc = PetSys12.Settings(mapOf("drop" to false, "water" to true, "sleep" to false), 1, "22:00", 2000)
        assertEquals(loc, PetSys12.settings(s, loc))
        assertEquals(1000L, PetSys12.settings(s, loc.copy(ts = 500))!!.ts)
        assertEquals(loc, PetSys12.settings(null, loc)); assertEquals(true, PetSys12.settings(s, null)!!.on["drop"])
        assertEquals("w2", PetSys12.line(s, "water", 0.9)); assertNull(PetSys12.line(s, "nope", 0.0))
    }
}
