package com.nexusai.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.app.NotificationCompat
import com.nexusai.app.NexusApplication
import com.nexusai.app.util.NexusWebSocket
import com.nexusai.app.util.VoiceManager

/**
 * Serviço em primeiro plano que mantém a NEXUS "sempre ouvindo" para a wake word "Nexus".
 *
 * Fluxo:
 *  1. Escuta continuamente (modo WAKE) procurando "nexus" nas respostas parciais.
 *  2. Ao detectar, fala "Pronto" e captura o comando (modo COMMAND).
 *  3. Comandos de controle do celular são tratados localmente (NexusController);
 *     os demais vão ao backend via WebSocket e a resposta é falada (TTS).
 *  4. Volta ao modo WAKE.
 *
 * Tudo roda no aparelho até o envio do comando; nada sai do dispositivo além do
 * próprio backend.
 */
class NexusVoiceService : Service() {

    private lateinit var recognizer: SpeechRecognizer
    private lateinit var voice: VoiceManager
    private var ws: NexusWebSocket? = null
    private val mainHandler = Handler(Looper.getMainLooper())

    private var mode = Mode.WAKE
    private var capturing = false
    private var listening = false
    private var conversationId: Int? = null
    private var pendingCommand: String? = null
    private val response = StringBuilder()

    private enum class Mode { WAKE, COMMAND }

    companion object {
        const val ACTION_STOP = "com.nexusai.app.ACTION_STOP_VOICE"
        private const val CHANNEL_ID = "nexus_voice"
        private const val NOTIF_ID = 1

        fun start(context: Context) {
            context.startForegroundService(Intent(context, NexusVoiceService::class.java))
        }

        fun stop(context: Context) {
            context.sendBroadcast(Intent(ACTION_STOP).setPackage(context.packageName))
        }
    }

    private val stopReceiver = object : BroadcastReceiver() {
        override fun onReceive(c: Context?, i: Intent?) {
            if (i?.action == ACTION_STOP) stopSelf()
        }
    }

    override fun onCreate() {
        super.onCreate()
        voice = VoiceManager(this)
        voice.initTts()
        registerReceiver(stopReceiver, IntentFilter(ACTION_STOP))
        createChannel()
        startForeground(NOTIF_ID, buildNotification())
        mainHandler.post { initRecognizer() }
    }

