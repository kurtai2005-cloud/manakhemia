package hk.vizard.glimmer.fpet

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PetStatusTest {
    private val H = 3_600_000L
    private fun m(h: Double, mo: Double, c: Double, e: Double) = mapOf("hunger" to h, "mood" to mo, "clean" to c, "energy" to e)
    private fun snap(vals: Map<String, Double>?, sleeping: Boolean = false, v: Int = 3, egg: Boolean = false,
                     rate: Map<String, Double>? = m(-6.0, -4.0, -3.9, -5.0), awake: Map<String, Double>? = m(-6.0, -4.0, -3.9, -5.0)) =
        PetStatus.Snap(v, 0L, egg, vals?.let { PetStatus.band(it.getValue("mood")) }, sleeping, null, 30.0, vals, rate, awake, 20.0, 100.0)

    @Test fun oldSnapshotsNeutral() {
        assertEquals(PetStatus.Status.NONE, PetStatus.project(null, 0))
        assertEquals(PetStatus.Status.NONE, PetStatus.project(snap(m(10.0, 10.0, 10.0, 10.0), v = 2), 0))
        assertEquals(PetStatus.Status.NONE, PetStatus.project(snap(m(10.0, 10.0, 10.0, 10.0), egg = true), 0))
    }
    @Test fun v3WithoutRatesUsesSnapFields() {
        val s = PetStatus.Snap(3, 0, false, "sad", true, "hunger", 30.0, null, null, null, 20.0, 100.0)
        assertEquals(PetStatus.Status("sad", true, "hunger", null), PetStatus.project(s, 5 * H))
    }
    @Test fun happyNow() {
        val st = PetStatus.project(snap(m(80.0, 80.0, 80.0, 80.0)), 0)
        assertEquals("happy", st.moodBand); assertNull(st.urgent); assertFalse(st.sleeping)
    }
    @Test fun becomesHungryOverTime() {
        // hunger 50 −6/h → 3.5h 後 29 → 提示 hunger（其他仲高）
        val s = snap(m(50.0, 90.0, 90.0, 95.0))
        assertNull(PetStatus.project(s, 3 * H).urgent)
        assertEquals("hunger", PetStatus.project(s, (3.6 * H).toLong()).urgent)
    }
    @Test fun moodTurnsSadAndFloorHolds() {
        val s = snap(m(100.0, 40.0, 100.0, 100.0))
        assertEquals("ok", PetStatus.project(s, 2 * H).moodBand)
        val late = PetStatus.project(s, 48 * H)
        assertEquals("sad", late.moodBand)
        assertEquals(20.0, late.vals!!.getValue("mood"), 1e-9)   // 離線保底 20
        assertEquals(20.0, late.vals!!.getValue("hunger"), 1e-9)
    }
    @Test fun belowFloorStaysNotLower() {
        val late = PetStatus.project(snap(m(10.0, 80.0, 80.0, 80.0)), 10 * H)
        assertEquals(10.0, late.vals!!.getValue("hunger"), 1e-9); assertEquals("hunger", late.urgent)
    }
    @Test fun sleepThenAutoWake() {
        val s = snap(m(80.0, 80.0, 80.0, 40.0), sleeping = true, rate = m(-1.8, -1.2, -1.17, 14.4))
        assertTrue(PetStatus.project(s, 4 * H).sleeping)                 // 40 + 14.4×4 = 97.6 < 100
        val w = PetStatus.project(s, 5 * H)                               // 4.17h 醒
        assertFalse(w.sleeping)
        assertTrue(w.vals!!.getValue("energy") < 100.0 && w.vals!!.getValue("energy") > 95.0)
    }
}
