package com.nexusai.app.viewmodel

import android.app.Application
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.MemoryFact
import com.nexusai.app.data.repository.NexusRepository
import kotlinx.coroutines.launch

/**
 * ViewModel para a tela de Memória de Longo Prazo do NEXUS.
 * Gerencia os fatos duráveis extraídos das conversas pelo backend.
 */
class MemoryViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    val facts = mutableStateListOf<MemoryFact>()
    var loading = mutableStateOf(false)
    var error = mutableStateOf<String?>(null)
    var totalFacts = mutableStateOf(0)

    fun load() {
        loading.value = true
        error.value = null
        viewModelScope.launch {
            try {
                val result = repo.memoryFacts()
                facts.clear()
                facts.addAll(result)
                totalFacts.value = result.size
            } catch (e: Exception) {
                error.value = e.localizedMessage ?: "Erro ao carregar memória"
            } finally {
                loading.value = false
            }
        }
    }

    fun addFact(text: String, category: String = "manual") {
        if (text.isBlank()) return
        viewModelScope.launch {
            try {
                repo.addMemoryFact(text.trim(), category, importance = 2)
                load() // Recarrega para mostrar o novo fato
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }

    fun deleteFact(fid: Int) {
        viewModelScope.launch {
            try {
                repo.deleteMemoryFact(fid)
                facts.removeIf { it.id == fid }
                totalFacts.value = facts.size
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }

    fun clearAll() {
        viewModelScope.launch {
            try {
                repo.clearMemoryFacts()
                facts.clear()
                totalFacts.value = 0
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }
}
