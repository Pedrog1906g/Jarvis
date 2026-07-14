package com.nexusai.app.viewmodel

import android.app.Application
import android.content.Context
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.SystemInfo
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.service.NexusVoiceService
import kotlinx.coroutines.launch

class SettingsViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    var serverUrl = mutableStateOf(repo.tokenStore.getServerUrl())
    var info = mutableStateOf<SystemInfo?>(null)
    var error = mutableStateOf<String?>(null)
    var saved = mutableStateOf(false)
    var wakeWord = mutableStateOf(false)

    fun loadInfo() {
        viewModelScope.launch {
            try {
                info.value = repo.systemInfo()
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }

    fun loadWakeWord() {
        wakeWord.value = repo.tokenStore.isWakeWordEnabled()
    }

    fun toggleWakeWord(context: Context, enable: Boolean) {
        repo.tokenStore.setWakeWordEnabled(enable)
        wakeWord.value = enable
        if (enable) NexusVoiceService.start(context) else NexusVoiceService.stop(context)
    }

    fun saveServer(url: String) {
        repo.setServer(url)
        serverUrl.value = url
        saved.value = true
    }
}
