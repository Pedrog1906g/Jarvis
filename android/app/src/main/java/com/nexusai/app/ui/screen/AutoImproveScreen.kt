package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.AutoImproveViewModel

@Composable
fun AutoImproveScreen() {
    val vm: AutoImproveViewModel = viewModel()
    LaunchedEffect(Unit) { vm.loadStatus() }

    Column(
        Modifier.fillMaxSize().background(NexusBackground).padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text("Auto-melhoria de Código", style = MaterialTheme.typography.titleLarge, color = NexusText)
        Spacer(Modifier.height(8.dp))
        Text(
            "A NEXUS pode melhorar o próprio código sozinha. Toda mudança faz um BACKUP " +
                "automático e, se o build quebrar, ela reverte sozinha. Você também pode pedir " +
                "por voz: \"NEXUS, auto melhore\".",
            color = NexusTextDim, style = MaterialTheme.typography.bodySmall
        )

        Spacer(Modifier.height(12.dp))
        Text(
            "Token do GitHub: ${if (vm.tokenConfigured.value) "configurado (${vm.tokenSource.value})" else "NÃO configurado"}",
            color = if (vm.tokenConfigured.value) NexusPrimary else NexusDanger
        )

        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = vm.tokenInput.value, onValueChange = { vm.tokenInput.value = it },
            label = { Text("Cole seu token do GitHub (fine-grained, permissão contents:write)") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { vm.saveToken() }) { Text("Salvar token com segurança") }

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = vm.improveRequest.value, onValueChange = { vm.improveRequest.value = it },
            label = { Text("O que melhorar? (ex: deixe a tela de chat mais bonita)") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { vm.requestImprove() }) { Text("Pedir auto-melhoria") }

        Spacer(Modifier.height(12.dp))
        Button(onClick = { vm.pollStatus() }) { Text("Atualizar status") }

        Spacer(Modifier.height(12.dp))
        if (vm.statusText.value.isNotEmpty()) {
            Text("Status:", color = NexusPrimary)
            Text(vm.statusText.value, color = NexusText, style = MaterialTheme.typography.bodySmall)
        }
        if (vm.message.value.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text(vm.message.value, color = NexusTextDim, style = MaterialTheme.typography.bodySmall)
        }
    }
}
