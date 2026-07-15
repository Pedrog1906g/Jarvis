package com.nexusai.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Toast
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.collectAsState
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.nexusai.app.data.store.TokenStore
import com.nexusai.app.service.NexusVoiceService
import com.nexusai.app.ui.nav.AppScaffold
import com.nexusai.app.ui.screen.LoginScreen
import com.nexusai.app.ui.theme.NexusTheme
import com.nexusai.app.viewmodel.AuthViewModel
import com.nexusai.app.util.UpdateChecker
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var authVm: AuthViewModel
    private val prefs by lazy { TokenStore(this) }
    companion object { private const val REQ_PERMS = 1001 }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        authVm = ViewModelProvider(this)[AuthViewModel::class.java]
        setContent {
            NexusTheme {
                val token by authVm.token.collectAsState()
                if (token == null) {
                    LoginScreen(vm = authVm)
                } else {
                    AppScaffold(authVm = authVm)
                }
            }
        }

        // Pede a permissão do microfone (e notificações) ao abrir. Sem isso o Android
        // bloqueia o reconhecimento de voz e o "Jarvis" nunca responde.
        requestNeededPermissions()

        // Login automático: o app já entra com as credenciais padrão (owner/nexus),
        // assim o JARVIS responde de imediato, sem precisar digitar nada.
        if (prefs.getToken().isNullOrBlank()) {
            authVm.login("owner", "nexus", prefs.getServerUrl())
        }

        // Avisa sobre atualização disponível ao abrir o app.
        lifecycleScope.launch {
            val rel = UpdateChecker.fetchLatest()
            if (rel != null && UpdateChecker.isUpdateAvailable(rel)) {
                Toast.makeText(
                    this@MainActivity,
                    "Nova versão do JARVIS disponível (${rel.version}). Vá em Ajustes > Atualização.",
                    Toast.LENGTH_LONG
                ).show()
            }
        }
    }

    private fun requestNeededPermissions() {
        val needed = mutableListOf<String>()
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.RECORD_AUDIO)
        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
            != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.POST_NOTIFICATIONS)
        if (needed.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, needed.toTypedArray(), REQ_PERMS)
        } else {
            maybeStartVoice()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == REQ_PERMS) {
            val micOk = permissions.zip(grantResults.toList())
                .any { (p, r) -> p == Manifest.permission.RECORD_AUDIO && r == PackageManager.PERMISSION_GRANTED }
            if (!micOk) {
                Toast.makeText(this, "Permita o microfone para falar com o JARVIS.", Toast.LENGTH_LONG).show()
            }
            maybeStartVoice()
        }
    }

    /** Se a wake word "Jarvis" já estava ativada, religa o serviço de voz. */
    private fun maybeStartVoice() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            == PackageManager.PERMISSION_GRANTED && prefs.isWakeWordEnabled()
        ) {
            NexusVoiceService.start(this)
        }
    }
}
