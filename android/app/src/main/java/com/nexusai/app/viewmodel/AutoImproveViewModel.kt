package com.nexusai.app.viewmodel

import android.app.Application
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.repository.NexusRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class AutoImproveViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    var tokenConfigured = mutableStateOf(false)
    var tokenSource = mutableStateOf("")
    var tokenInput = mutableStateOf("")
    var statusText = mutableStateOf("")
    var improveRequest = mutableStateOf("")
    var message = mutableStateOf("")

    fun loadStatus() {
        viewModelScope.launch {
            try {
                val s = repo.githubTokenStatus()
                tokenConfigured.value = (s["configured"] as? Boolean) ?: false
                tokenSource.value = (s["source"] as? String) ?: ""
            } catch (e: Exception) {
                message.value = e.localizedMessage ?: ""
            }
        }
    }

    fun saveToken() {
        viewModelScope.launch {
            try {
                val r = repo.setGithubToken(tokenInput.value.trim())
                message.value = (r["message"] as? String) ?: r.toString()
                loadStatus()
            } catch (e: Exception) {
                message.value = e.localizedMessage ?: ""
            }
        }
    }

    fun requestImprove() {
        viewModelScope.launch {
            try {
                val req = improveRequest.value.ifBlank { "melhore a experiência geral do app" }
                val r = repo.selfImprove(req)
                message.value = (r["message"] as? String) ?: r.toString()
                pollStatus()
            } catch (e: Exception) {
                message.value = e.localizedMessage ?: ""
            }
        }
    }

    fun pollStatus() {
        viewModelScope.launch {
            repeat(12) {
                try {
                    val s = repo.selfImproveStatus()
                    val configured = (s["token_configured"] as? Boolean) == true
                    statusText.value = buildString {
                        append("Estado: ${s["status"]} | etapa: ${s["stage"] ?: "-"}\n")
                        append(s["message"] ?: "")
                        append("\nToken: ${if (configured) "configurado (${s["token_source"]})" else "NÃO configurado"}")
                    }
                } catch (e: Exception) {
                    statusText.value = e.localizedMessage ?: ""
                }
                delay(4000)
            }
        }
    }
}
