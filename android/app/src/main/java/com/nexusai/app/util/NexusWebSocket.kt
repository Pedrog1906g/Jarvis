package com.nexusai.app.util

import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Cliente WebSocket para chat em streaming com o backend NEXUS.
 * O backend envia: {type:"start"}, {type:"delta", content}, {type:"done", conversation_id}.
 */
/**
 * Payload de lembrete recebido via push do servidor.
 * Corresponde ao evento WS {type:"reminder", id, title, note, due_at}.
 */
data class ReminderPush(val id: Int, val title: String, val note: String, val dueAt: String)

class NexusWebSocket(
    private val baseUrl: String,
    private val token: String,
    private val onDelta: (String) -> Unit,
    private val onDone: (Int) -> Unit,
    private val onError: (String) -> Unit,
    private val onOpen: () -> Unit = {},
    /** Chamado quando o servidor envia um lembrete via push (tipo "reminder"). */
    private val onReminder: (ReminderPush) -> Unit = {}
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
                    when (json.optString("type")) {
                        "delta"    -> onDelta(json.getString("content"))
                        "done"     -> onDone(json.optInt("conversation_id", -1))
                        "error"    -> onError(json.optString("message", "erro"))
                        "reminder" -> onReminder(
                            ReminderPush(
                                id     = json.optInt("id", -1),
                                title  = json.optString("title", "Lembrete"),
                                note   = json.optString("note", ""),
                                dueAt  = json.optString("due_at", "")
                            )
                        )
                        // Outros tipos de push (futuro): ignorados silenciosamente
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
