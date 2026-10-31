package hk.vizard.glimmer.fpet

/**
 * 懸浮窗揀邊套 atlas（Kurt 10-31 22:50：懸浮團絨要同遊戲一樣）。
 * snapshot（v2+）有 evoForm（evo_egg／evo_dot／evo_sprout／evo_hop／evo_guard_*／evo_still_*）→ 直接用同名 evo atlas
 *（tools/bake_evo_atlas.py 由遊戲 art/evo6 烤出，assets/pet/evo/pet_<evoForm>.webp/json）。
 * 舊 atlas（sprout／soft／radiant）只做 fallback：v1 snapshot（冇 evoForm）／唔認得嘅 evoForm／APK 冇嗰套 evo atlas。
 * 純 Kotlin → JUnit。
 */
object PetForm {
    val LEGACY = setOf("sprout", "radiant", "soft")
    val EVO = setOf(
        "evo_egg", "evo_dot", "evo_sprout", "evo_hop",
        "evo_guard_lumi", "evo_guard_radiant", "evo_guard_soft", "evo_guard_dust",
        "evo_still_lumi", "evo_still_radiant", "evo_still_soft", "evo_still_dust",
        // §7 新支線 ×5（水珠／菇傘／晶角／月眠／火苗）：守夜者＋靜光
        "evo_guard_tide", "evo_guard_shroom", "evo_guard_crystal", "evo_guard_moon", "evo_guard_ember",
        "evo_still_tide", "evo_still_shroom", "evo_still_crystal", "evo_still_moon", "evo_still_ember",
    )
    /** data.js FORMS frameSize（snapshot 冇 sizeDp 時用 frameSize × overlayDpPerPx 1.625）。 */
    const val DP_PER_PX = 1.625f

    fun isEvo(form: String) = form in EVO

    /** @param evoForm snapshot.evoForm（v1 冇 → null）；@param legacy snapshot.form；@param avail APK 入面有嘅 evo atlas。 */
    fun pick(evoForm: String?, legacy: String?, avail: Set<String> = EVO): String {
        if (evoForm != null && evoForm in EVO && evoForm in avail) return evoForm
        return if (legacy != null && legacy in LEGACY) legacy else "soft"
    }

    /** 冇 sizeDp 嘅預設顯示大細（dp）：evo＝frameSize×1.625；舊 sprout 52／其他 72（照舊）。 */
    fun defaultDp(form: String, frameSize: Int): Float =
        if (isEvo(form)) frameSize * DP_PER_PX else if (form == "sprout") 52f else 72f
}
