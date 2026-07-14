package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.PluginState
import com.nexusai.app.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun DevicesScreen() {
    val ctx = LocalContext.current
    val scope = rememberCoroutineScope()
    val repo = (ctx.applicationContext as NexusApplication).repository

    var plugins by remember { mutableStateOf<List<PluginState>>(emptyList()) }
    var command by remember { mutableStateOf("") }
    var result by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        try { plugins = repo.plugins() } catch (e: Exception) { result = e.localizedMessage ?: "" }
    }

    Column(Modifier.fillMaxSize().background(NexusBackground).padding(16.dp)) {
        Text("Dispositivos & Plugins", style = MaterialTheme.typography.titleLarge, color = NexusText)
        Spacer(Modifier.height(8.dp))
        plugins.forEach { p ->
            Text("• ${p.name} : ${if (p.enabled) "ativo" else "inativo"}", color = NexusTextDim)
        }
        Spacer(Modifier.height(16.dp))

        OutlinedTextField(
            value = command, onValueChange = { command = it },
            label = { Text("Comando (ex: abrir Spotify / tocar música / aumentar volume)") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                scope.launch { try { val r = repo.system(command); result = r.toString() } catch (e: Exception) { result = e.localizedMessage ?: "" } }
            }) { Text("Sistema") }
            Button(onClick = {
                scope.launch { try { val r = repo.spotify(command); result = r.toString() } catch (e: Exception) { result = e.localizedMessage ?: "" } }
            }) { Text("Spotify") }
        }
        Spacer(Modifier.height(12.dp))
        if (result.isNotEmpty()) {
            Text("Resposta:", color = NexusPrimary)
            Text(result, color = NexusTextDim, style = MaterialTheme.typography.bodySmall)
        }
    }
}
