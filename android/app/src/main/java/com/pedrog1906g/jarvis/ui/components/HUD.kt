import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp

@Composable
fun HUD() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "HUD",
            style = MaterialTheme.typography.titleLarge,
            color = Color(0xFF7A288A) // Cor roxa
        )
        // Outros componentes do HUD...
    }
}

@Preview
@Composable
fun PreviewHUD() {
    HUD()
}
