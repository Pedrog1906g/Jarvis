package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.AuthViewModel
import com.nexusai.app.viewmodel.SettingsViewModel

@Composable
fun SettingsScreen(authVm: AuthViewModel) {
    val vm: SettingsViewModel = viewModel()
    var server by remember { mutableStateOf(vm.serverUrl.value) }

    LaunchedEffect(Unit) { vm.loadInfo() }

    Column(Modifier.fillMaxSize().background(NexusBackground).padding(16.dp)) {
        Text("Ajustes", style = MaterialTheme.typography.titleLarge, color = NexusText)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(value = server, onValueChange = { server = it },
            label = { Text("URL do servidor") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        Button(onClick = { vm.saveServer(server) }) { Text("Salvar servidor") }
        if (vm.saved.value) Text("Servidor salvo. Reinicie o app para reconectar.", color = NexusPrimary)

        Spacer(Modifier.height(16.dp))
        vm.info.value?.let { info ->
            Text("Versão: ${info.version}", color = NexusText)
            Text("LLM disponível: ${if (info.llmAvailable) "sim" else "não (modo demo)"}", color = NexusText)
            Text("Usuário: ${info.user.displayName}", color = NexusTextDim)
            Spacer(Modifier.height(8.dp))
            Text("Novidades (changelog):", color = NexusPrimary)
            Text(info.changelog.take(2500), color = NexusTextDim,
                style = MaterialTheme.typography.bodySmall)
        }
        if (vm.error.value != null) Text(vm.error.value ?: "", color = NexusDanger)

        Spacer(Modifier.weight(1f))
        Button(onClick = { authVm.logout() },
            colors = ButtonDefaults.buttonColors(containerColor = NexusDanger)) {
            Text("Sair / Desconectar")
        }
    }
}
