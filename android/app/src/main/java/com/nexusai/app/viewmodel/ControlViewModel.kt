package com.nexusai.app.viewmodel

import android.app.Application
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.service.NexusAccessibilityService
import com.nexusai.app.service.NexusNotificationListener

class ControlViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    var accessibilityEnabled = mutableStateOf(false)
    var notificationEnabled = mutableStateOf(false)
    var status = mutableStateOf("")
    var screenText = mutableStateOf("")

    fun refresh(context: Context) {
        accessibilityEnabled.value = isAccessibilityEnabled(context)
        notificationEnabled.value = NexusNotificationListener.isEnabled(context)
    }

    fun isAccessibilityEnabled(context: Context): Boolean {
        val cn = ComponentName(context, NexusAccessibilityService::class.java).flattenToString()
        val enabled = Settings.Secure.getString(
            context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: ""
        return enabled.split(":").any { it.equals(cn, ignoreCase = true) }
    }

    fun openAccessibilitySettings(context: Context) {
        context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
    }

    fun openNotificationSettings(context: Context) {
        context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
    }

    fun readScreen() {
        val svc = NexusAccessibilityService.instance
        if (svc == null) {
            status.value = "Serviço de acessibilidade não está ativo."
            return
        }
        val text = svc.readScreen()
        screenText.value = if (text.isBlank()) "(sem texto na tela)" else text.take(2000)
    }

    fun click(text: String) {
        val svc = NexusAccessibilityService.instance
        if (svc == null) {
            status.value = "Serviço de acessibilidade não está ativo."
            return
        }
        val ok = svc.clickByText(text)
        status.value = if (ok) "Toquei em \"$text\"" else "Não encontrei \"$text\" na tela atual."
    }

    fun scroll(direction: String) {
        val svc = NexusAccessibilityService.instance
        if (svc == null) {
            status.value = "Serviço de acessibilidade não está ativo."
            return
        }
        val ok = svc.scroll(direction)
        status.value = if (ok) "Rolei para $direction" else "Não consegui rolar."
    }

    fun notificationsSummary(): String = NexusNotificationListener.summary()
}
