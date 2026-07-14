package com.nexusai.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat

/**
 * Serviço em primeiro plano (stub) para manter a NEXUS "sempre disponível".
 * Expansão futura: escuta contínua por "Ei Nexus" e execução de comandos em background.
 */
class NexusVoiceService : Service() {

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        val nm = getSystemService(NotificationManager::class.java)
        val ch = NotificationChannel("nexus", "NEXUS", NotificationManager.IMPORTANCE_LOW)
        nm.createNotificationChannel(ch)
        val notif = NotificationCompat.Builder(this, "nexus")
            .setContentTitle("NEXUS ativo")
            .setContentText("Assistente em segundo plano")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .build()
        startForeground(1, notif)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY
}
