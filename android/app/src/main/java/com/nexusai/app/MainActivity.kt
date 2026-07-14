package com.nexusai.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.compose.runtime.collectAsState
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.nexusai.app.ui.nav.AppScaffold
import com.nexusai.app.ui.screen.LoginScreen
import com.nexusai.app.ui.theme.NexusTheme
import com.nexusai.app.viewmodel.AuthViewModel
import com.nexusai.app.util.UpdateChecker
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var authVm: AuthViewModel

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
}