    private fun createChannel() {
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "JARVIS Assistente", NotificationManager.IMPORTANCE_LOW)
        )
    }

    private fun buildNotification() = NotificationCompat.Builder(this, CHANNEL_ID)
        .setContentTitle("JARVIS ativo")
        .setContentText("Diga \"Jarvis\" para falar comigo")
        .setSmallIcon(android.R.drawable.ic_btn_speak_now)
        .setOngoing(true)
        .addAction(
            android.R.drawable.ic_menu_close_clear_cancel,
            "Parar",
            PendingIntent.getBroadcast(
                this, 0,
                Intent(ACTION_STOP).setPackage(packageName),
                PendingIntent.FLAG_IMMUTABLE
            )
        )
        .build()

    private fun initRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            voice.speak("Reconhecimento de voz indisponível neste aparelho.")
            stopSelf()
            return
        }
        recognizer = VoiceManager.createRecognizer(this, listener)
        recognizer.setRecognitionListener(listener)
        startWakeListening()
    }

    private fun startWakeListening() {
        mode = Mode.WAKE
        capturing = false
        listening = true
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            // Mantém o microfone aberto um pouco mais entre pausas (menos falhas).
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1500)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1000)
        }
        try {
            recognizer.startListening(intent)
        } catch (e: Exception) {
            scheduleRestart()
        }
    }

    private fun startCommandListening() {
        mode = Mode.COMMAND
        capturing = false
        listening = true
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, false)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PROMPT, "Diga seu comando")
        }
        try {
            recognizer.startListening(intent)
        } catch (e: Exception) {
            scheduleRestart()
        }
    }

    private fun scheduleRestart(delayMs: Long = 1200) {
        listening = false
        mainHandler.removeCallbacks(restartRunnable)
        mainHandler.postDelayed(restartRunnable, delayMs)
    }

    private val restartRunnable = Runnable { startWakeListening() }

    private val listener = object : RecognitionListener {
        override fun onResults(bundle: Bundle?) {
            val text = bundle?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull().orEmpty()
            handleResult(text)
        }

        override fun onPartialResults(bundle: Bundle?) {
            if (mode == Mode.WAKE && !capturing) {
                val text = bundle?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull().orEmpty()
                if (containsWakeWord(text)) onWakeDetected()
            }
        }

        override fun onError(error: Int) {
            scheduleRestart()
        }

        override fun onReadyForSpeech(bundle: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onEndOfSpeech() {}
        override fun onRmsChanged(r: Float) {}
        override fun onBufferReceived(bytes: ByteArray?) {}
        override fun onEvent(i: Int, bundle: Bundle?) {}
    }

    private fun containsWakeWord(text: String): Boolean {
        val t = text.lowercase()
        // Wake word principal: "jarvis". "nexus" fica como reserva (nome do sistema).
        return t.contains("jarvis") || t.contains("jarvís") || t.contains("jarvi") ||
               t.contains("nexus") || t.contains("néxus")
    }

    private fun onWakeDetected() {
        if (capturing) return
        capturing = true
        try { recognizer.stopListening() } catch (_: Exception) {}
        listening = false
        voice.applyJarvisVoice()
        voice.speak("Às ordens.")
        mainHandler.postDelayed({ startCommandListening() }, 700)
    }

    private fun handleResult(text: String) {
        // Ignora o "onResults" final que surge ao parar o reconhecimento durante
        // a detecção da wake word (evita reiniciar antes de capturar o comando).
        if (mode == Mode.WAKE && capturing) return
        val trimmed = text.trim()
        if (mode == Mode.WAKE) {
            if (containsWakeWord(trimmed)) onWakeDetected()
            else scheduleRestart()
        } else {
            if (trimmed.isEmpty()) {
                startWakeListening()
                return
            }
            // Comando local (controle do celular) tem prioridade sobre o backend.
            if (NexusController.tryHandleLocal(this, trimmed, voice)) {
                startWakeListening()
                return
            }
            sendToBackend(trimmed)
        }
    }

    private fun sendToBackend(command: String) {
        val app = application as NexusApplication
        val token = app.tokenStore.getToken()
        if (token.isNullOrBlank()) {
            voice.speak("Você precisa fazer login no app NEXUS primeiro.")
            startWakeListening()
            return
        }
        pendingCommand = command
        ensureWs(token, app.tokenStore.getServerUrl())
    }

    private fun ensureWs(token: String, baseUrl: String) {
        if (ws == null) {
            ws = NexusWebSocket(
                baseUrl = baseUrl,
                token = token,
                onDelta = { response.append(it) },
                onDone = { cid ->
                    if (cid > 0) conversationId = cid
                    val reply = response.toString().trim()
                    if (reply.isNotEmpty()) voice.speak(reply)
                    startWakeListening()
                },
                onError = { err ->
                    ws = null
                    voice.speak("Erro: $err")
                    startWakeListening()
                },
                onOpen = {
                    val cmd = pendingCommand
                    if (cmd != null) {
                        pendingCommand = null
                        ws?.send(cmd, conversationId)
                    }
                }
            )
            ws?.connect()
        } else if (pendingCommand != null) {
            val cmd = pendingCommand
            pendingCommand = null
            if (cmd != null) ws?.send(cmd, conversationId)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onDestroy() {
        super.onDestroy()
        try { unregisterReceiver(stopReceiver) } catch (_: Exception) {}
        try { recognizer.destroy() } catch (_: Exception) {}
        ws?.close()
        voice.shutdown()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
