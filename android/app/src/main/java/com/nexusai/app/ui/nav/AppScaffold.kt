package com.nexusai.app.ui.nav

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.nexusai.app.ui.screen.*
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.AuthViewModel
import com.nexusai.app.viewmodel.MemoryViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppScaffold(authVm: AuthViewModel) {
    val drawerState = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    var screen by remember { mutableStateOf("chat") }

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet(drawerContainerColor = NexusSurface) {
                Spacer(Modifier.height(24.dp))
                Text("JARVIS", modifier = Modifier.padding(16.dp),
                    color = NexusPrimary, style = MaterialTheme.typography.titleLarge)
                val items = listOf(
                    "chat"      to "Chat",
                    "history"   to "Histórico",
                    "reminders" to "Lembretes",
                    "memory"    to "🧠 Memória",
                    "devices"   to "Dispositivos",
                    "controle"  to "Controle",
                    "auto"      to "Auto-melhoria",
                    "settings"  to "Ajustes"
                )
                items.forEach { (key, label) ->
                    NavigationDrawerItem(
                        label = { Text(label, color = NexusText) },
                        selected = screen == key,
                        onClick = { screen = key; scope.launch { drawerState.close() } },
                        modifier = Modifier.padding(horizontal = 12.dp)
                    )
                }
            }
        }
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("JARVIS", color = NexusText) },
                    navigationIcon = {
                        IconButton(onClick = { scope.launch { drawerState.open() } }) {
                            Icon(Icons.Filled.Menu, contentDescription = "Menu", tint = NexusPrimary)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = NexusBackground)
                )
            },
            containerColor = NexusBackground
        ) { padding ->
            Box(Modifier.fillMaxSize().padding(padding)) {
                when (screen) {
                    "chat"      -> ChatScreen()
                    "history"   -> HistoryScreen()
                    "reminders" -> RemindersScreen()
                    "memory"    -> MemoryScreen(viewModel = MemoryViewModel(androidx.compose.ui.platform.LocalContext.current.applicationContext as android.app.Application))
                    "devices"   -> DevicesScreen()
                    "controle"  -> ControlScreen()
                    "auto"      -> AutoImproveScreen()
                    "settings"  -> SettingsScreen(authVm)
                }
            }
        }
    }
}
