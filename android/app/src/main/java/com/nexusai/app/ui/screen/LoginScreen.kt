package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.runtime.collectAsState
import androidx.fragment.app.FragmentActivity
import com.nexusai.app.ui.theme.*
import com.nexusai.app.util.ServiceDiscovery
import com.nexusai.app.util.canUseBiometric
import com.nexusai.app.util.showBiometricPrompt
import com.nexusai.app.viewmodel.AuthStatus
import com.nexusai.app.viewmodel.AuthViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

@Composable
fun LoginScreen(vm: AuthViewModel) {
    val ctx = LocalContext.current
    val activity = ctx as? FragmentActivity
    val scope = rememberCoroutineScope()

    var server by remember { mutableStateOf(vm.serverUrl.value) }
    var user by remember { mutableStateOf(vm.username.value) }
    var pass by remember { mutableStateOf(vm.passphrase.value) }

    val status by vm.status
    val error by vm.error
    val token by vm.token.collectAsState()

    var scanning by remember { mutableStateOf(false) }
    var testing by remember { mutableStateOf(false) }
    var connMsg by remember { mutableStateOf<String?>(null) }

    fun testConnection() {
        val base = server.trim().trimEnd('/')
        if (base.isEmpty()) { connMsg = "Informe a URL do servidor"; return }
        testing = true
        connMsg = "Testando conexão…"
        scope.launch(Dispatchers.IO) {
            try {
                val con = (URL("$base/").openConnection() as HttpURLConnection).apply {
                    connectTimeout = 4000
                    readTimeout = 4000
                    requestMethod = "GET"
                }
                val code = con.responseCode
                con.disconnect()
                withContext(Dispatchers.Main) {
                    connMsg = if (code in 200..399) "✅ Conectado (HTTP $code)" else "❌ Servidor respondeu $code"
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { connMsg = "❌ Não conectou: ${e.message}" }
            } finally {
                withContext(Dispatchers.Main) { testing = false }
            }
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().background(NexusBackground).padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("NEXUS", style = MaterialTheme.typography.headlineLarge, color = NexusPrimary)
        Text("Assistente pessoal de IA", color = NexusTextDim)
        Spacer(Modifier.height(24.dp))

        OutlinedTextField(
            value = server, onValueChange = { server = it },
            label = { Text("Servidor (URL)") },
            placeholder = { Text("http://192.168.0.15:8000") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(6.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = {
                    scanning = true
                    connMsg = "Buscando servidor NEXUS na rede…"
                    ServiceDiscovery.discover(ctx) { list ->
                        scanning = false
                        if (list.isNotEmpty()) {
                            server = list.first()
                            connMsg = "🔎 Servidor encontrado: ${list.first()}"
                        } else {
                            connMsg = "Nenhum servidor NEXUS encontrado na rede."
                        }
                    }
                },
                enabled = !scanning,
                modifier = Modifier.weight(1f)
            ) { Text(if (scanning) "Buscando…" else "🔎 Buscar na rede") }

            OutlinedButton(
                onClick = { testConnection() },
                enabled = !testing,
                modifier = Modifier.weight(1f)
            ) { Text(if (testing) "Testando…" else "Testar") }
        }
        Spacer(Modifier.height(6.dp))
        Text(
            "Padrão: https://nexus-api-2o1y.onrender.com (backend na nuvem). Em rede local, " +
                "toque em \"Buscar na rede\" ou digite o IP (ex: http://192.168.0.15:8000).",
            style = MaterialTheme.typography.bodySmall, color = NexusTextDim
        )
        if (connMsg != null) {
            Spacer(Modifier.height(4.dp))
            val ok = connMsg?.startsWith("✅") == true
            Text(connMsg ?: "", style = MaterialTheme.typography.bodySmall,
                color = if (ok) NexusPrimary else NexusTextDim)
        }
        Spacer(Modifier.height(10.dp))

        OutlinedTextField(value = user, onValueChange = { user = it },
            label = { Text("Usuário") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(value = pass, onValueChange = { pass = it },
            label = { Text("Frase de acesso") }, visualTransformation = PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(16.dp))

        Button(onClick = { vm.login(user, pass, server) }, modifier = Modifier.fillMaxWidth(),
            enabled = status != AuthStatus.Loading) {
            Text(if (status == AuthStatus.Loading) "Conectando…" else "Entrar")
        }

        if (error != null) {
            Spacer(Modifier.height(8.dp))
            Text(error ?: "", color = NexusDanger)
        }

        if (token != null && activity != null) {
            Spacer(Modifier.height(12.dp))
            OutlinedButton(
                onClick = {
                    if (canUseBiometric(activity))
                        showBiometricPrompt(activity,
                            onSuccess = { vm.unlockWithBiometric() },
                            onError = { vm.unlockWithBiometric() })
                    else vm.unlockWithBiometric()
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Desbloquear com biometria")
            }
        }
    }
}
