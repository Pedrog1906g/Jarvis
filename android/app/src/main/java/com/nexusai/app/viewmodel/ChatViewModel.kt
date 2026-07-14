package com.nexusai.app.viewmodel

import android.app.Application
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.ChatMessage
import com.nexusai.app.data.repository.NexusRepository
import com.nexusai.app.util.NexusWebSocket
import kotlinx.coroutines.launch
import java.util.UUID

class ChatViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    val messages = mutableStateListOf<ChatMessage>()
    var conversationId = mutableStateOf<Int?>(null)
    var isThinking = mutableStateOf(false)
    var error = mutableStateOf<String?>(null)

    private var ws: NexusWebSocket? = null
    private var streamingIndex: Int? = null

    fun ensureConnected() {
        if (ws == null) {
            val token = repo.tokenStore.getToken() ?: return
            val base = repo.tokenStore.getServerUrl()
            ws = NexusWebSocket(
                baseUrl = base,
                token = token,
                onDelta = { delta -> appendDelta(delta) },
                onDone = { cid -> if (cid > 0) conversationId.value = cid; isThinking.value = false },
                onError = { e -> error.value = e; isThinking.value = false }
            )
            ws?.connect()
        }
    }

    private fun appendDelta(delta: String) {
        if (streamingIndex == null) {
            messages.add(ChatMessage(id = UUID.randomUUID().toString(), role = "assistant", content = ""))
            streamingIndex = messages.lastIndex
        }
        val idx = streamingIndex!!
        val cur = messages[idx]
        messages[idx] = cur.copy(content = cur.content + delta)
    }

    fun send(text: String) {
        val t = text.trim()
        if (t.isBlank()) return
        ensureConnected()
        messages.add(ChatMessage(id = UUID.randomUUID().toString(), role = "user", content = t))
        isThinking.value = true
        error.value = null
        streamingIndex = null
        ws?.send(t, conversationId.value)
    }

    fun loadConversation(cid: Int) {
        viewModelScope.launch {
            try {
                val msgs = repo.messages(cid)
                messages.clear()
                msgs.forEach {
                    messages.add(ChatMessage(id = UUID.randomUUID().toString(), role = it.role, content = it.content))
                }
                conversationId.value = cid
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }

    fun newConversation() {
        messages.clear()
        conversationId.value = null
        streamingIndex = null
    }

    override fun onCleared() {
        ws?.close()
    }
}
