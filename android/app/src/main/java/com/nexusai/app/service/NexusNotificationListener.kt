package com.nexusai.app.service

import android.content.Context
import android.provider.Settings
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import java.util.concurrent.ConcurrentHashMap

/**
 * Leitor de Notificações do NEXUS (Fase 3).
 *
 * O usuário ativa manualmente em Configurações > Notificações > Ouvir notificações.
 * Guarda as notificações recebidas em memória para que o assistente possa lê-las
 * quando pedido ("leia minhas notificações"). Nada é enviado a servidores externos.
 */
class NexusNotificationListener : NotificationListenerService() {

    data class Entry(val pkg: String, val title: String, val text: String, val ts: Long)

    companion object {
        private val latest = ConcurrentHashMap<Long, Entry>()
        var instance: NexusNotificationListener? = null

        fun isEnabled(context: Context): Boolean {
            val enabled = Settings.Secure.getString(
                context.contentResolver, "enabled_notification_listeners"
            ) ?: ""
            return enabled.contains(context.packageName)
        }

        fun summary(): String {
            if (latest.isEmpty()) return "Nenhuma notificação recente."
            return latest.values.sortedByDescending { it.ts }.take(10).joinToString("\n") {
                val app = it.pkg.split(".").lastOrNull() ?: it.pkg
                "$app: ${it.title} — ${it.text}"
            }
        }
    }

    override fun onListenerConnected() {
        instance = this
        super.onListenerConnected()
    }

    override fun onListenerDisconnected() {
        instance = null
        super.onListenerDisconnected()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        sbn ?: return
        val extras = sbn.notification.extras ?: return
        val title = extras.getCharSequence("android.title")?.toString() ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""
        val entry = Entry(sbn.packageName ?: "", title, text, System.currentTimeMillis())
        latest[System.currentTimeMillis()] = entry
        while (latest.size > 50) {
            latest.entries.firstOrNull()?.key?.let { latest.remove(it) }
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {}
}
