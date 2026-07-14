package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.ChatMessage
import com.nexusai.app.data.model.ConversationSummary
import com.nexusai.app.data.model.MessageDto
import com.nexusai.app.ui.component.MessageBubble
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.ChatViewModel
import kotlinx.coroutines.launch

@Composable
fun HistoryScreen() {
    val vm: ChatViewModel = viewModel()
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val repo = (ctx.applicationContext as NexusApplication).repository

    var convs by remember { mutableStateOf<List<ConversationSummary>>(emptyList()) }
    var selected by remember { mutableStateOf<Int?>(null) }
    var msgs by remember { mutableStateOf<List<MessageDto>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        loading = true
        try { convs = repo.conversations() } catch (_: Exception) {}
        loading = false
    }

    Column(Modifier.fillMaxSize().background(NexusBackground).padding(12.dp)) {
        if (selected == null) {
            Text("Conversas", style = MaterialTheme.typography.titleLarge, color = NexusText)
            Spacer(Modifier.height(8.dp))
            if (loading) CircularProgressIndicator(color = NexusPrimary)
            LazyColumn {
                items(convs) { c ->
                    Card(
                        Modifier.fillMaxWidth().padding(4.dp)
                            .clickable { selected = c.id },
                        colors = CardDefaults.cardColors(containerColor = NexusSurface)
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(c.title, color = NexusText)
                            Text(c.preview, color = NexusTextDim,
                                style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }
        } else {
            LaunchedEffect(selected) {
                try { msgs = repo.messages(selected!!) } catch (_: Exception) {}
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(onClick = { selected = null; msgs = emptyList() }) {
                    Icon(androidx.compose.material.icons.Icons.Filled.ArrowBack,
                        contentDescription = "Voltar", tint = NexusPrimary)
                }
                Text("Mensagens", color = NexusText)
            }
            LazyColumn(Modifier.weight(1f)) {
                items(msgs) { m ->
                    MessageBubble(ChatMessage(id = m.id.toString(), role = m.role, content = m.content))
                }
            }
            Button(onClick = { vm.loadConversation(selected!!); selected = null },
                modifier = Modifier.fillMaxWidth()) {
                Text("Abrir nesta conversa")
            }
        }
    }
}
