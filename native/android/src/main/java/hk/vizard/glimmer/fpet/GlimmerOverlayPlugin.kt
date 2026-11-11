package hk.vizard.glimmer.fpet

import android.app.Activity
import android.content.Intent
import android.provider.Settings
import android.view.View
import org.godotengine.godot.Dictionary
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.UsedByGodot

/** Godot 插件，取代舊 Capacitor FloatingPetPlugin（drainQueue／openSettings／status／start／stop）。 */
class GlimmerOverlayPlugin(godot: Godot) : GodotPlugin(godot) {
    override fun getPluginName(): String = "GlimmerOverlay"

    override fun onMainCreate(activity: Activity?): View? {
        activity?.application?.let { GlimmerApp.install(it) }
        return null
    }

    @UsedByGodot
    fun startOverlay() {
        val act = activity ?: return
        PetOverlayService.start(act)
    }

    @UsedByGodot
    fun stopOverlay() {
        val act = activity ?: return
        PetOverlayService.start(act, PetOverlayService.ACTION_STOP)
    }

    @UsedByGodot
    fun openSettings() {
        val act = activity ?: return
        act.startActivity(Intent(act, SettingsActivity::class.java))
    }

    @UsedByGodot
    fun drainQueue(): String {
        val act = activity ?: return "[]"
        return PetPrefs.drainQueue(act).toString()
    }

    @UsedByGodot
    fun status(): Dictionary {
        val d = Dictionary()
        val act = activity
        d["running"] = PetOverlayService.running
        if (act != null) {
            d["mode"] = PetPrefs.mode(act)
            d["overlay"] = Settings.canDrawOverlays(act)
            d["form"] = PetPrefs.snapshotForm(act)
        } else {
            d["mode"] = ""
            d["overlay"] = false
            d["form"] = ""
        }
        return d
    }

    @UsedByGodot
    fun writeSnapshot(json: String) {
        val act = activity ?: return
        PetPrefs.cap(act).edit().putString(PetPrefs.KEY_SNAPSHOT, json).commit()
    }
}
