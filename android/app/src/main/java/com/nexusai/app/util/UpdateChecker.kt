package com.nexusai.app.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import androidx.core.content.FileProvider
import com.nexusai.app.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.io.File

/** Informações da última release pública do app. */
data class ReleaseInfo(
    val version: Int,
    val name: String,
    val tag: String,
    val url: String,
    val notes: String
)

/**
 * Verifica e instala atualizações do app direto do GitHub Releases.
 * O versionCode de cada APK é igual ao número da release (nexus-ai-N), então
 * basta comparar com BuildConfig.VERSION_CODE.
 */
object UpdateChecker {
    private const val REPO = "Pedrog1906g/Jarvis"
    private const val API_LIST = "https://api.github.com/repos/$REPO/releases"
    private const val AUTHORITY = "com.nexusai.app.fileprovider"
    private val client = OkHttpClient()

    /** Busca a release mais nova (maior número nexus-ai-N), ignorando rascunhos. */
    suspend fun fetchLatest(): ReleaseInfo? = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url("$API_LIST?per_page=100")
                .header("Accept", "application/vnd.github+json")
                .build()
            val resp = client.newCall(req).execute()
            val body = resp.body?.string() ?: return@withContext null
            val arr = org.json.JSONArray(body)
            var best: ReleaseInfo? = null
            for (i in 0 until arr.length()) {
                val j = arr.getJSONObject(i)
                if (j.optBoolean("draft", false) || j.optBoolean("prerelease", false)) continue
                val tag = j.optString("tag_name", "")
                val version = Regex("(\\d+)").find(tag)?.value?.toIntOrNull() ?: 0
                if (version <= 0) continue
                val assets = j.optJSONArray("assets")
                var url = ""
                if (assets != null) {
                    for (k in 0 until assets.length()) {
                        val o = assets.getJSONObject(k)
                        if (o.optString("name").endsWith(".apk")) {
                            url = o.optString("browser_download_url")
                            break
                        }
                    }
                }
                if (url.isEmpty()) continue
                if (best == null || version > best!!.version) {
                    best = ReleaseInfo(
                        version = version,
                        name = j.optString("name", tag),
                        tag = tag,
                        url = url,
                        notes = j.optString("body", "")
                    )
                }
            }
            best
        } catch (_: Exception) {
            null
        }
    }

    fun isUpdateAvailable(rel: ReleaseInfo): Boolean =
        rel.version > BuildConfig.VERSION_CODE && rel.url.isNotEmpty()

    suspend fun downloadApk(
        context: Context,
        url: String,
        onProgress: (Int) -> Unit = {}
    ): File? = withContext(Dispatchers.IO) {
        try {
            val req = Request.Builder().url(url).build()
            val resp = client.newCall(req).execute()
            val body = resp.body ?: return@withContext null
            val total = body.contentLength()
            val file = File(context.cacheDir, "nexus_update.apk")
            file.outputStream().use { out ->
                body.byteStream().use { inp ->
                    val buf = ByteArray(8192)
                    var read: Int
                    var done = 0L
                    while (inp.read(buf).also { read = it } != -1) {
                        out.write(buf, 0, read)
                        done += read
                        if (total > 0) onProgress(((done * 100) / total).toInt())
                    }
                }
            }
            file
        } catch (_: Exception) {
            null
        }
    }

    fun install(context: Context, file: File) {
        val uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            FileProvider.getUriForFile(context, AUTHORITY, file)
        } else {
            Uri.fromFile(file)
        }
        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(intent)
    }
}
