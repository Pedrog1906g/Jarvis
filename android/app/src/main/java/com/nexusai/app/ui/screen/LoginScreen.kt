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
import com.nexusai.app.util.canUseBiometric
import com.nexusai.app.util.showBiometricPrompt
import com.nexusai.app.viewmodel.AuthStatus
import com.nexusai.app.viewmodel.AuthViewModel

@Composable
fun LoginScreen(vm: AuthViewModel) {
    val ctx = LocalContext.current
    val activity = ctx as? FragmentActivity

    var server by remember { mutableStateOf(vm.serverUrl.value) }
    var user by remember { mutableStateOf(vm.username.value) }
    var pass by remember { mutableStateOf(vm.passphrase.value) }

    val status by vm.status
    val error by vm.error
    val token by vm.token.collectAsState()

    Column(
        modifier = Modifier.fillMaxSize().background(NexusBackground).padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        Text("NEXUS", style = MaterialTheme.typography.headlineLarge, color = NexusPrimary)
        Text("Assistente pessoal de IA", color = NexusTextDim)
        Spacer(Modifier.height(24.dp))

        OutlinedTextField(value = server, onValueChange = { server = it },
            label = { Text("Servidor (URL)") }, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
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
