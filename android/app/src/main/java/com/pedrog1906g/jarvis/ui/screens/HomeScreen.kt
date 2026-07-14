import android.util.Log
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.pedrog1906g.jarvis.data.model.Item
import com.pedrog1906g.jarvis.ui.theme.JarvisTheme

@Composable
fun HomeScreen(
    items: List<Item>,
    onItemClicked: (Item) -> Unit,
    onButtonClicked: () -> Unit
) {
    JarvisTheme {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "Bem-vindo ao Jarvis",
                style = MaterialTheme.typography.headlineMedium
            )
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(items) { item ->
                    ItemCard(
                        item = item,
                        onClick = { onItemClicked(item) }
                    )
                }
            }
            Button(
                onClick = onButtonClicked,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            ) {
                Text(text = "Clique aqui")
            }
        }
    }
}

@Composable
fun ItemCard(
    item: Item,
    onClick: () -> Unit
) {
    androidx.compose.material3.Card(
        modifier = Modifier
            .fillMaxWidth()
            .height(50.dp),
        onClick = onClick
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = item.name,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    HomeScreen(
        items = listOf(
            Item("Item 1"),
            Item("Item 2"),
            Item("Item 3")
        ),
        onItemClicked = { item -> Log.d("Item", item.name) },
        onButtonClicked = { Log.d("Button", "Clicado") }
    )
}