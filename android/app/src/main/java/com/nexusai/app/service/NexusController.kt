package com.nexusai.app.service

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.util.Base64
import com.nexusai.app.util.VoiceManager
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

/**
 * Comandos de CONTROLE DO CELULAR tratados 100% no aparelho (acessibilidade /
 * notificações / abertura de apps). Só são enviados ao backend quando não forem
 * reconhecidos como ação local — nada de dados de tela sai do dispositivo.
 */
object NexusController {

    /** Tenta tratar localmente comandos de controle. Retorna true se tratou. */
    fun tryHandleLocal(context: Context, command: String, voice: VoiceManager): Boolean {
        val c = command.lowercase().trim()

        // ---- Leitura de tela ----
        if (c.contains("leia a tela") || c.contains("ler a tela") ||
            c.contains("o que está na tela") || c.contains("o que tem na tela") ||
            c.contains("mostre o que tem na tela") || c.contains("ler tela")) {
            val svc = NexusAccessibilityService.instance
            if (svc == null) {
                voice.speak("Ative o serviço de acessibilidade do JARVIS nas configurações.")
            } else {
                val text = svc.readScreen()
                voice.speak(if (text.isBlank()) "A tela está vazia ou sem texto." else text.take(400))
            }
            return true
        }

        // ---- Notificações ----
        if (c.contains("minhas notificações") || c.contains("ler notificação") ||
            c.contains("leia as notificações") || c.contains("o que chegou") ||
            c.contains("tem notificação") || c.contains("notificações recentes")) {
            voice.speak(NexusNotificationListener.summary().take(400))
            return true
        }

        // ---- Abrir app (antes da música p/ "abrir youtube" não virar "tocar") ----
        val openMatch = Regex("""(abra|abrir|abre|inicie|iniciar|entre no|entre em|aberta|abre o|abre a|abrir o|abrir a|abrir o app|abre o app)\s+(.+)""")
            .find(c)
        if (openMatch != null) {
            val raw = openMatch.groupValues[2].trim()
            val appName = raw.replace(
                Regex("""\b(o|a|os|as|do|da|dos|das|no|na|nos|nas|um|uma|app|meu|minha)\b"""), " "
            ).trim().ifBlank { raw }
            val ok = openApp(context, appName)
            voice.speak(if (ok) "Abrindo $appName" else "Não encontrei o app $appName no aparelho.")
            return true
        }

        // ---- Tocar / clicar em texto na tela ----
        val clickMatch = Regex("""(toque em|toque no|toque na|clique em|clique no|aperte|selecione)\s+(.+)""")
            .find(c)
        if (clickMatch != null) {
            val target = clickMatch.groupValues[2].trim()
            val svc = NexusAccessibilityService.instance
            if (svc == null) {
                voice.speak("Ative o serviço de acessibilidade do JARVIS para tocar na tela.")
            } else {
                val ok = svc.clickByText(target)
                voice.speak(if (ok) "Toquei em $target" else "Não encontrei $target na tela.")
            }
            return true
        }

                // ---- Música / tocar ----
        if (c.contains("tocar") || c.contains("toque") || c.contains("música") ||
            c.contains("musica") || c.contains("ouvir") || c.contains("som") ||
            c.contains("play") || c.contains("spotify") || c.contains("youtube") ||
            c.contains("youtube music") || c.contains("deezer")
        ) {
            playMusic(context, command, voice)
            return true
        }

        // ---- Rolar ----
        if (c.contains("role para baixo") || c.contains("descer") || c.contains("role pra baixo")) {
            val svc = NexusAccessibilityService.instance
            voice.speak(if (svc?.scroll("down") == true) "Rolei para baixo" else "Não consegui rolar")
            return true
        }
        if (c.contains("role para cima") || c.contains("subir") || c.contains("role pra cima")) {
            val svc = NexusAccessibilityService.instance
            voice.speak(if (svc?.scroll("up") == true) "Rolei para cima" else "Não consegui rolar")
            return true
        }

        return false
    }

