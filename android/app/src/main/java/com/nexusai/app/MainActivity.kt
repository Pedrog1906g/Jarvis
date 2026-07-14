package com.nexusai.app

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.runtime.getValue
import androidx.lifecycle.ViewModelProvider
import androidx.compose.runtime.collectAsState
import com.nexusai.app.ui.nav.AppScaffold
import com.nexusai.app.ui.screen.LoginScreen
import com.nexusai.app.ui.theme.NexusTheme
import com.nexusai.app.viewmodel.AuthViewModel

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
    }
}
