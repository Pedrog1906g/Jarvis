package com.nexusai.app.data.model

import com.google.gson.annotations.SerializedName

data class LoginRequest(val username: String = "owner", val passphrase: String)
data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String = "bearer",
    val user: UserInfo
)
data class UserInfo(val id: Int, val username: String, @SerializedName("display_name") val displayName: String)

data class ChatRequest(val content: String, @SerializedName("conversation_id") val conversationId: Int? = null)
data class ChatResponse(
    @SerializedName("conversation_id") val conversationId: Int,
    val reply: String,
    val demo: Boolean
)

data class ConversationSummary(
    val id: Int,
    val title: String,
    @SerializedName("updated_at") val updatedAt: String?,
    val preview: String
)
data class MessageDto(val id: Int, val role: String, val content: String)

data class ReminderDto(
    val id: Int,
    val title: String,
    val note: String?,
    @SerializedName("due_at") val dueAt: String,
    val done: Boolean
)
data class ReminderRequest(val title: String, val note: String? = null, @SerializedName("due_at") val dueAt: String)

data class SystemInfo(
    val app: String,
    val version: String,
    @SerializedName("llm_available") val llmAvailable: Boolean,
    @SerializedName("demo_mode") val demoMode: Boolean,
    val user: UserInfo,
    val changelog: String,
    @SerializedName("update_available") val updateAvailable: Boolean
)

data class PluginState(val name: String, val enabled: Boolean)

// Modelo de UI (não serializado)
data class ChatMessage(val id: String, val role: String, val content: String)
