package hk.vizard.glimmer.fpet

import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import android.util.Base64
import androidx.core.content.FileProvider
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin
import java.io.File

/**
 * 6d「朋友碼」JS 橋（src/long6dui.js 用）。冇新權限、冇網絡。
 * ・copy／paste：系統剪貼簿（淨係純文字朋友碼）。
 * ・saveImage：分享圖 PNG → API 29+ MediaStore「Pictures/微光小圃」（唔使權限）；API 26–28 → app 自己嘅 Pictures 資料夾（唔使權限，相簿未必見到）。
 * ・share：PNG 寫去 cache/share6d → 現有 FileProvider（${applicationId}.fileprovider，cache-path）→ ACTION_SEND（圖＋碼文字）。
 */
@CapacitorPlugin(name = "Share6d")
class Share6dPlugin : Plugin() {
    private fun safeName(n: String?): String {
        val b = (n ?: "glimmer-6d.png").replace(Regex("[^A-Za-z0-9._-]"), "_").take(64)
        return if (b.endsWith(".png")) b else "$b.png"
    }

    private fun bytesOf(call: PluginCall): ByteArray? {
        val d = call.getString("data") ?: return null
        return try { Base64.decode(d, Base64.DEFAULT) } catch (e: IllegalArgumentException) { null }
    }

    @PluginMethod
    fun copy(call: PluginCall) {
        val t = call.getString("text") ?: return call.reject("notext")
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("微光小圃朋友碼", t))
        call.resolve()
    }

    @PluginMethod
    fun paste(call: PluginCall) {
        val cm = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = cm.primaryClip
        val t = if (clip != null && clip.itemCount > 0) clip.getItemAt(0).coerceToText(context)?.toString() else null
        val r = JSObject(); r.put("text", t ?: ""); call.resolve(r)
    }

    @PluginMethod
    fun saveImage(call: PluginCall) {
        val bytes = bytesOf(call) ?: return call.reject("nodata")
        if (bytes.size > 8 * 1024 * 1024) return call.reject("toobig")
        val name = safeName(call.getString("name"))
        try {
            val r = JSObject()
            if (Build.VERSION.SDK_INT >= 29) {
                val cv = ContentValues().apply {
                    put(MediaStore.Images.Media.DISPLAY_NAME, name)
                    put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                    put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/微光小圃")
                    put(MediaStore.Images.Media.IS_PENDING, 1)
                }
                val res = context.contentResolver
                val uri = res.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv) ?: return call.reject("insert")
                res.openOutputStream(uri)?.use { it.write(bytes) } ?: return call.reject("open")
                cv.clear(); cv.put(MediaStore.Images.Media.IS_PENDING, 0); res.update(uri, cv, null, null)
                r.put("uri", uri.toString()); r.put("gallery", true)
            } else {
                val dir = context.getExternalFilesDir(Environment.DIRECTORY_PICTURES) ?: context.filesDir
                val f = File(dir, name); f.writeBytes(bytes)
                r.put("path", f.absolutePath); r.put("gallery", false)
            }
            call.resolve(r)
        } catch (e: Exception) {
            call.reject("save:" + e.javaClass.simpleName)
        }
    }

    @PluginMethod
    fun share(call: PluginCall) {
        val bytes = bytesOf(call) ?: return call.reject("nodata")
        if (bytes.size > 8 * 1024 * 1024) return call.reject("toobig")
        try {
            val dir = File(context.cacheDir, "share6d"); dir.mkdirs()
            dir.listFiles()?.forEach { it.delete() }
            val f = File(dir, safeName(call.getString("name"))); f.writeBytes(bytes)
            val uri = FileProvider.getUriForFile(context, context.packageName + ".fileprovider", f)
            val send = Intent(Intent.ACTION_SEND).apply {
                type = "image/png"
                putExtra(Intent.EXTRA_STREAM, uri)
                call.getString("text")?.let { putExtra(Intent.EXTRA_TEXT, it) }
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            val ch = Intent.createChooser(send, "分享朋友碼").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(ch)
            call.resolve()
        } catch (e: Exception) {
            call.reject("share:" + e.javaClass.simpleName)
        }
    }
}
