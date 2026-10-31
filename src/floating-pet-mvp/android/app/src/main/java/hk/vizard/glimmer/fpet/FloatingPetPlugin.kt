package hk.vizard.glimmer.fpet

import android.content.Intent
import android.provider.Settings
import com.getcapacitor.JSArray
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

/** JS 橋：drainQueue（原子取走 overlay 互動 queue）、openSettings、status。 */
@CapacitorPlugin(name = "FloatingPet")
class FloatingPetPlugin : Plugin() {
    @PluginMethod
    fun drainQueue(call: PluginCall) {
        val arr = PetPrefs.drainQueue(context)
        call.resolve(JSObject().put("items", JSArray(arr.toString())))
    }
    @PluginMethod
    fun openSettings(call: PluginCall) {
        activity.startActivity(Intent(context, SettingsActivity::class.java)); call.resolve()
    }
    @PluginMethod
    fun status(call: PluginCall) {
        call.resolve(JSObject().put("running", PetOverlayService.running).put("mode", PetPrefs.mode(context))
            .put("overlay", Settings.canDrawOverlays(context)).put("form", PetPrefs.snapshotForm(context)))
    }
}
