import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.MaterialTheme
import androidx.compose.material.Surface
import androidx.compose.ui.Modifier
import com.pedrog1906g.jarvis.ui.theme.JarvisTheme

class MainActivity : ComponentActivity() {
    private lateinit var speechRecognizer: SpeechRecognizer

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this)
        val listener = object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                // Não necessário
            }

            override fun onBeginningOfSpeech() {
                // Não necessário
            }

            override fun onRmsChanged(rmsdB: Float) {
                // Não necessário
            }

            override fun onBufferReceived(buffer: ByteArray?) {
                // Não necessário
            }

            override fun onEndOfSpeech() {
                // Não necessário
            }

            override fun onError(errorCode: Int) {
                // Não necessário
            }

            override fun onResults(results: Bundle?) {
                val texto = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)?.get(0)
                if (texto != null && texto.contains("Jarvis")) {
                    // Responder quando chamado
                    resposta("Olá, estou aqui!")
                }
                if (texto != null && texto.contains("tocar música")) {
                    // Tocar música
                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://www.youtube.com/results?search_query=música+aleatória"))
                    startActivity(intent)
                }
            }

            override fun onPartialResults(partialResults: Bundle?) {
                // Não necessário
            }

            override fun onEvent(eventType: Int, params: Bundle?) {
                // Não necessário
            }
        }
        speechRecognizer.setRecognitionListener(listener)

        setContent {
            JarvisTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colors.background
                ) {
                    // Interface do usuário
                }
            }
        }
    }

    private fun resposta(resposta: String) {
        // Implementar resposta
    }
}