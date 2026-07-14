import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.pedrog1906.jarvis.ui.theme.JarvisTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            JarvisTheme {
                // Adicionei uma mensagem de boas-vindas
                android.widget.Toast.makeText(this, "Bem-vindo ao Jarvis!", android.widget.Toast.LENGTH_SHORT).show()
            }
        }
    }
}