package hk.vizard.glimmer.fpet

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import java.io.File
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

    // ── v10.2（遊測 40fe202 P2-1）：落雨撐葉／霧冬打冷震 ──
    private fun wx(manual: String? = null, season: String = "autumn") = JSONObject(json).put("wx", JSONObject("""{"days":{"2026-11-01":"rain","2026-11-02":"fog","2026-11-03":"clear"},
      "manual":${if (manual == null) "null" else "\"$manual\""},"season":"$season","shiver":{"everySec":[25,50],"base":0.25,"fogMul":2,"winterMul":2}}"""))
    @Test fun weatherFromSnapshot() {
        val w = PetSys12.parse(wx())!!.wx!!
        assertEquals("rain", PetSys12.weatherAt(w, at(2026, 11, 1, 0, 5))); assertEquals("rain", PetSys12.weatherAt(w, at(2026, 11, 1, 23, 55)))   // 成日
        assertEquals("fog", PetSys12.weatherAt(w, at(2026, 11, 2, 9))); assertEquals("clear", PetSys12.weatherAt(w, at(2026, 11, 9, 9)))         // 過咗 7 日 → 晴
        assertEquals("fog", PetSys12.weatherAt(PetSys12.parse(wx("fog"))!!.wx, at(2026, 11, 1, 9)))                                              // DEV manual 贏
        assertNull(snap().wx); assertEquals("clear", PetSys12.weatherAt(null, at(2026, 11, 1, 9)))                                              // 舊 snapshot 冇 wx → 晴
    }
    @Test fun rainPlaysLeafUmbrella() {
        val has = setOf("idle", "leaf_umbrella", "leaf_umbrella_in", "shiver")
        assertEquals("leaf_umbrella", PetSys12.idleClip("rain") { it in has }); assertEquals("idle", PetSys12.idleClip("fog") { it in has })
        assertEquals("idle", PetSys12.idleClip("rain") { it == "idle" })   // 光卵／舊 atlas 冇 clip → idle
    }
    @Test fun shiverFogOrWinter() {
        val a = PetSys12.parse(wx())!!.wx; val win = PetSys12.parse(wx(season = "winter"))!!.wx
        assertEquals(0.5, PetSys12.shiverChance(a, "fog"), 1e-9); assertEquals(0.0, PetSys12.shiverChance(a, "clear"), 1e-9)
        assertEquals(0.5, PetSys12.shiverChance(win, "clear"), 1e-9); assertEquals(1.0, PetSys12.shiverChance(win, "fog"), 1e-9)
        assertEquals(25.0, PetSys12.shiverNextSec(a, 0.0), 1e-9); assertEquals(50.0, PetSys12.shiverNextSec(a, 1.0), 1e-9)
    }
    @Test fun bakedAtlasHasRainClips() {
        val dir = listOf(File("src/main/assets/pet/evo"), File("app/src/main/assets/pet/evo")).first { it.isDirectory }
        val js = dir.listFiles { f -> f.name.endsWith(".json") && f.name != "pet_evo_egg.json" }!!; assertEquals(21, js.size)
        for (f in js) {
            val c = JSONObject(f.readText()).getJSONObject("clips")
            assertTrue(f.name, c.getJSONObject("leaf_umbrella").getBoolean("loop") && c.getJSONObject("leaf_umbrella").getJSONArray("frames").length() == 4)
            assertTrue(f.name, !c.getJSONObject("leaf_umbrella_in").getBoolean("loop") && c.getJSONObject("leaf_umbrella_in").getJSONArray("frames").length() == 2)
            assertTrue(f.name, !c.getJSONObject("shiver").getBoolean("loop") && c.getJSONObject("shiver").getJSONArray("frames").length() == 12)
        }
    }

    // v10.3：懸浮摸頭 → 摸頭委託（snapshot.sys12.pat）
    @Test fun patSnapshotAndGate() {
        assertNull("舊 www 冇 pat", snap().pat)
        assertFalse("舊 www → 唔 queue pat（避免舊 bridge 當互動重複加 mood）", PetSys12.patOk(snap(), 0))
        val o = JSONObject(json); o.put("pat", JSONObject().put("day", "2026-11-01").put("left", 2).put("cap", 12))
        val sn = PetSys12.parse(o)!!
        assertEquals(PetSys12.Pat("2026-11-01", 2, 12), sn.pat)
        assertTrue(PetSys12.patOk(sn, 0)); assertTrue(PetSys12.patOk(sn, 11))
        assertFalse("每日 cap（config overlayPatPerDay）", PetSys12.patOk(sn, 12))
        assertTrue("left 0 照 queue（snapshot 可能舊；JS skip 多出嘅）", PetSys12.patOk(sn.copy(pat = sn.pat!!.copy(left = 0)), 3))
        o.put("egg", true); assertFalse("蛋唔計", PetSys12.patOk(PetSys12.parse(o), 0))
        assertFalse(PetSys12.patOk(null, 0))
    }

    @Test fun overlayTapStillQueuesTapAndPat() {
        val src = listOf(File("src/main/java/hk/vizard/glimmer/fpet/PetOverlayService.kt"), File("app/src/main/java/hk/vizard/glimmer/fpet/PetOverlayService.kt")).first { it.isFile }.readText()
        val tap = src.lines().first { it.contains("\"tap → turn_back\"") }
        assertTrue("舊 tap（mood）保留", tap.contains("appendQueue(this, \"tap\")"))
        assertTrue("v10.3 加 queuePat()", tap.contains("queuePat()"))
        assertTrue(src.contains(".put(\"k\", \"pat\")"))
    }
}
