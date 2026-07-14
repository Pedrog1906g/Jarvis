import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.MaterialTheme
import androidx.compose.material.Surface
import androidx.compose.ui.Modifier
import com.pedrog1906g.jarvis.ui.theme.JarvisTheme
import java.util.*

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            JarvisTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    // Aqui você pode adicionar o código para alterar a voz
                    val texto = "Olá, eu sou o Jarvis!"
                    val voz = android.speech.tts.TextToSpeech(this@MainActivity, android.speech.tts.TextToSpeech.OnInitListener {
                        if (it == android.speech.tts.TextToSpeech.SUCCESS) {
                            val tts = android.speech.tts.TextToSpeech(this@MainActivity, android.speech.tts.TextToSpeech.OnInitListener {
                                tts.setSpeechRate(0.8f) // Taxa de fala
                                tts.setPitch(0.8f) // Tom da voz
                                tts.speak(texto, android.speech.tts.TextToSpeech.QUEUE_FLUSH, null, null)
                            })
                        }
                    })
                }
            }
        }
    }
}