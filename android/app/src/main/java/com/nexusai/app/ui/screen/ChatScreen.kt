package com.nexusai.app.ui.screen

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.component.MessageBubble
import com.nexusai.app.ui.theme.*
import com.nexusai.app.util.VoiceManager
import com.nexusai.app.viewmodel.ChatViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen() {
    val vm: ChatViewModel = viewModel()
    val scope = rememberCoroutineScope()
    val listState = rememberLazyListState()
    val voice = vm.getVoice()

    val messages by vm.messages.collectAsState()
    val isThinking by vm.isThinking.collectAsState()
    val error by vm.error.collectAsState()

    var input by remember { mutableStateOf("") }
    var listening by remember { mutableStateOf(false) }
    var partial by remember { mutableStateOf("") }
    var micGranted by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted -> micGranted = granted }

    DisposableEffect(Unit) {
        vm.ensureConnected()
        onDispose { }
    }

    LaunchedEffect(messages.size, isThinking) {
        if (messages.isNotEmpty()) listState.animateScrollToItem(messages.lastIndex)
    }

    Column(Modifier.fillMaxSize().background(NexusBackground)) {
        LazyColumn(
            state = listState,
            modifier = Modifier.weight(1f).fillMaxWidth().padding(horizontal = 8.dp),
            contentPadding = PaddingValues(vertical = 8.dp)
        ) {
            items(messages, key = { it.id }) { msg ->
                MessageBubble(msg, onSpeak = { voice.speak(it) })
            }
            if (isThinking) {
                item {
                    Text("JARVIS está pensando…", color = NexusTextDim,
                        modifier = Modifier.padding(12.dp))
                }
            }
        }

        if (error != null) {
            Text(error ?: "", color = NexusDanger, modifier = Modifier.padding(8.dp))
        }

        Row(Modifier.fillMaxWidth().padding(8.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = {
                if (!micGranted) { permissionLauncher.launch(Manifest.permission.RECORD_AUDIO); return@IconButton }
                if (listening) { voice.stopListening(); listening = false }
                else {
                    listening = true
                    voice.startListening(
                        onPartial = { partial = it; input = it },
                        onResult = { text ->
                            listening = false; partial = ""
                            if (text.isNotBlank()) { vm.send(text); input = "" }
                        },
                        onError = { listening = false; vm.reportError(it) }
                    )
                }
            }) {
                Icon(
                    Icons.Filled.Mic,
                    contentDescription = "Falar",
                    tint = if (listening) NexusDanger else NexusPrimary
                )
            }

            OutlinedTextField(
                value = if (listening) partial else input,
                onValueChange = { input = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Fale ou escreva…") },
                maxLines = 4
            )

            IconButton(onClick = {
                if (input.isNotBlank()) { vm.send(input); input = "" }
            }) {
                Icon(Icons.Filled.Send,
                    contentDescription = "Enviar", tint = NexusPrimary)
            }
        }
    }
}
