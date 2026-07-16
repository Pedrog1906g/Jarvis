package com.nexusai.app.ui.screen

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.nexusai.app.data.model.MemoryFact
import com.nexusai.app.ui.theme.NexusCyan
import com.nexusai.app.ui.theme.NexusViolet
import com.nexusai.app.viewmodel.MemoryViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemoryScreen(vm: MemoryViewModel = viewModel()) {
    var newFact by remember { mutableStateOf("") }

    LaunchedEffect(Unit) { vm.load() }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // ── Cabeçalho ──────────────────────────────────────────────────────
        Text(
            "MEMÓRIA LONGA",
            style = MaterialTheme.typography.titleMedium,
            color = NexusViolet,
            letterSpacing = 4.sp,
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.padding(bottom = 4.dp)
        )
        Text(
            "${vm.totalFacts.value} fatos armazenados",
            style = MaterialTheme.typography.bodySmall,
            color = Color(0xFF507F9F),
            fontFamily = FontFamily.Monospace,
            modifier = Modifier.padding(bottom = 12.dp)
        )

        // ── Erro ───────────────────────────────────────────────────────────
        vm.error.value?.let {
            Text(it, color = MaterialTheme.colorScheme.error, fontSize = 12.sp,
                modifier = Modifier.padding(bottom = 8.dp))
        }

        // ── Campo de adicionar fato ─────────────────────────────────────────
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp)
        ) {
            OutlinedTextField(
                value = newFact,
                onValueChange = { newFact = it },
                placeholder = { Text("Adicionar fato...", fontFamily = FontFamily.Monospace, fontSize = 12.sp) },
                modifier = Modifier.weight(1f),
                singleLine = true,
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
                keyboardActions = KeyboardActions(onDone = {
                    vm.addFact(newFact); newFact = ""
                }),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = NexusViolet,
                    unfocusedBorderColor = Color(0xFF1A2440),
                    focusedTextColor = Color(0xFFD6F3FF),
                    unfocusedTextColor = Color(0xFF507F9F)
                )
            )
            Spacer(Modifier.width(8.dp))
            Button(
                onClick = { vm.addFact(newFact); newFact = "" },
                colors = ButtonDefaults.buttonColors(containerColor = NexusViolet)
            ) {
                Text("+", fontFamily = FontFamily.Monospace)
            }
        }

        // ── Lista de fatos ──────────────────────────────────────────────────
        if (vm.loading.value) {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator(color = NexusViolet, modifier = Modifier.size(32.dp))
            }
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(vm.facts, key = { it.id }) { fact ->
                    MemoryFactCard(fact = fact, onDelete = { vm.deleteFact(fact.id) })
                }
                if (vm.facts.isEmpty()) {
                    item {
                        Text(
                            "Nenhum fato na memória ainda.\nConverse com o JARVIS para que ele aprenda sobre você.",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF507F9F),
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun MemoryFactCard(fact: MemoryFact, onDelete: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0A1828)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF1A2440))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.Top
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    fact.fact,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFFD6F3FF),
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 18.sp
                )
                Spacer(Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        fact.category.uppercase(),
                        style = MaterialTheme.typography.labelSmall,
                        color = NexusViolet,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 1.sp
                    )
                    Text(
                        "imp:${fact.importance}",
                        style = MaterialTheme.typography.labelSmall,
                        color = Color(0xFF507F9F),
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
            IconButton(onClick = onDelete, modifier = Modifier.size(32.dp)) {
                Icon(Icons.Default.Delete, contentDescription = "Remover",
                    tint = Color(0x88FF3A58), modifier = Modifier.size(16.dp))
            }
        }
    }
}
