package hk.vizard.glimmer.fpet

import android.Manifest
import android.content.Context
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import com.getcapacitor.JSObject
import com.getcapacitor.PermissionState
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin
import com.getcapacitor.annotation.Permission
import com.getcapacitor.annotation.PermissionCallback
import java.util.concurrent.atomic.AtomicBoolean

/**
 * 6b「真世界連動」JS 橋（src/long6bui.js 用）。全部權限可以唔畀：唔畀 → JS 照舊玩（遊戲天氣／原本晝夜／冇步數碎）。
 * ・steps：ACTIVITY_RECOGNITION（Android 10／API 29+ 先係 runtime 權限；26–28 唔使問）→ TYPE_STEP_COUNTER 讀一次（開機至今總步數＋開機時間），唔開背景 service。
 * ・location：ACCESS_COARSE_LOCATION（大概位置）→ 上次已知／單次 NETWORK 位置，四捨五入到 0.1°（約 11 km）先交俾 JS；原生唔存。
 * 步數同位置都唔會離開部機（位置只用嚟砌 Open-Meteo 天氣 URL）。
 */
@CapacitorPlugin(
    name = "RealWorld",
    permissions = [
        Permission(alias = "steps", strings = [Manifest.permission.ACTIVITY_RECOGNITION]),
        Permission(alias = "location", strings = [Manifest.permission.ACCESS_COARSE_LOCATION]),
    ]
)
class RealWorldPlugin : Plugin() {
    private val main = Handler(Looper.getMainLooper())
    private fun sm() = context.getSystemService(Context.SENSOR_SERVICE) as SensorManager?
    private fun counter(): Sensor? = sm()?.getDefaultSensor(Sensor.TYPE_STEP_COUNTER)
    private fun stepsState(): String = if (Build.VERSION.SDK_INT < 29) "granted" else getPermissionState("steps").toString()
    private fun locState(): String = getPermissionState("location").toString()
    private fun r1(x: Double) = Math.round(x * 10.0) / 10.0

    @PluginMethod
    fun status(call: PluginCall) {
        call.resolve(JSObject().put("steps", stepsState()).put("location", locState()).put("sensor", counter() != null).put("sdk", Build.VERSION.SDK_INT))
    }

    @PluginMethod
    fun requestSteps(call: PluginCall) {
        if (stepsState() == "granted") { call.resolve(JSObject().put("steps", "granted")); return }
        requestPermissionForAlias("steps", call, "stepsCb")
    }
    @PermissionCallback
    private fun stepsCb(call: PluginCall) { call.resolve(JSObject().put("steps", stepsState())) }

    @PluginMethod
    fun requestLocation(call: PluginCall) {
        if (getPermissionState("location") == PermissionState.GRANTED) { call.resolve(JSObject().put("location", "granted")); return }
        requestPermissionForAlias("location", call, "locCb")
    }
    @PermissionCallback
    private fun locCb(call: PluginCall) { call.resolve(JSObject().put("location", locState())) }

    /** 讀一次計步器：{ steps（開機至今）, bootMs（開機時刻，JS 用嚟認重開機） }；4 秒冇讀數 → reject("timeout")。 */
    @PluginMethod
    fun steps(call: PluginCall) {
        if (stepsState() != "granted") { call.reject("permission"); return }
        val m = sm(); val s = counter()
        if (m == null || s == null) { call.reject("nosensor"); return }
        val done = AtomicBoolean(false)
        val l = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) {
                if (!done.compareAndSet(false, true)) return
                m.unregisterListener(this)
                val boot = System.currentTimeMillis() - SystemClock.elapsedRealtime()
                call.resolve(JSObject().put("steps", e.values[0].toLong()).put("bootMs", boot))
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        m.registerListener(l, s, SensorManager.SENSOR_DELAY_NORMAL)
        main.postDelayed({ if (done.compareAndSet(false, true)) { m.unregisterListener(l); call.reject("timeout") } }, 4000)
    }

    /** 大概位置（0.1°）：上次已知 NETWORK／PASSIVE；冇 → 單次 NETWORK（10 秒）。 */
    @PluginMethod
    fun location(call: PluginCall) {
        if (getPermissionState("location") != PermissionState.GRANTED) { call.reject("permission"); return }
        val lm = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager?
        if (lm == null) { call.reject("noloc"); return }
        val give = { loc: Location -> call.resolve(JSObject().put("lat", r1(loc.latitude)).put("lon", r1(loc.longitude))) }
        var best: Location? = null
        for (p in listOf(LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER)) {
            try { val l = lm.getLastKnownLocation(p); if (l != null && (best == null || l.time > best!!.time)) best = l } catch (e: Exception) { }
        }
        if (best != null && System.currentTimeMillis() - best!!.time < 6 * 3600_000L) { give(best!!); return }
        val enabled = try { lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER) } catch (e: Exception) { false }
        if (!enabled) { if (best != null) give(best!!) else call.reject("noloc"); return }
        val done = AtomicBoolean(false)
        val fallback = best
        val ll = object : LocationListener {
            override fun onLocationChanged(loc: Location) { if (done.compareAndSet(false, true)) { lm.removeUpdates(this); give(loc) } }
            @Deprecated("API < 29") override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
            override fun onProviderEnabled(provider: String) {}
            override fun onProviderDisabled(provider: String) {}
        }
        try {
            @Suppress("DEPRECATION") lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER, ll, Looper.getMainLooper())
        } catch (e: Exception) { if (done.compareAndSet(false, true)) { if (fallback != null) give(fallback) else call.reject("noloc") }; return }
        main.postDelayed({ if (done.compareAndSet(false, true)) { lm.removeUpdates(ll); if (fallback != null) give(fallback) else call.reject("timeout") } }, 10000)
    }
}
