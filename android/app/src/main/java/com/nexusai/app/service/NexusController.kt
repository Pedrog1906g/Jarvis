package com.nexusai.app.service

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import com.nexusai.app.util.VoiceManager

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
                voice.speak("Ative o serviço de acessibilidade do NEXUS nas configurações.")
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

        // ---- Abrir app ----
        val openMatch = Regex("""(abra|abrir|abre|inicie|iniciar|entre no|entre em|aberta)\s+(.+)""")
            .find(c)
        if (openMatch != null) {
            val appName = openMatch.groupValues[2].trim()
            val ok = openApp(context, appName)
            voice.speak(if (ok) "Abrindo $appName" else "Não encontrei o app $appName no aparelho.")
            return true
        }

        // ---- Tocar / clicar em texto ----
        val clickMatch = Regex("""(toque|clique|aperte|selecione|toque em|clique em)\s+(.+)""")
            .find(c)
        if (clickMatch != null) {
            val target = clickMatch.groupValues[2].trim()
            val svc = NexusAccessibilityService.instance
            if (svc == null) {
                voice.speak("Ative o serviço de acessibilidade do NEXUS para tocar na tela.")
            } else {
                val ok = svc.clickByText(target)
                voice.speak(if (ok) "Toquei em $target" else "Não encontrei $target na tela.")
            }
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
            "nexus" to "com.nexusai.app"
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
}
