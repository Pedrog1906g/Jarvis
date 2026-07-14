package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.ControlViewModel

@Composable
fun ControlScreen() {
    val vm: ControlViewModel = viewModel()
    val ctx = LocalContext.current
    var clickTarget by remember { mutableStateOf("") }
    var notifSummary by remember { mutableStateOf("") }

    LaunchedEffect(Unit) { vm.refresh(ctx) }

    Column(
        Modifier.fillMaxSize().background(NexusBackground).padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Text("Controle do Celular", style = MaterialTheme.typography.titleLarge, color = NexusText)
        Spacer(Modifier.height(8.dp))
        Text(
            "Recursos locais. Você ativa manualmente nas configurações do Android. " +
                "Nada sai do aparelho além do seu comando ao backend.",
            color = NexusTextDim, style = MaterialTheme.typography.bodySmall
        )

        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Acessibilidade (ler tela / tocar)", color = NexusText)
                Text(
                    if (vm.accessibilityEnabled.value) "ATIVO" else "DESATIVADO",
                    color = if (vm.accessibilityEnabled.value) NexusPrimary else NexusDanger,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Button(onClick = { vm.openAccessibilitySettings(ctx) }) { Text("Ativar") }
        }

        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Leitor de Notificações", color = NexusText)
                Text(
                    if (vm.notificationEnabled.value) "ATIVO" else "DESATIVADO",
                    color = if (vm.notificationEnabled.value) NexusPrimary else NexusDanger,
                    style = MaterialTheme.typography.bodySmall
                )
            }
            Button(onClick = { vm.openNotificationSettings(ctx) }) { Text("Ativar") }
        }

        Spacer(Modifier.height(8.dp))
        Button(onClick = { vm.refresh(ctx) }) { Text("Atualizar status") }

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))
        Text("Testar agora (com o app em primeiro plano):", color = NexusPrimary)

        Button(onClick = { vm.readScreen() }) { Text("Ler tela atual") }
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = clickTarget, onValueChange = { clickTarget = it },
            label = { Text("Texto para tocar na tela") }, modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { if (clickTarget.isNotBlank()) vm.click(clickTarget) }) {
            Text("Tocar no texto")
        }
        Spacer(Modifier.height(8.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { vm.scroll("up") }) { Text("Rolar ↑") }
            Button(onClick = { vm.scroll("down") }) { Text("Rolar ↓") }
        }
        Spacer(Modifier.height(8.dp))
        Button(onClick = { notifSummary = vm.notificationsSummary() }) {
            Text("Ver notificações recentes")
        }

        Spacer(Modifier.height(8.dp))
        if (vm.status.value.isNotEmpty()) Text(vm.status.value, color = NexusText)
        if (vm.screenText.value.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text("Tela:", color = NexusPrimary)
            Text(vm.screenText.value, color = NexusTextDim, style = MaterialTheme.typography.bodySmall)
        }
        if (notifSummary.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text("Notificações:", color = NexusPrimary)
            Text(notifSummary, color = NexusTextDim, style = MaterialTheme.typography.bodySmall)
        }
    }
}
