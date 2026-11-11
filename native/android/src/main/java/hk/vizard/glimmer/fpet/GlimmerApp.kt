package hk.vizard.glimmer.fpet

import android.app.Activity
import android.app.Application
import android.os.Bundle

/**
 * 追蹤 Godot activity 有冇喺前台：前台時收起團絨，離開先出。
 * 唔再當 Application（Godot 用自己嘅 Application）；由 GlimmerOverlayPlugin 喺 onMainCreate 安裝。
 */
object GlimmerApp {
    @Volatile var visible = false
    var visibilityListener: ((Boolean) -> Unit)? = null
    private var started = 0
    private var installed = false

    fun install(app: Application) {
        if (installed) return
        installed = true
        app.registerActivityLifecycleCallbacks(object : Application.ActivityLifecycleCallbacks {
            override fun onActivityStarted(a: Activity) { started++; update() }
            override fun onActivityStopped(a: Activity) { started = maxOf(0, started - 1); update() }
            override fun onActivityCreated(a: Activity, b: Bundle?) {}
            override fun onActivityResumed(a: Activity) {}
            override fun onActivityPaused(a: Activity) {}
            override fun onActivitySaveInstanceState(a: Activity, b: Bundle) {}
            override fun onActivityDestroyed(a: Activity) {}
        })
    }

    private fun update() {
        val v = started > 0
        if (v != visible) {
            visible = v
            visibilityListener?.invoke(v)
        }
    }
}
