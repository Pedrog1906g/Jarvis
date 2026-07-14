package com.nexusai.app.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.Intent.ACTION_BOOT_COMPLETED
import android.content.Intent.ACTION_MY_PACKAGE_REPLACED
import com.nexusai.app.data.store.TokenStore
import com.nexusai.app.service.NexusVoiceService

/**
 * Reinia o assistente de voz (wake word) após o aparelho ligar ou após atualização
 * do app, caso o usuário tenha deixado a opção ativada.
 */
class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action == ACTION_BOOT_COMPLETED ||
            intent?.action == ACTION_MY_PACKAGE_REPLACED
        ) {
            val ts = TokenStore(context)
            if (ts.isWakeWordEnabled()) {
                NexusVoiceService.start(context)
            }
        }
    }
}
