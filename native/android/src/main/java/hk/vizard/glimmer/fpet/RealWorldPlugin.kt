package hk.vizard.glimmer.fpet

import android.Manifest
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
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
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import org.godotengine.godot.Dictionary
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.SignalInfo
import org.godotengine.godot.plugin.UsedByGodot
import java.util.concurrent.atomic.AtomicBoolean

/**
 * 6b「真世界連動」Godot 橋（由 Capacitor RealWorldPlugin 移植）。
 * 全部權限可以唔畀：唔畀就照玩（遊戲天氣／原本晝夜／冇步數碎）。
 * steps：ACTIVITY_RECOGNITION → TYPE_STEP_COUNTER 讀一次，唔開背景 service。
 * location：ACCESS_COARSE_LOCATION → 四捨五入到 0.1°；原生唔存。
 */
class RealWorldPlugin(godot: Godot) : GodotPlugin(godot) {
    override fun getPluginName(): String = "RealWorld"

    override fun getPluginSignals(): MutableSet<SignalInfo> = mutableSetOf(
        SignalInfo("steps_result", Dictionary::class.java),
        SignalInfo("location_result", Dictionary::class.java),
    )

    private val main = Handler(Looper.getMainLooper())
    @Volatile var lastStepsResult: Dictionary = Dictionary().apply { put("ok", false); put("error", "none") }
    @Volatile var lastLocationResult: Dictionary = Dictionary().apply { put("ok", false); put("error", "none") }
    private fun ctx(): Context? = activity
    private fun sm() = ctx()?.getSystemService(Context.SENSOR_SERVICE) as SensorManager?
    private fun counter(): Sensor? = sm()?.getDefaultSensor(Sensor.TYPE_STEP_COUNTER)
    private fun r1(x: Double) = Math.round(x * 10.0) / 10.0

    private fun granted(perm: String): Boolean {
        val a = activity ?: return false
        return ContextCompat.checkSelfPermission(a, perm) == PackageManager.PERMISSION_GRANTED
    }

    private fun stepsState(): String {
        if (Build.VERSION.SDK_INT < 29) return "granted"
        return if (granted(Manifest.permission.ACTIVITY_RECOGNITION)) "granted" else "denied"
    }

    private fun locState(): String =
        if (granted(Manifest.permission.ACCESS_COARSE_LOCATION)) "granted" else "denied"

    @UsedByGodot
    fun status(): Dictionary {
        val d = Dictionary()
        d["steps"] = stepsState()
        d["location"] = locState()
        d["sensor"] = counter() != null
        d["sdk"] = Build.VERSION.SDK_INT
        return d
    }

    @UsedByGodot
    fun requestSteps(): String {
        val a = activity ?: return stepsState()
        if (stepsState() == "granted") return "granted"
        if (Build.VERSION.SDK_INT >= 29) {
            ActivityCompat.requestPermissions(a, arrayOf(Manifest.permission.ACTIVITY_RECOGNITION), 1601)
        }
        return stepsState()
    }

