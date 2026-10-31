package hk.vizard.glimmer.fpet

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

class PetFormTest {
    @Test fun evoFormPicksEvoAtlas() {
        for (f in PetForm.EVO) assertEquals(f, PetForm.pick(f, "soft"))
        assertEquals("evo_hop", PetForm.pick("evo_hop", "sprout"))
        assertEquals("evo_guard_dust", PetForm.pick("evo_guard_dust", "soft"))   // 微塵
        assertEquals("evo_still_lumi", PetForm.pick("evo_still_lumi", "soft"))   // 靜光・螢絨
    }

    @Test fun legacyFallback() {
        assertEquals("sprout", PetForm.pick(null, "sprout"))            // v1 snapshot：冇 evoForm
        assertEquals("radiant", PetForm.pick(null, "radiant"))
        assertEquals("soft", PetForm.pick("evo_unknown", "soft"))        // 唔認得
        assertEquals("sprout", PetForm.pick("evo_unknown", "sprout"))
        assertEquals("soft", PetForm.pick(null, "egg"))                  // 舊行為：egg → soft
        assertEquals("soft", PetForm.pick(null, null))
        assertEquals("sprout", PetForm.pick("evo_sprout", "sprout", emptySet()))   // APK 冇 evo atlas
    }

    @Test fun defaultDpMatchesGame() {
        assertEquals(52f, PetForm.defaultDp("evo_sprout", 32), 0.01f)   // 32 × 1.625
        assertEquals(78f, PetForm.defaultDp("evo_still_soft", 48), 0.01f)
        assertEquals(52f, PetForm.defaultDp("sprout", 32), 0.01f)
        assertEquals(72f, PetForm.defaultDp("soft", 64), 0.01f)
    }

    /** 每個 evoForm 都有 atlas；idle 一定有；frame 喺圖入面；同遊戲 frameSize 一致。 */
    @Test fun evoAtlasAssetsComplete() {
        val dir = listOf(File("src/main/assets/pet/evo"), File("app/src/main/assets/pet/evo")).first { it.isDirectory }
        val size = mapOf("evo_egg" to 24, "evo_dot" to 28, "evo_sprout" to 32, "evo_hop" to 38)
        val need = listOf("idle", "walk", "turn_back", "picked_up", "emo_happy", "sleep_loop", "fall_asleep", "wake", "sniff", "swat", "cheer_jump", "droop", "emo_hungry")
        for (f in PetForm.EVO) {
            val o = JSONObject(File(dir, "pet_$f.json").readText())
            assertTrue(File(dir, o.getString("image")).isFile)
            val fs = o.getInt("frameSize")
            assertEquals(size[f] ?: if (f.startsWith("evo_guard")) 44 else 48, fs)
            val cl = o.getJSONObject("clips"); assertTrue("$f idle", cl.has("idle"))
            val fb = o.getJSONArray("fallbackIdle"); val fbs = (0 until fb.length()).map { fb.getString(it) }
            for (n in need) assertTrue("$f $n", cl.has(n) || n in fbs)
            if (f != "evo_egg") assertTrue("$f 全 clip", fbs.isEmpty())
        }
    }
}
