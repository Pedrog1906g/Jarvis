package com.nexusai.app.data.repository

import com.nexusai.app.data.model.*
import com.nexusai.app.data.remote.NexusApi
import com.nexusai.app.data.remote.RetrofitClient
import com.nexusai.app.data.store.TokenStore

class NexusRepository(val tokenStore: TokenStore) {

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

    // ---- Conversa: deletar ----
    suspend fun deleteConversation(cid: Int): DeleteResult = api.deleteConversation(auth(), cid)

    // ---- Auto-melhoria de código ----
    suspend fun selfImprove(request: String): Map<String, Any> =
        api.selfImprove(auth(), mapOf("request" to request))

    suspend fun selfImproveStatus(): Map<String, Any> = api.selfImproveStatus(auth())

    suspend fun setGithubToken(token: String): Map<String, Any> =
        api.setGithubToken(auth(), mapOf("token" to token))

    suspend fun githubTokenStatus(): Map<String, Any> = api.githubTokenStatus(auth())

    // ---- Memória de longo prazo ----
    suspend fun memoryFacts(): List<MemoryFact> = api.memoryFacts(auth())
    suspend fun addMemoryFact(fact: String, category: String = "geral", importance: Int = 1): Map<String, Any> =
        api.addMemoryFact(auth(), MemoryFactRequest(fact, category, importance))
    suspend fun deleteMemoryFact(fid: Int): Map<String, Any> = api.deleteMemoryFact(auth(), fid)
    suspend fun clearMemoryFacts(): Map<String, Any> = api.clearMemoryFacts(auth())
    suspend fun memorySummary(): MemorySummary = api.memorySummary(auth())

    // ---- Spotify OAuth2 ----
    suspend fun spotifyAuthStart(): SpotifyAuthUrl = api.spotifyAuthStart(auth())
    suspend fun spotifyNowPlaying(): SpotifyCommandResult = api.spotifyNowPlaying(auth())
    suspend fun spotifyStatus(): SpotifyStatus = api.spotifyStatus(auth())
    suspend fun spotifyCommand(cmd: String): Map<String, Any> = api.spotifyCommand(auth(), mapOf("command" to cmd))

    // ---- Voz / TTS ----
    suspend fun voiceInfo(): VoiceInfo = api.voiceInfo(auth())
    suspend fun synthesizeSpeech(text: String): okhttp3.ResponseBody =
        api.synthesizeSpeech(auth(), mapOf("text" to text))
}
