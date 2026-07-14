package com.nexusai.app.util

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.speech.tts.TextToSpeech
import android.speech.tts.Voice
import java.util.Locale

/**
 * Gerencia STT (Reconhecedor de Fala do Android) e TTS (TextToSpeech nativo).
 * Aplica a "voz do JARVIS": seleciona uma voz masculina disponível e deixa o
 * tom mais grave/calmo (pitch mais baixo). Funciona offline/online conforme o
 * motor de voz do aparelho.
 */
class VoiceManager(private val context: Context) {

    private var recognizer: SpeechRecognizer? = null
    var tts: TextToSpeech? = null
    var isListening = false

    // Ajustes de voz persistidos (compartilhados entre as instâncias).
    private val prefs = context.getSharedPreferences("jarvis_voice", Context.MODE_PRIVATE)
    var pitch: Float = prefs.getFloat("pitch", 0.82f)
        set(value) {
            field = value.coerceIn(0.5f, 1.5f)
            prefs.edit().putFloat("pitch", field).apply()
            tts?.setPitch(field)
        }
    var rate: Float = prefs.getFloat("rate", 0.98f)
        set(value) {
            field = value.coerceIn(0.5f, 2.0f)
            prefs.edit().putFloat("rate", field).apply()
            tts?.setSpeechRate(field)
        }

    fun initTts(onReady: () -> Unit = {}) {
        if (tts == null) {
            tts = TextToSpeech(context) { status ->
                if (status == TextToSpeech.SUCCESS) {
                    tts?.language = Locale("pt", "BR")
                    applyJarvisVoice()
                    onReady()
                }
            }
        } else {
            applyJarvisVoice()
            onReady()
        }
    }

    /** Tenta selecionar uma voz masculina e deixa o tom grave (estilo JARVIS). */
    fun applyJarvisVoice() {
        val t = tts ?: return
        t.setPitch(pitch)
        t.setSpeechRate(rate)
        try {
            val voices = t.voices ?: return
            // Prioridade: pt-BR masculina -> en-US masculina -> qualquer masculina
            // -> pt-BR qualquer -> primeira disponível.
            val male = voices.filter {
                it.name.contains("Male", true) || it.name.contains("Masculino", true)
                        || it.name.contains("Ricardo", true) || it.name.contains("Google", true)
            }
            val chosen = male.firstOrNull { it.locale.language == "pt" && it.locale.country == "BR" }
                ?: male.firstOrNull { it.locale.language == "en" }
                ?: male.firstOrNull()
                ?: voices.firstOrNull { it.locale.language == "pt" && it.locale.country == "BR" }
                ?: voices.firstOrNull()
            chosen?.let { t.voice = it }
        } catch (_: Exception) {
            // Sem voz específica: o pitch baixo já deixa o tom mais grave.
        }
    }

    fun speak(text: String) {
        val clean = text.replace(Regex("\\*\\*|\\*|`|#"), "").trim()
        if (clean.isNotEmpty()) {
            val params = Bundle()
            tts?.speak(clean, TextToSpeech.QUEUE_FLUSH, params, "jarvis_${System.currentTimeMillis()}")
        }
    }

    fun startListening(onPartial: (String) -> Unit = {}, onResult: (String) -> Unit, onError: (String) -> Unit) {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            onError("Reconhecimento de voz indisponível neste aparelho")
            return
        }
        recognizer?.destroy()
        recognizer = SpeechRecognizer.createSpeechRecognizer(context)
        recognizer?.setRecognitionListener(object : RecognitionListener {
            override fun onResults(b: Bundle) {
                val matches = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                onResult(matches?.firstOrNull() ?: "")
                isListening = false
            }
            override fun onPartialResults(b: Bundle) {
                val matches = b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                matches?.firstOrNull()?.let { onPartial(it) }
            }
            override fun onError(e: Int) {
                isListening = false
                onError("Erro STT: $e")
            }
            override fun onReadyForSpeech(p: Bundle) {}
            override fun onBeginningOfSpeech() {}
            override fun onEndOfSpeech() {}
            override fun onRmsChanged(r: Float) {}
            override fun onBufferReceived(b: ByteArray) {}
            override fun onEvent(i: Int, b: Bundle) {}
        })
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "pt-BR")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        isListening = true
        recognizer?.startListening(intent)
    }

    fun stopListening() {
        recognizer?.stopListening()
        isListening = false
    }

    fun shutdown() {
        recognizer?.destroy()
        recognizer = null
        tts?.shutdown()
        tts = null
    }
}