    /** Abre um app pelo nome (lista conhecida ou busca por rótulo instalado). */
    fun openApp(context: Context, name: String): Boolean {
        val pm = context.packageManager
        val target = name.lowercase()

        val known = mapOf(
            "whatsapp" to "com.whatsapp",
            "instagram" to "com.instagram.android",
            "youtube" to "com.google.android.youtube",
            "youtube music" to "com.google.android.apps.youtube.music",
            "maps" to "com.google.android.apps.maps",
            "gmail" to "com.google.android.gm",
            "chrome" to "com.android.chrome",
            "spotify" to "com.spotify.music",
            "facebook" to "com.facebook.katana",
            "mensagens" to "com.google.android.apps.messaging",
            "telefone" to "com.android.dialer",
            "câmera" to "com.android.camera",
            "camera" to "com.android.camera",
            "configurações" to "com.android.settings",
            "configuracoes" to "com.android.settings",
            "tiktok" to "com.zhiliaoapp.musically",
            "twitter" to "com.twitter.android",
            "x" to "com.twitter.android",
            "linkedin" to "com.linkedin.android",
            "netflix" to "com.netflix.mediaclient",
            "telegram" to "org.telegram.messenger",
            "drive" to "com.google.android.apps.docs",
            "calendário" to "com.google.android.calendar",
            "calculadora" to "com.google.android.calculator",
            "nexus" to "com.nexusai.app",
            "jarvis" to "com.nexusai.app"
        )
        val pkg = known.entries.firstOrNull { target.contains(it.key) }?.value
        if (pkg != null && launch(context, pkg)) return true

        val intent = Intent(Intent.ACTION_MAIN, null).apply {
            addCategory(Intent.CATEGORY_LAUNCHER)
        }
        val apps = pm.queryIntentActivities(intent, PackageManager.MATCH_ALL)
        for (resolve in apps) {
            val label = resolve.loadLabel(pm).toString().lowercase()
            if (label.contains(target) || resolve.activityInfo.packageName.lowercase().contains(target)) {
                if (launch(context, resolve.activityInfo.packageName)) return true
            }
        }
        return false
    }

    private fun launch(context: Context, pkg: String): Boolean {
        val intent = context.packageManager.getLaunchIntentForPackage(pkg)
        if (intent != null) {
            try {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(intent)
                return true
            } catch (_: Exception) {
            }
        }
        return false
    }

    // -------------------- Música: YouTube (melhor vídeo) + Spotify (tocar) --------------------

    private val STOP = setOf(
        "a", "o", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas",
        "um", "uma", "umas", "para", "com", "que", "seu", "sua", "seus", "su", "as", "os",
        "ao", "aos", "pela", "pelas", "pelo", "the", "of", "to", "and"
    )

    private val YT_RE = Regex(
        "\"videoId\":\"([A-Za-z0-9_-]{11})\".*?\"title\":\\{\"runs\":\\[\\{\"text\":\"(.*?)\"\\}\\]",
        RegexOption.DOT_MATCHES_ALL
    )

    private fun norm(s: String): List<String> =
        Regex("[a-z0-9]+").findAll(s.lowercase()).map { it.value }.toList()

    private fun score(qtok: List<String>, ttok: List<String>): Double {
        if (ttok.isEmpty()) return 0.0
        val ts = ttok.filter { it !in STOP }.toSet()
        val qs = qtok.filter { it !in STOP }.toSet()
        if (qs.isEmpty()) return 0.0
        val inter = qs.intersect(ts)
        val j = inter.size.toDouble() / (qs.union(ts).size)
        return j * 100 + inter.size * 5
    }

    private fun ytPairs(query: String): List<Pair<String, String>> {
        return try {
            val url = "https://www.youtube.com/results?search_query=" + URLEncoder.encode(query, "UTF-8")
            val conn = (URL(url).openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                setRequestProperty("User-Agent", "Mozilla/5.0")
                connectTimeout = 8000
                readTimeout = 8000
            }
            val html = conn.inputStream.bufferedReader().readText()
            YT_RE.findAll(html).map { it.groupValues[1] to it.groupValues[2] }.toList()
        } catch (_: Exception) { emptyList() }
    }