    @UsedByGodot
    fun requestLocation(): String {
        val a = activity ?: return locState()
        if (locState() == "granted") return "granted"
        ActivityCompat.requestPermissions(a, arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION), 1602)
        return locState()
    }


    @UsedByGodot
    fun lastSteps(): Dictionary = lastStepsResult

    @UsedByGodot
    fun lastLocation(): Dictionary = lastLocationResult

    /** 非堵塞：開始讀計步器，完成後發 steps_result。 */
    @UsedByGodot
    fun steps(): Dictionary {
        val out = Dictionary()
        if (stepsState() != "granted") { out["ok"] = false; out["error"] = "permission"; lastStepsResult = out; return out }
        val m = sm(); val s = counter()
        if (m == null || s == null) { out["ok"] = false; out["error"] = "nosensor"; lastStepsResult = out; return out }
        val done = AtomicBoolean(false)
        val l = object : SensorEventListener {
            override fun onSensorChanged(e: SensorEvent) {
                if (!done.compareAndSet(false, true)) return
                m.unregisterListener(this)
                val boot = System.currentTimeMillis() - SystemClock.elapsedRealtime()
                val acc = Dictionary()
                acc["ok"] = true
                acc["steps"] = e.values[0].toLong()
                acc["bootMs"] = boot
                lastStepsResult = acc
                emitSignal("steps_result", acc)
            }
            override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}
        }
        m.registerListener(l, s, SensorManager.SENSOR_DELAY_NORMAL)
        main.postDelayed({
            if (done.compareAndSet(false, true)) {
                m.unregisterListener(l)
                val acc = Dictionary()
                acc["ok"] = false
                acc["error"] = "timeout"
                lastStepsResult = acc
                emitSignal("steps_result", acc)
            }
        }, 4000)
        out["ok"] = true
        out["pending"] = true
        return out
    }

    /** 非堵塞：讀大概位置，完成後發 location_result。 */
    @UsedByGodot
    fun location(): Dictionary {
        val out = Dictionary()
        val a = activity
        if (a == null) { out["ok"] = false; out["error"] = "noloc"; lastLocationResult = out; return out }
        if (locState() != "granted") { out["ok"] = false; out["error"] = "permission"; lastLocationResult = out; return out }
        val lm = a.getSystemService(Context.LOCATION_SERVICE) as LocationManager?
        if (lm == null) { out["ok"] = false; out["error"] = "noloc"; lastLocationResult = out; return out }
        fun pack(loc: Location): Dictionary {
            val d = Dictionary()
            d["ok"] = true
            d["lat"] = r1(loc.latitude)
            d["lon"] = r1(loc.longitude)
            return d
        }
        var best: Location? = null
        for (p in listOf(LocationManager.NETWORK_PROVIDER, LocationManager.PASSIVE_PROVIDER)) {
            try {
                val l = lm.getLastKnownLocation(p)
                if (l != null && (best == null || l.time > best!!.time)) best = l
            } catch (_: Exception) {}
        }
        if (best != null && System.currentTimeMillis() - best!!.time < 6 * 3600_000L) {
            val p = pack(best!!)
            lastLocationResult = p
            emitSignal("location_result", p)
            return p
        }
        val enabled = try { lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER) } catch (_: Exception) { false }
        if (!enabled) {
            if (best != null) {
                val p = pack(best!!); lastLocationResult = p; emitSignal("location_result", p); return p
            }
            out["ok"] = false; out["error"] = "noloc"; lastLocationResult = out; return out
        }
        val done = AtomicBoolean(false)
        val fallback = best
        val ll = object : LocationListener {
            override fun onLocationChanged(loc: Location) {
                if (done.compareAndSet(false, true)) {
                    lm.removeUpdates(this)
                    val p = pack(loc)
                    lastLocationResult = p
                    emitSignal("location_result", p)
                }
            }
            @Deprecated("API < 29") override fun onStatusChanged(provider: String?, status: Int, extras: Bundle?) {}
            override fun onProviderEnabled(provider: String) {}
            override fun onProviderDisabled(provider: String) {}
        }
        try {
            @Suppress("DEPRECATION")
            lm.requestSingleUpdate(LocationManager.NETWORK_PROVIDER, ll, Looper.getMainLooper())
        } catch (_: Exception) {
            if (done.compareAndSet(false, true)) {
                if (fallback != null) {
                    val p = pack(fallback); lastLocationResult = p; emitSignal("location_result", p)
                } else {
                    out["ok"] = false; out["error"] = "noloc"; lastLocationResult = out; emitSignal("location_result", out)
                }
            }
        }
        main.postDelayed({
            if (done.compareAndSet(false, true)) {
                lm.removeUpdates(ll)
                if (fallback != null) {
                    val p = pack(fallback); lastLocationResult = p; emitSignal("location_result", p)
                } else {
                    val acc = Dictionary(); acc["ok"] = false; acc["error"] = "timeout"
                    lastLocationResult = acc; emitSignal("location_result", acc)
                }
            }
        }, 10000)
        out["ok"] = true
        out["pending"] = true
        return out
    }
}
