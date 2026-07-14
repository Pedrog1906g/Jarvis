package com.nexusai.app.ui.screen

import android.Manifest
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.AuthViewModel
import com.nexusai.app.viewmodel.SettingsViewModel

@Composable
fun SettingsScreen(authVm: AuthViewModel) {
    val vm: SettingsViewModel = viewModel()
    val ctx = LocalContext.current
    var server by remember { mutableStateOf(vm.serverUrl.value) }

    val micLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) vm.toggleWakeWord(ctx, true) else vm.error.value = "Permissão de microfone necessária para o assistente por voz."
    }

    LaunchedEffect(Unit) { vm.loadInfo(); vm.loadWakeWord() }

    Column(Modifier.fillMaxSize().background(NexusBackground).padding(16.dp)) {
        Text("Ajustes", style = MaterialTheme.typography.titleLarge, color = NexusText)
        Spacer(Modifier.height(12.dp))

        OutlinedTextField(
            value = server, onValueChange = { server = it },
            label = { Text("URL do servidor") }, modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(8.dp))
        Button(onClick = { vm.saveServer(server) }) { Text("Salvar servidor") }
        if (vm.saved.value) Text("Servidor salvo. Reinicie o app para reconectar.", color = NexusPrimary)

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))

        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Assistente por voz (wake word \"Jarvis\")", color = NexusText)
                Text(
                    "Mantém o JARVIS ouvindo em segundo plano, mesmo com o app fechado.",
                    color = NexusTextDim, style = MaterialTheme.typography.bodySmall
                )
            }
            Switch(
                checked = vm.wakeWord.value,
                onCheckedChange = { enable ->
                    if (enable) {
                        if (ctx.checkSelfPermission(Manifest.permission.RECORD_AUDIO) ==
                            android.content.pm.PackageManager.PERMISSION_GRANTED
                        ) vm.toggleWakeWord(ctx, true)
                        else micLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    } else {
                        vm.toggleWakeWord(ctx, false)
                    }
                }
            )
        }

        Spacer(Modifier.height(8.dp))
        Button(onClick = { requestBatteryOptimizationExemption(ctx) }) {
            Text("Otimizar bateria (manter sempre ativo)")
        }

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))

        // ---- Voz do JARVIS ----
        Text("Voz do JARVIS", color = NexusPrimary, style = MaterialTheme.typography.titleMedium)
        Text(
            "Ajuste o tom (mais grave = mais parecido com o JARVIS).",
            color = NexusTextDim, style = MaterialTheme.typography.bodySmall
        )
        Spacer(Modifier.height(6.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Tom:", color = NexusText, modifier = Modifier.width(48.dp))
            Slider(
                value = vm.pitch.value,
                onValueChange = { vm.setPitch(it) },
                valueRange = 0.5f..1.5f,
                modifier = Modifier.weight(1f)
            )
            Text("%.2f".format(vm.pitch.value), color = NexusTextDim, modifier = Modifier.width(48.dp))
        }
        Button(onClick = { vm.testVoice() }) { Text("Testar voz do JARVIS") }
        vm.voiceStatus.value?.let { Text(it, color = NexusTextDim, style = MaterialTheme.typography.bodySmall) }

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))

        // ---- Atualização ----
        Text("Atualização do app", color = NexusPrimary, style = MaterialTheme.typography.titleMedium)
        Button(onClick = { vm.checkUpdate(ctx) }) { Text("Verificar atualização") }
        vm.updateStatus.value?.let {
            Text(it, color = if (vm.updateAvailable.value) NexusPrimary else NexusTextDim,
                style = MaterialTheme.typography.bodySmall)
        }

        Spacer(Modifier.height(16.dp))
        Divider(color = NexusSurface)
        Spacer(Modifier.height(12.dp))

        vm.info.value?.let { info ->
            Text("Versão: ${info.version}", color = NexusText)
            Text(
                "LLM disponível: ${if (info.llmAvailable) "sim" else "não (modo demo)"}",
                color = NexusText
            )
            Text("Usuário: ${info.user.displayName}", color = NexusTextDim)
            Spacer(Modifier.height(8.dp))
            Text("Novidades (changelog):", color = NexusPrimary)
            Text(
                info.changelog.take(2500), color = NexusTextDim,
                style = MaterialTheme.typography.bodySmall
            )
        }
        if (vm.error.value != null) Text(vm.error.value ?: "", color = NexusDanger)

        Spacer(Modifier.weight(1f))
        Button(
            onClick = { authVm.logout() },
            colors = ButtonDefaults.buttonColors(containerColor = NexusDanger)
        ) {
            Text("Sair / Desconectar")
        }
    }
}

private fun requestBatteryOptimizationExemption(context: Context) {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
        val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
            data = Uri.parse("package:${context.packageName}")
        }
        context.startActivity(intent)
    }
}
