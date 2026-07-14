import android.content.Context
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import java.time.format.DateTimeFormatter

@Composable
fun NotificationCard(notification: Notification) {
    val context = LocalContext.current
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Text(
            text = notification.title,
            style = MaterialTheme.typography.titleLarge
        )
        Text(
            text = notification.message,
            style = MaterialTheme.typography.bodyMedium
        )
        Text(
            text = "Atualizado em: ${notification.updatedAt.format(DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm"))}",
            style = MaterialTheme.typography.bodySmall
        )
    }
}

data class Notification(
    val id: Int,
    val title: String,
    val message: String,
    val updatedAt: java.time.LocalDateTime
)

@Preview
@Composable
fun PreviewNotificationCard() {
    val notification = Notification(
        id = 1,
        title = "Título da notificação",
        message = "Mensagem da notificação",
        updatedAt = java.time.LocalDateTime.now()
    )
    NotificationCard(notification = notification)
}