package com.example.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Main ViewModel for the app.
 */
class MainViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    fun loadData() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                // Simulate network call
                val data = repository.getData()
                _uiState.value = UiState(data = data)
            } catch (e: Exception) {
                _uiState.value = UiState(error = e.message)
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun refresh() {
        loadData()
    }
}

/**
 * UI state for the main screen.
 */
data class UiState(
    val data: List<Item> = emptyList(),
    val error: String? = null,
    val isLoading: Boolean = false
)

/**
 * An item in the list.
 */
data class Item(
    val id: String,
    val title: String,
    val description: String,
    val timestamp: Long
)
