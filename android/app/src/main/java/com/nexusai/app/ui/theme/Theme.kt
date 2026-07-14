package com.nexusai.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = NexusPrimary,
    onPrimary = NexusBackground,
    background = NexusBackground,
    surface = NexusSurface,
    onSurface = NexusText,
    onBackground = NexusText,
    secondary = NexusAccent,
    onSecondary = NexusText,
    error = NexusDanger
)

@Composable
fun NexusTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
