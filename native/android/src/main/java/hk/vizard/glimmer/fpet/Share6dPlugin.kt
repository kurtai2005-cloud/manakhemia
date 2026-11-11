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
import org.godotengine.godot.Dictionary
import org.godotengine.godot.Godot
import org.godotengine.godot.plugin.GodotPlugin
import org.godotengine.godot.plugin.UsedByGodot
import java.io.File

/**
 * 6d「朋友碼」Godot 橋（由 Capacitor Share6dPlugin 移植）。冇新權限、冇網絡。
 * copy／paste：系統剪貼簿。saveImage：Pictures/微光小圃。share：FileProvider + ACTION_SEND。
 */
class Share6dPlugin(godot: Godot) : GodotPlugin(godot) {
    override fun getPluginName(): String = "Share6d"

    private fun safeName(n: String?): String {
        val b = (n ?: "glimmer-6d.png").replace(Regex("[^A-Za-z0-9._-]"), "_").take(64)
        return if (b.endsWith(".png")) b else "$b.png"
    }

    private fun bytesOf(data: String?): ByteArray? {
        if (data.isNullOrEmpty()) return null
        return try { Base64.decode(data, Base64.DEFAULT) } catch (_: IllegalArgumentException) { null }
    }

    @UsedByGodot
    fun copy(text: String): Dictionary {
        val out = Dictionary()
        val a = activity
        if (a == null || text.isEmpty()) { out["ok"] = false; out["error"] = "notext"; return out }
        val cm = a.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        cm.setPrimaryClip(ClipData.newPlainText("微光小圃朋友碼", text))
        out["ok"] = true
        return out
    }

    @UsedByGodot
    fun paste(): Dictionary {
        val out = Dictionary()
        val a = activity
        if (a == null) { out["ok"] = true; out["text"] = ""; return out }
        val cm = a.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        val clip = cm.primaryClip
        val t = if (clip != null && clip.itemCount > 0) clip.getItemAt(0).coerceToText(a)?.toString() else null
        out["ok"] = true
        out["text"] = t ?: ""
        return out
    }

    @UsedByGodot
    fun saveImage(data: String, name: String): Dictionary {
        val out = Dictionary()
        val a = activity
        val bytes = bytesOf(data)
        if (a == null || bytes == null) { out["ok"] = false; out["error"] = "nodata"; return out }
        if (bytes.size > 8 * 1024 * 1024) { out["ok"] = false; out["error"] = "toobig"; return out }
        val fname = safeName(name)
        return try {
            if (Build.VERSION.SDK_INT >= 29) {
                val cv = ContentValues().apply {
                    put(MediaStore.Images.Media.DISPLAY_NAME, fname)
                    put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                    put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/微光小圃")
                    put(MediaStore.Images.Media.IS_PENDING, 1)
                }
                val res = a.contentResolver
                val uri = res.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, cv)
                    ?: return Dictionary().apply { put("ok", false); put("error", "insert") }
                res.openOutputStream(uri)?.use { it.write(bytes) }
                    ?: return Dictionary().apply { put("ok", false); put("error", "open") }
                cv.clear(); cv.put(MediaStore.Images.Media.IS_PENDING, 0); res.update(uri, cv, null, null)
                out["ok"] = true
                out["uri"] = uri.toString()
                out["gallery"] = true
            } else {
                val dir = a.getExternalFilesDir(Environment.DIRECTORY_PICTURES) ?: a.filesDir
                val f = File(dir, fname); f.writeBytes(bytes)
                out["ok"] = true
                out["path"] = f.absolutePath
                out["gallery"] = false
            }
            out
        } catch (e: Exception) {
            out["ok"] = false
            out["error"] = "save:" + e.javaClass.simpleName
            out
        }
    }

    @UsedByGodot
    fun share(data: String, name: String, text: String): Dictionary {
        val out = Dictionary()
        val a = activity
        val bytes = bytesOf(data)
        if (a == null || bytes == null) { out["ok"] = false; out["error"] = "nodata"; return out }
        if (bytes.size > 8 * 1024 * 1024) { out["ok"] = false; out["error"] = "toobig"; return out }
        return try {
            val dir = File(a.cacheDir, "share6d"); dir.mkdirs()
            dir.listFiles()?.forEach { it.delete() }
            val f = File(dir, safeName(name)); f.writeBytes(bytes)
            val uri = FileProvider.getUriForFile(a, a.packageName + ".fileprovider", f)
            val send = Intent(Intent.ACTION_SEND).apply {
                type = "image/png"
                putExtra(Intent.EXTRA_STREAM, uri)
                if (text.isNotEmpty()) putExtra(Intent.EXTRA_TEXT, text)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            val ch = Intent.createChooser(send, "分享朋友碼").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            a.startActivity(ch)
            out["ok"] = true
            out
        } catch (e: Exception) {
            out["ok"] = false
            out["error"] = "share:" + e.javaClass.simpleName
            out
        }
    }
}
