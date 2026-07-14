import android.util.Log
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.pedrog1906g.jarvis.data.model.Item

@Composable
fun HomeScreen(
    items: List<Item>,
    onItemClicked: (Item) -> Unit,
    onAddItemClicked: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            text = "Jarvis",
            style = MaterialTheme.typography.headlineLarge
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = onAddItemClicked) {
            Text("Adicionar Item")
        }
        Spacer(modifier = Modifier.height(16.dp))
        LazyColumn(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        ) {
            items(items = items) { item ->
                ItemCard(
                    item = item,
                    onItemClicked = { onItemClicked(item) }
                )
            }
        }
    }
}

@Composable
fun ItemCard(
    item: Item,
    onItemClicked: () -> Unit
) {
    androidx.compose.material3.Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        onClick = onItemClicked
    ) {
        Column(
            modifier = Modifier
                .padding(16.dp)
                .fillMaxWidth()
        ) {
            Text(
                text = item.name,
                style = MaterialTheme.typography.bodyLarge
            )
            Text(
                text = item.description,
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

@Preview
@Composable
fun HomeScreenPreview() {
    HomeScreen(
        items = listOf(
            Item("Item 1", "Descrição do item 1"),
            Item("Item 2", "Descrição do item 2")
        ),
        onItemClicked = { item -> Log.d("HomeScreen", "Item clicado: ${item.name}") },
        onAddItemClicked = { Log.d("HomeScreen", "Botão adicionar item clicado") }
    )
}