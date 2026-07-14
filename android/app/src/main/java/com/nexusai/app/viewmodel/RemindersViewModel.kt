package com.nexusai.app.viewmodel

import android.app.Application
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.nexusai.app.NexusApplication
import com.nexusai.app.data.model.ReminderDto
import com.nexusai.app.data.repository.NexusRepository
import kotlinx.coroutines.launch

class RemindersViewModel(app: Application) : AndroidViewModel(app) {

    private val repo: NexusRepository = (app as NexusApplication).repository

    val reminders = mutableStateListOf<ReminderDto>()
    var loading = mutableStateOf(false)
    var error = mutableStateOf<String?>(null)

    fun load() {
        loading.value = true
        viewModelScope.launch {
            try {
                reminders.clear()
                reminders.addAll(repo.reminders())
            } catch (e: Exception) {
                error.value = e.localizedMessage
            } finally {
                loading.value = false
            }
        }
    }

    fun add(title: String, dueAt: String, note: String? = null) {
        if (title.isBlank()) return
        viewModelScope.launch {
            try {
                val r = repo.createReminder(title, dueAt, note)
                reminders.add(0, r)
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }

    fun done(id: Int) {
        viewModelScope.launch {
            try {
                repo.doneReminder(id)
                reminders.removeIf { it.id == id }
            } catch (e: Exception) {
                error.value = e.localizedMessage
            }
        }
    }
}
