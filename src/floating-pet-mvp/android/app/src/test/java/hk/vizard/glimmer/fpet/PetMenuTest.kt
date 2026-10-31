package hk.vizard.glimmer.fpet

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** 長按選單狀態區（snapshot v4＋v1–v3 fallback）。 */
class PetMenuTest {
    private val vals = mapOf("hunger" to 72.4, "mood" to 45.0, "clean" to 20.0, "energy" to 90.0)
    private fun snap(v: Int, egg: Boolean = false) = PetStatus.Snap(v, 0L, egg, if (v >= 3) "ok" else null, false, "clean", 30.0, if (v >= 3) vals else null, null, null, 20.0, 100.0)
    private val info = PetStatus.Info("團絨", 1, "adult", "守夜者", "微塵形態", "微塵", "evo_guard_dust", 0.5, 84.0, 5L * 86400 + 100, 5, false, false)

    @Test fun v4Full() {
        val st = PetStatus.Status("happy", true, "clean", vals)
        val m = PetStatus.menu(info, "adult", snap(4), st)
        assertEquals("團絨・守夜者", m.title)
        assertEquals("微塵形態 · 5 日大", m.sub)
        assertEquals("心情：開心　瞓緊 zZ", m.moodLine)
        assertEquals(listOf("hunger", "mood", "clean", "energy"), m.needs.map { it.key })
        assertEquals(listOf("飽腹", "心情", "清潔", "精力"), m.needs.map { it.label })
        assertEquals(listOf(72, 45, 20, 90), m.needs.map { it.value })
        assertEquals(listOf(0xFFFFD36A.toInt(), 0xFFF59A4A.toInt(), 0xFFFF6A6A.toInt(), 0xFFFFD36A.toInt()), m.needs.map { it.color })   // HUD 三色
        assertEquals(0.5, m.progress!!, 1e-9)
        assertEquals("階段 50%・仲有 3 日", m.progressText)
    }

    @Test fun v4FadeReadyAndUnwellAndYoung() {
        val i = info.copy(stage = "elder", stageName = "靜光", sub = "螢絨形態 · 準備化光", fadeReady = true, unwell = true, progress = 1.0, leftH = 0.0)
        val m = PetStatus.menu(i, "elder", snap(4), PetStatus.Status("sad", false, null, vals))
        assertEquals("團絨・靜光", m.title); assertEquals("準備化光", m.progressText)
        assertEquals("心情：唔開心　醒緊　不適", m.moodLine)
        val y = PetStatus.menu(info.copy(stage = "newborn", stageName = "絨點", sub = "絨點仔", ageSec = 3 * 3600L, days = 0, progress = 0.1, leftH = 5.4), "newborn", snap(4), PetStatus.Status.NONE)
        assertEquals("絨點仔 · 3 小時大", y.sub); assertEquals("階段 10%・仲有 5 小時", y.progressText)
        assertEquals(listOf(72, 45, 20, 90), y.needs.map { it.value })   // project 冇 vals → 用 snapshot vals
    }

    @Test fun egg() {
        val m = PetStatus.menu(info.copy(stage = "egg", stageName = "光卵", sub = "光卵", days = 0, ageSec = 60), "egg", snap(4, egg = true), PetStatus.Status.NONE)
        assertEquals("團絨・光卵", m.title); assertEquals("光卵：未孵化", m.moodLine); assertTrue(m.needs.isEmpty())
        assertEquals("啱啱出世", m.sub)
    }

    @Test fun fallbackV3V2V1() {
        val m3 = PetStatus.menu(null, "juvenile", snap(3), PetStatus.Status("ok", false, "clean", vals))
        assertEquals("團絨・跳跳期", m3.title); assertNull(m3.sub); assertEquals("心情：平靜　醒緊", m3.moodLine)
        assertEquals(4, m3.needs.size); assertNull(m3.progress); assertNull(m3.progressText)
        val m2 = PetStatus.menu(null, "sprout", snap(2), PetStatus.Status.NONE)
        assertEquals("團絨・芽崽", m2.title); assertEquals("（開返遊戲同步狀態）", m2.moodLine); assertTrue(m2.needs.isEmpty())
        val m1 = PetStatus.menu(null, null, null, PetStatus.Status.NONE)
        assertEquals("團絨", m1.title); assertTrue(m1.needs.isEmpty()); assertNull(m1.progress)
    }
}
