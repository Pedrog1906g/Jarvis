package com.nexusai.app.viewmodel

import android.app.Application
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.service.NexusVoiceService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface AuthStatus {
    object Idle : AuthStatus
    object Loading : AuthStatus
    object Success : AuthStatus
    object Error : AuthStatus
}

class AuthViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    private val _token = MutableStateFlow(repo.tokenStore.getToken())
    val token = _token.asStateFlow()

    var serverUrl = mutableStateOf(repo.tokenStore.getServerUrl())
    var username = mutableStateOf("owner")
    var passphrase = mutableStateOf("nexus")
    var status = mutableStateOf<AuthStatus>(AuthStatus.Idle)
    var error = mutableStateOf<String?>(null)

    fun login(user: String, pass: String, server: String) {
        status.value = AuthStatus.Loading
        error.value = null
        viewModelScope.launch {
            try {
                repo.setServer(server)
                val resp = repo.login(user, pass)
                repo.tokenStore.saveToken(resp.accessToken)
                _token.value = resp.accessToken
                status.value = AuthStatus.Success
            } catch (e: Exception) {
                error.value = e.localizedMessage ?: "Falha no login"
                status.value = AuthStatus.Error
            }
        }
    }

    fun unlockWithBiometric() {
        val t = repo.tokenStore.getToken()
        if (t != null) {
            _token.value = t
            status.value = AuthStatus.Success
        }
    }

    fun logout() {
        try { NexusVoiceService.stop(getApplication()) } catch (_: Exception) {}
        repo.tokenStore.clear()
        _token.value = null
        status.value = AuthStatus.Idle
    }
}
