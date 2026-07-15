package com.nexusai.app.util

import android.content.ComponentName
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
 * Gerencia STT (Reconhecedor de Fala) e TTS (TextToSpeech nativo).
 * Aplica a "voz do JARVIS": seleciona uma voz masculina e deixa o tom mais
 * grave/calmo. O reconhecimento usa o serviço de voz correto do aparelho
 * (ex.: Google) — essencial em Android 12+ onde o padrão pode falhar.
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
    var rate: Float = prefs.getFloat("rate", 0.95f)
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

    /**
     * Seleciona a voz mais "humana" disponível: prioriza qualidade alta/neural,
     * idioma pt-BR e timbre masculino (estilo JARVIS). O tom grave é ajustado
     * via pitch/rate salvos nas preferências.
     */
    fun applyJarvisVoice() {
        val t = tts ?: return
        t.setPitch(pitch)
        t.setSpeechRate(rate)
        try {
            val voices = t.voices ?: return
            fun score(v: Voice): Int {
                var s = when (v.quality) {
                    Voice.QUALITY_VERY_HIGH -> 140
                    Voice.QUALITY_HIGH -> 90
                    Voice.QUALITY_NORMAL -> 45
                    Voice.QUALITY_LOW -> 15
                    else -> 25
                }
                if (v.locale.language == "pt" && v.locale.country == "BR") s += 70
                else if (v.locale.language == "pt") s += 30
                if (v.name.contains("Male", true) || v.name.contains("Masculino", true)
                        || v.name.contains("Ricardo", true)) s += 40
                if (v.features.contains("network")) s += 20 // vozes online/neurais soam mais naturais
                return s
            }
            val best = voices
                .filter { !it.features.contains("notInstalled") }
                .maxByOrNull { score(it) }
            best?.let { t.voice = it }
        } catch (_: Exception) {
            // Mantém o pitch grave se não conseguir selecionar uma voz específica.
        }
    }

    fun speak(text: String) {
        val clean = text.replace(Regex("\\*\\*|\\*|`|#"), "").trim()
        if (clean.isEmpty()) return
        val t = tts ?: return
        // Fala frase a frase (QUEUE_ADD) para um ritmo mais natural e sem cortar
        // respostas longas. Pausas automáticas entre frases deixam a fala mais humana.
        val parts = clean.split(Regex("(?<=[.!?…:])\\s+"))
        parts.forEachIndexed { i, part ->
            if (part.isBlank()) return@forEachIndexed
            val mode = if (i == 0) TextToSpeech.QUEUE_FLUSH else TextToSpeech.QUEUE_ADD
            t.speak(part, mode, Bundle(), "jarvis_${System.currentTimeMillis()}_$i")
        }
    }

    fun startListening(onPartial: (String) -> Unit = {}, onResult: (String) -> Unit, onError: (Int) -> Unit) {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            onError(ERROR_ENGINE)
            return
        }
        recognizer?.destroy()
        recognizer = createRecognizer(context, object : RecognitionListener {
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
                onError(e)
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

    companion object {
        const val ERROR_ENGINE = 99

        /** Cria o reconhecedor apontando para o serviço de voz disponível (Google, etc.). */
        fun createRecognizer(context: Context, listener: RecognitionListener): SpeechRecognizer {
            return try {
                val query = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                val infos = context.packageManager.queryIntentServices(query, 0)
                val comp = if (infos.isNotEmpty()) {
                    val ri = infos[0]
                    ComponentName(ri.serviceInfo.packageName, ri.serviceInfo.name)
                } else null
                if (comp != null) SpeechRecognizer.createSpeechRecognizer(context, comp)
                else SpeechRecognizer.createSpeechRecognizer(context)
            } catch (_: Exception) {
                SpeechRecognizer.createSpeechRecognizer(context)
            }
        }
    }
}

/** Traduz o código de erro do STT para uma mensagem amigável (sem códigos crípticos). */
fun sttErrorMessage(code: Int): String = when (code) {
    1 -> "Sem internet para o reconhecimento de voz."
    2 -> "Conexão lenta. Tente de novo."
    3 -> "Erro de áudio do microfone."
    4 -> "Serviço de voz indisponível agora. Tente depois."
    5 -> "Erro no app de voz. Reinicie o app."
    6 -> "Não ouvi nada. Fale mais perto do microfone."
    7 -> "Não entendi. Fale de novo, mais claro."
    8 -> "Reconhecedor ocupado. Aguarde um instante."
    9 -> "Permissão de microfone negada. Habilite em Ajustes."
    VoiceManager.Companion.ERROR_ENGINE -> "Reconhecimento de voz indisponível neste aparelho."
    else -> "Não consegui entender o áudio."
}
