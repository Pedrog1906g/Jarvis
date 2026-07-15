package com.nexusai.app.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.ChatMessage
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.service.NexusController
import com.nexusai.app.util.NexusWebSocket
import com.nexusai.app.util.VoiceManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.UUID

class ChatViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    // StateFlow é thread-safe: pode ser atualizado de qualquer thread
    // (incluindo a thread de fundo do OkHttp que entrega o WebSocket).
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _conversationId = MutableStateFlow<Int?>(null)
    val conversationId: StateFlow<Int?> = _conversationId.asStateFlow()

    private val _isThinking = MutableStateFlow(false)
    val isThinking: StateFlow<Boolean> = _isThinking.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()

    private var ws: NexusWebSocket? = null
    private var wsOpen = false
    private var pendingText: String? = null
    private var streamingIndex: Int? = null

    // Voz (TTS/STT) — instância única, com o contexto da Application.
    private val voice = VoiceManager(app)

    init {
        voice.initTts()
    }

    fun getVoice(): VoiceManager = voice

    fun ensureConnected() {
        if (ws == null) {
            val token = repo.tokenStore.getToken() ?: return
            val base = repo.tokenStore.getServerUrl()
            ws = NexusWebSocket(
                baseUrl = base,
                token = token,
                onDelta = { appendDelta(it) },
                onDone = { cid ->
                    if (cid > 0) _conversationId.value = cid
                    _isThinking.value = false
                    // Fala a resposta do assistente automaticamente.
                    _messages.value.lastOrNull()?.let {
                        if (it.role == "assistant") voice.speak(it.content)
                    }
                },
                onError = { e ->
                    wsOpen = false
                    _error.value = e
                    _isThinking.value = false
                    pendingText?.let { fallbackRest(it) }
                },
                onOpen = { wsOpen = true }
            )
            ws?.connect()
        }
    }

    private fun appendDelta(delta: String) {
        val idx = if (streamingIndex == null) {
            val newMsg = ChatMessage(id = UUID.randomUUID().toString(), role = "assistant", content = "")
            _messages.value = _messages.value + newMsg
            streamingIndex = _messages.value.lastIndex
            _messages.value.lastIndex
        } else {
            streamingIndex!!
        }
        val cur = _messages.value[idx]
        val updated = _messages.value.toMutableList().apply {
            this[idx] = cur.copy(content = cur.content + delta)
        }
        _messages.value = updated
    }

    fun send(text: String) {
        val t = text.trim()
        if (t.isBlank()) return
        // Comandos de controle local (música, abrir apps, ler tela, notificações)
        // funcionam tanto por voz quanto digitando — fora do backend.
        if (NexusController.tryHandleLocal(getApplication(), t, voice)) return
        ensureConnected()
        _messages.value = _messages.value + ChatMessage(id = UUID.randomUUID().toString(), role = "user", content = t)
        _isThinking.value = true
        _error.value = null
        streamingIndex = null
        pendingText = t
        if (ws != null && wsOpen) {
            ws?.send(t, _conversationId.value)
        } else {
            fallbackRest(t)
        }
    }

    fun loadConversation(cid: Int) {
        viewModelScope.launch {
            try {
                val msgs = repo.messages(cid)
                _messages.value = msgs.map {
                    ChatMessage(id = UUID.randomUUID().toString(), role = it.role, content = it.content)
                }
                _conversationId.value = cid
            } catch (e: Exception) {
                _error.value = e.localizedMessage
            }
        }
    }

    fun newConversation() {
        _messages.value = emptyList()
        _conversationId.value = null
        streamingIndex = null
    }

    fun reportError(msg: String?) {
        _error.value = msg
        _isThinking.value = false
    }

    private fun fallbackRest(text: String) {
        viewModelScope.launch {
            _isThinking.value = true
            try {
                val resp = repo.chat(text, _conversationId.value)
                _conversationId.value = resp.conversationId
                _messages.value = _messages.value + ChatMessage(
                    id = UUID.randomUUID().toString(), role = "assistant", content = resp.reply
                )
                voice.speak(resp.reply)
            } catch (e: Exception) {
                _error.value = e.localizedMessage ?: "Falha ao falar com o servidor"
            } finally {
                _isThinking.value = false
                pendingText = null
            }
        }
    }

    override fun onCleared() {
        ws?.close()
        voice.shutdown()
    }
}
