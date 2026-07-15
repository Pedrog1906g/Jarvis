package com.nexusai.app.service

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
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

    /** Toca música de verdade: abre o app (Spotify) ou o vídeo do YouTube já tocando. */
    private fun playMusic(context: Context, command: String, voice: VoiceManager) {
        val q = command.lowercase()
            .replace(Regex("""(?i).*?\b(tocar|toque|ouvir|play|m[úu]sica|som)\b"""), "")
            .replace(Regex("""(?i)\b(no spotify|no youtube|youtube|spotify|deezer|app|da |do )\b"""), " ")
            .trim().ifBlank { "lofi hip hop" }
        val useSpotify = command.lowercase().contains("spotify")
        Thread {
            try {
                val videoId = if (useSpotify) null else resolveYouTubeVideoId(q)
                val uri = if (useSpotify) {
                    Uri.parse("https://open.spotify.com/search/" + Uri.encode(q))
                } else if (!videoId.isNullOrBlank()) {
                    Uri.parse("https://www.youtube.com/watch?v=$videoId")
                } else {
                    Uri.parse("https://www.youtube.com/results?search_query=" + Uri.encode(q))
                }
                context.startActivity(Intent(Intent.ACTION_VIEW, uri).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                })
                val label = if (useSpotify) "Abrindo no Spotify"
                            else if (!videoId.isNullOrBlank()) "Tocando $q"
                            else "Abrindo música"
                voice.speak(label)
            } catch (_: Exception) {
                voice.speak("Não consegui abrir o player de música.")
            }
        }.start()
    }

    /** Busca o 1º vídeo do YouTube para a query (para já começar a tocar). */
    private fun resolveYouTubeVideoId(query: String): String? {
        return try {
            val url = "https://www.youtube.com/results?search_query=" + URLEncoder.encode(query, "UTF-8")
            val conn = URL(url).openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.setRequestProperty("User-Agent", "Mozilla/5.0")
            conn.connectTimeout = 8000
            conn.readTimeout = 8000
            val html = conn.inputStream.bufferedReader().readText()
            val m = Regex("\"videoId\":\"([A-Za-z0-9_-]{11})\"").find(html)
            m?.groupValues?.get(1)
        } catch (_: Exception) { null }
    }
}