    /** Escolhe o vídeo que melhor combina com o pedido (não só o 1º da lista). */
    private fun bestYouTubeId(query: String): String? {
        val pairs = ytPairs(query)
        if (pairs.isEmpty()) return null
        val qtok = norm(query)
        var best: String? = null
        var bestSc = -1.0
        for ((vid, rawTitle) in pairs) {
            val title = rawTitle.replace("\\u0026", "&").replace("\\\"", "\"")
            var sc = score(qtok, norm(title))
            val low = title.lowercase()
            if (low.contains("official") || low.contains("original")) sc += 12.0
            if (low.contains("audio") || low.contains("álbum") || low.contains("album")) sc += 6.0
            if (low.contains("live") || low.contains("ao vivo")) sc -= 6.0
            if (low.contains("lyrics") || low.contains("letra") || low.contains("karaoke") ||
                low.contains("instrumental") || low.contains("remix") || low.contains("cover") ||
                low.contains("tutorial") || low.contains("reaction")) sc -= 10.0
            if (qtok.isNotEmpty() && qtok.none { it in STOP } && qtok.all { it in low }) sc += 12.0
            if (sc > bestSc) { bestSc = sc; best = vid }
        }
        return best
    }

    /** Pega o access_token do Spotify via Client Credentials (app-to-app, sem login). */
    private fun spotifyToken(): String? {
        val cid = BuildConfig.SPOTIFY_CLIENT_ID
        val sec = BuildConfig.SPOTIFY_CLIENT_SECRET
        if (cid.isBlank() || sec.isBlank() || cid.startsWith("__")) return null
        return try {
            val auth = Base64.encodeToString("$cid:$sec".toByteArray(), Base64.NO_WRAP)
            val conn = (URL("https://accounts.spotify.com/api/token")).openConnection() as HttpURLConnection
            conn.requestMethod = "POST"
            conn.doOutput = true
            conn.setRequestProperty("Authorization", "Basic $auth")
            conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded")
            conn.connectTimeout = 8000
            conn.readTimeout = 8000
            conn.outputStream.write("grant_type=client_credentials".toByteArray())
            val resp = conn.inputStream.bufferedReader().readText()
            org.json.JSONObject(resp).optString("access_token").ifBlank { null }
        } catch (_: Exception) { null }
    }

    /** Tenta achar o ID exato da música no Spotify (precisa de Premium na conta dona do app). */
    private fun spotifyTrackId(query: String): String? {
        val token = spotifyToken() ?: return null
        return try {
            val q = URLEncoder.encode(query, "UTF-8")
            val conn = (URL("https://api.spotify.com/v1/search?q=$q&type=track&limit=1")).openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.setRequestProperty("Authorization", "Bearer $token")
            conn.connectTimeout = 8000
            conn.readTimeout = 8000
            val resp = conn.inputStream.bufferedReader().readText()
            val items = org.json.JSONObject(resp).getJSONObject("tracks").getJSONArray("items")
            if (items.length() == 0) null else items.getJSONObject(0).getString("id")
        } catch (_: Exception) { null }
    }


    /** Toca música de verdade:
     *  - Spotify: abre a música no app (spotify:track:ID) ou a busca dentro do app.
     *  - YouTube: escolhe o vídeo que melhor combina e já abre tocando. */
    private fun playMusic(context: Context, command: String, voice: VoiceManager) {
        val q = command.lowercase()
            .replace(Regex("""(?i).*?\b(tocar|toque|ouvir|play|m[úu]sica|som)\b"""), "")
            .replace(Regex("""(?i)\b(no spotify|no youtube|youtube|spotify|deezer|app|da |do )\b"""), " ")
            .trim().ifBlank { "lofi hip hop" }
        val useSpotify = command.lowercase().contains("spotify")
        Thread {
            try {
                if (useSpotify) {
                    val tid = spotifyTrackId(q)
                    val uri = if (!tid.isNullOrBlank()) "spotify:track:$tid"
                              else "spotify:search:" + Uri.encode(q)
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    })
                    voice.speak(if (!tid.isNullOrBlank()) "Tocando $q no Spotify" else "Abrindo $q no Spotify")
                } else {
                    val videoId = bestYouTubeId(q)
                    val uri = if (!videoId.isNullOrBlank()) "https://www.youtube.com/watch?v=$videoId"
                              else "https://www.youtube.com/results?search_query=" + Uri.encode(q)
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    })
                    voice.speak(if (!videoId.isNullOrBlank()) "Tocando $q" else "Abrindo música")
                }
            } catch (_: Exception) {
                voice.speak("Não consegui abrir o player de música.")
            }
        }.start()
    }
}
