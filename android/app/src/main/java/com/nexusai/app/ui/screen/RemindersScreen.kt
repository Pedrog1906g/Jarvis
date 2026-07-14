package com.nexusai.app.ui.screen

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.ui.theme.*
import com.nexusai.app.viewmodel.RemindersViewModel
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RemindersScreen() {
    val vm: RemindersViewModel = viewModel()
    val scope = rememberCoroutineScope()
    var showDialog by remember { mutableStateOf(false) }
    var title by remember { mutableStateOf("") }
    var date by remember { mutableStateOf("") }
    var note by remember { mutableStateOf("") }

    LaunchedEffect(Unit) { vm.load() }

    Scaffold(
        containerColor = NexusBackground,
        floatingActionButton = {
            FloatingActionButton(onClick = { showDialog = true }, containerColor = NexusPrimary) {
                Icon(androidx.compose.material.icons.Icons.Filled.Add, contentDescription = "Novo", tint = NexusBackground)
            }
        }
    ) { padding ->
        Column(Modifier.fillMaxSize().background(NexusBackground).padding(padding).padding(12.dp)) {
            Text("Lembretes", style = MaterialTheme.typography.titleLarge, color = NexusText)
            if (vm.loading.value) CircularProgressIndicator(color = NexusPrimary)
            LazyColumn {
                items(vm.reminders, key = { it.id }) { r ->
                    Card(Modifier.fillMaxWidth().padding(4.dp),
                        colors = CardDefaults.cardColors(containerColor = NexusSurface)) {
                        Row(Modifier.fillMaxWidth().padding(12.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically) {
                            Column {
                                Text(r.title, color = NexusText)
                                Text(r.dueAt.replace("T", " ").substringBefore("."), color = NexusTextDim,
                                    style = MaterialTheme.typography.bodySmall)
                            }
                            TextButton(onClick = { vm.done(r.id) }) {
                                Text("Concluir", color = NexusPrimary)
                            }
                        }
                    }
                }
            }
        }
    }

    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            containerColor = NexusSurface,
            title = { Text("Novo lembrete", color = NexusText) },
            text = {
                Column {
                    OutlinedTextField(value = title, onValueChange = { title = it },
                        label = { Text("Título") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(value = date, onValueChange = { date = it },
                        label = { Text("Data/hora (AAAA-MM-DD HH:MM)") }, modifier = Modifier.fillMaxWidth())
                    Spacer(Modifier.height(8.dp))
                    OutlinedTextField(value = note, onValueChange = { note = it },
                        label = { Text("Nota (opcional)") }, modifier = Modifier.fillMaxWidth())
                }
            },
            confirmButton = {
                Button(onClick = {
                    val iso = date.replace(" ", "T") + ":00"
                    vm.add(title, iso, note.ifBlank { null })
                    title = ""; date = ""; note = ""
                    showDialog = false
                }) { Text("Salvar") }
            },
            dismissButton = { TextButton(onClick = { showDialog = false }) { Text("Cancelar") } }
        )
    }
}
