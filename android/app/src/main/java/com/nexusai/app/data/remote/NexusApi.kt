package com.nexusai.app.data.remote

import com.nexusai.app.data.model.*
import retrofit2.http.*

interface NexusApi {
    @POST("/api/auth/login")
    suspend fun login(@Body req: LoginRequest): LoginResponse

    @GET("/api/system/info")
    suspend fun systemInfo(@Header("Authorization") auth: String): SystemInfo

    @POST("/api/chat")
    suspend fun chat(@Header("Authorization") auth: String, @Body req: ChatRequest): ChatResponse

    @GET("/api/conversations")
    suspend fun conversations(@Header("Authorization") auth: String): List<ConversationSummary>

    @GET("/api/conversations/{cid}/messages")
    suspend fun messages(@Header("Authorization") auth: String, @Path("cid") cid: Int): List<MessageDto>

    @GET("/api/reminders")
    suspend fun reminders(@Header("Authorization") auth: String): List<ReminderDto>

    @POST("/api/reminders")
    suspend fun createReminder(@Header("Authorization") auth: String, @Body req: ReminderRequest): ReminderDto

    @POST("/api/reminders/{rid}/done")
    suspend fun doneReminder(@Header("Authorization") auth: String, @Path("rid") rid: Int): Map<String, Boolean>

    @GET("/api/plugins")
    suspend fun plugins(@Header("Authorization") auth: String): List<PluginState>

    @POST("/api/plugins/spotify/command")
    suspend fun spotifyCommand(@Header("Authorization") auth: String, @Body body: Map<String, String>): Map<String, Any>

    @POST("/api/plugins/system/command")
    suspend fun systemCommand(@Header("Authorization") auth: String, @Body body: Map<String, String>): Map<String, Any>

    // ---- Auto-melhoria de código ----
    @POST("/api/agent/self_improve")
    suspend fun selfImprove(@Header("Authorization") auth: String, @Body body: Map<String, String>): Map<String, Any>

    @GET("/api/agent/self_improve/status")
    suspend fun selfImproveStatus(@Header("Authorization") auth: String): Map<String, Any>

    @POST("/api/agent/set_github_token")
    suspend fun setGithubToken(@Header("Authorization") auth: String, @Body body: Map<String, String>): Map<String, Any>

    @GET("/api/agent/github_token_status")
    suspend fun githubTokenStatus(@Header("Authorization") auth: String): Map<String, Any>
}
