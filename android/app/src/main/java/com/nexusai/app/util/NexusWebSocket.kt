package com.nexusai.app.util

import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Cliente WebSocket para chat em streaming com o backend NEXUS.
 * O backend envia: {type:"start"}, {type:"delta", content}, {type:"done", conversation_id}.
 */
class NexusWebSocket(
    private val baseUrl: String,
    private val token: String,
    private val onDelta: (String) -> Unit,
    private val onDone: (Int) -> Unit,
    private val onError: (String) -> Unit,
    private val onOpen: () -> Unit = {}
) {
    private val client = OkHttpClient.Builder().pingInterval(20, TimeUnit.SECONDS).build()
    private var ws: WebSocket? = null

    fun connect() {
        val wsBase = baseUrl.trimEnd('/')
            .replace("http://", "ws://")
            .replace("https://", "wss://")
        val url = "$wsBase/api/ws/chat?token=$token"
        val req = Request.Builder().url(url).build()
        ws = client.newWebSocket(req, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                onOpen()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    when (json.getString("type")) {
                        "delta" -> onDelta(json.getString("content"))
                        "done" -> onDone(json.optInt("conversation_id", -1))
                        "error" -> onError(json.optString("message", "erro"))
                    }
                } catch (e: Exception) {
                    onError(e.message ?: "resposta inválida")
                }
            }
            override fun onFailure(webSocket: WebSocket, t: Throwable, r: Response?) {
                onError(t.message ?: "falha de conexão")
            }
        })
    }

    fun send(content: String, conversationId: Int?) {
        val obj = JSONObject().apply {
            put("type", "message")
            put("content", content)
            if (conversationId != null) put("conversation_id", conversationId)
        }
        if (ws == null) onError("WebSocket não conectado")
        else ws?.send(obj.toString())
    }

    fun close() {
        try { ws?.close(1000, "bye") } catch (_: Exception) {}
        ws = null
    }
}
