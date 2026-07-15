package com.example.app.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.app.MainViewModel
import com.example.app.Item

/**
 * Main screen composable.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    viewModel: MainViewModel,
    onItemClick: (Item) -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("My App") }
            )
        }
    ) { paddingValues ->
        if (isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier.padding(paddingValues)
            ) {
                items(uiState.data) { item ->
                    ItemCard(
                        item = item,
                        onClick = { onItemClick(item) }
                    )
                }
            }
        }
    }
}

/**
 * Card for displaying an item.
 */
@Composable
fun ItemCard(
    item: Item,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = item.title,
                style = MaterialTheme.typography.headlineSmall
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = item.description,
                style = MaterialTheme.typography.bodyMedium
            )
        }
    }
}

/**
 * Extension function for formatting timestamps.
 */
fun Long.toFormattedDate(): String {
    val instant = Instant.fromEpochMilliseconds(this)
    val datetime = instant.toLocalDateTime(TimeZone.UTC)
    return "${datetime.year}-${datetime.monthNumber}-${datetime.dayOfMonth}"
}

/**
 * Remember function for creating a mutable state.
 */
@Composable
fun <T> rememberMutableStateOf(initial: T): MutableState<T> {
    return remember { mutableStateOf(initial) }
}
