package com.nexusai.app.ui.component

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.nexusai.app.ui.theme.NexusPrimary

/**
 * Moldura de HUD estilo "Homem de Ferro": scanlines sutis + cantos em colchete.
 * Usada atrás do conteúdo das telas para dar o visual de cabeçote do JARVIS.
 */
@Composable
fun HudFrame(modifier: Modifier = Modifier) {
    Box(modifier = modifier) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            // scanlines
            val step = 4.dp.toPx()
            var y = 0f
            while (y <= size.height) {
                drawLine(
                    color = Color(0xFF0A2A33),
                    start = Offset(0f, y),
                    end = Offset(size.width, y),
                    strokeWidth = 1f,
                    alpha = 0.22f
                )
                y += step
            }
            // cantos em colchete
            val c = NexusPrimary
            val L = 26.dp.toPx()
            val m = 12.dp.toPx()
            val w = 2.dp.toPx()
            val a = 0.85f
            // top-left
            drawLine(c, Offset(m, m + L), Offset(m, m), strokeWidth = w, alpha = a)
            drawLine(c, Offset(m, m), Offset(m + L, m), strokeWidth = w, alpha = a)
            // top-right
            drawLine(c, Offset(size.width - m - L, m), Offset(size.width - m, m), strokeWidth = w, alpha = a)
            drawLine(c, Offset(size.width - m, m), Offset(size.width - m, m + L), strokeWidth = w, alpha = a)
            // bottom-left
            drawLine(c, Offset(m, size.height - m - L), Offset(m, size.height - m), strokeWidth = w, alpha = a)
            drawLine(c, Offset(m, size.height - m), Offset(m + L, size.height - m), strokeWidth = w, alpha = a)
            // bottom-right
            drawLine(c, Offset(size.width - m - L, size.height - m), Offset(size.width - m, size.height - m), strokeWidth = w, alpha = a)
            drawLine(c, Offset(size.width - m, size.height - m), Offset(size.width - m, size.height - m - L), strokeWidth = w, alpha = a)
        }
    }
}
