package hk.vizard.glimmer.fpet

import android.app.Activity
import android.app.Application
import android.os.Bundle

/** 追蹤 app 有冇 activity 喺前台：前台時收起團絨，離開先出。 */
class GlimmerApp : Application() {
    companion object {
        @Volatile var visible = false
        var visibilityListener: ((Boolean) -> Unit)? = null
    }
    private var started = 0
    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(object : ActivityLifecycleCallbacks {
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
        if (v != visible) { visible = v; visibilityListener?.invoke(v) }
    }
}
