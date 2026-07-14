package com.nexusai.app.ui.component

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.nexusai.app.data.model.ChatMessage
import com.nexusai.app.ui.theme.*

@Composable
fun MessageBubble(message: ChatMessage, onSpeak: (String) -> Unit = {}) {
    val isUser = message.role == "user"
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(0.85f)
                .clip(RoundedCornerShape(12.dp))
                .background(if (isUser) NexusUserBubble else NexusBotBubble)
                .padding(12.dp)
        ) {
            Text(
                text = if (isUser) "Você" else "NEXUS",
                style = MaterialTheme.typography.labelSmall,
                color = if (isUser) NexusPrimary else NexusAccent
            )
            Spacer(Modifier.height(4.dp))
            Text(text = message.content.ifEmpty { "…" }, color = NexusText)
            if (!isUser && message.content.isNotEmpty()) {
                Spacer(Modifier.height(4.dp))
                TextButton(onClick = { onSpeak(message.content) }) {
                    Text("🔊 Ouvir", color = NexusPrimary)
                }
            }
        }
    }
}
