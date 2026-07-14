package com.nexusai.app.viewmodel

import android.app.Application
import android.content.Context
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.BuildConfig
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.SystemInfo
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.service.NexusVoiceService
import com.nexusai.app.util.UpdateChecker
import com.nexusai.app.util.VoiceManager
import kotlinx.coroutines.launch

class SettingsViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository
    private val voice = VoiceManager(app)

    var serverUrl = mutableStateOf(repo.tokenStore.getServerUrl())
    var info = mutableStateOf<SystemInfo?>(null)
    var error = mutableStateOf<String?>(null)
    var saved = mutableStateOf(false)
    var wakeWord = mutableStateOf(false)

    // Voz do JARVIS
    var pitch = mutableStateOf(voice.pitch)
    var voiceStatus = mutableStateOf<String?>(null)

    // Atualização
    var updateStatus = mutableStateOf<String?>(null)
    var updateAvailable = mutableStateOf(false)

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

    // ---- Voz ----
    fun setPitch(value: Float) {
        voice.pitch = value
        pitch.value = value
    }

    fun testVoice() {
        voice.initTts {
            voice.applyJarvisVoice()
            voice.speak("Teste de voz do JARVIS. Sempre às ordens.")
        }
        voiceStatus.value = "Testando a voz…"
    }

    // ---- Atualização ----
    fun checkUpdate(context: Context) {
        viewModelScope.launch {
            updateStatus.value = "Verificando atualizações…"
            val rel = UpdateChecker.fetchLatest()
            if (rel == null) {
                updateStatus.value = "Não foi possível verificar (sem internet?)."
                return@launch
            }
            if (UpdateChecker.isUpdateAvailable(rel)) {
                updateAvailable.value = true
                updateStatus.value = "Nova versão (${rel.version}) disponível. Baixando…"
                val file = UpdateChecker.downloadApk(context, rel.url) { p ->
                    updateStatus.value = "Baixando atualização… $p%"
                }
                if (file != null) {
                    updateStatus.value = "Download pronto. Abrindo instalador…"
                    UpdateChecker.install(context, file)
                    updateStatus.value = null
                } else {
                    updateStatus.value = "Falhou ao baixar a atualização."
                }
            } else {
                updateAvailable.value = false
                updateStatus.value = "Você já tem a versão mais recente (${BuildConfig.VERSION_CODE})."
            }
        }
    }

    override fun onCleared() {
        voice.shutdown()
    }
}
