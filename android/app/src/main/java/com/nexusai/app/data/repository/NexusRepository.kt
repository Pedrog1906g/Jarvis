package com.nexusai.app.data.repository

import com.nexusai.app.data.model.*
import com.nexusai.app.data.remote.NexusApi
import com.nexusai.app.data.remote.RetrofitClient
import com.nexusai.app.data.store.TokenStore

class NexusRepository(private val tokenStore: TokenStore) {

    private val api: NexusApi get() = RetrofitClient.api
    private fun auth() = "Bearer ${tokenStore.getToken()}"

    fun setServer(url: String) {
        tokenStore.setServerUrl(url)
        RetrofitClient.rebuild(url)
    }

    suspend fun login(user: String, pass: String): LoginResponse = api.login(LoginRequest(user, pass))
    suspend fun systemInfo(): SystemInfo = api.systemInfo(auth())
    suspend fun chat(text: String, cid: Int?): ChatResponse = api.chat(auth(), ChatRequest(text, cid))
    suspend fun conversations(): List<ConversationSummary> = api.conversations(auth())
    suspend fun messages(cid: Int): List<MessageDto> = api.messages(auth(), cid)
    suspend fun reminders(): List<ReminderDto> = api.reminders(auth())
    suspend fun createReminder(title: String, dueAt: String, note: String? = null): ReminderDto =
        api.createReminder(auth(), ReminderRequest(title, note, dueAt))
    suspend fun doneReminder(id: Int): Map<String, Boolean> = api.doneReminder(auth(), id)
    suspend fun plugins(): List<PluginState> = api.plugins(auth())
    suspend fun spotify(cmd: String): Map<String, Any> = api.spotifyCommand(auth(), mapOf("command" to cmd))
    suspend fun system(cmd: String): Map<String, Any> = api.systemCommand(auth(), mapOf("command" to cmd))
}
