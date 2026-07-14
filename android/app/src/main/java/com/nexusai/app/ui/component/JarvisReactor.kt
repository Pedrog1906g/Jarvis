package com.nexusai.app.ui.component

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nexusai.app.ui.theme.*

@Composable
fun JarvisReactor(
    listening: Boolean,
    partial: String = "",
    onClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val transition = rememberInfiniteTransition()
    val rot1 by transition.animateFloat(0f, 360f, infiniteRepeatable(tween(12000, easing = LinearEasing)))
    val rot2 by transition.animateFloat(360f, 0f, infiniteRepeatable(tween(9000, easing = LinearEasing)))
    val rot3 by transition.animateFloat(0f, 360f, infiniteRepeatable(tween(6000, easing = LinearEasing)))
    val pulse by transition.animateFloat(1f, 1.1f, infiniteRepeatable(tween(900), RepeatMode.Reverse))

    Box(
        modifier.fillMaxWidth().height(210.dp).clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Box(Modifier.size(184.dp).rotate(rot1).border(2.dp, NexusPrimary.copy(alpha = 0.35f), CircleShape)) {}
        Box(Modifier.size(150.dp).rotate(rot2).border(2.dp, NexusAccent.copy(alpha = 0.45f), CircleShape)) {}
        Box(Modifier.size(118.dp).rotate(rot3).border(1.dp, NexusPrimary.copy(alpha = 0.7f), CircleShape)) {}

        Box(
            Modifier
                .size((if (listening) 88 else 82).dp * pulse)
                .clip(CircleShape)
                .background(
                    Brush.radialGradient(
                        listOf(
                            if (listening) NexusAccent else NexusPrimary,
                            NexusAccent,
                            NexusBackground
                        )
                    )
                )
        )

        Text(
            if (listening) "OUVINDO…" else "JARVIS",
            color = if (listening) NexusAccent else NexusPrimary,
            fontSize = 12.sp,
            fontFamily = FontFamily.Monospace,
            fontWeight = FontWeight.Bold,
            letterSpacing = 3.sp,
            modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 46.dp)
        )

        if (listening) {
            Row(
                Modifier.align(Alignment.BottomCenter).padding(bottom = 12.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) { repeat(5) { WaveBar(it * 110) } }

            if (partial.isNotBlank()) {
                Text(
                    partial,
                    color = NexusPrimary,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.align(Alignment.TopCenter).padding(top = 6.dp)
                )
            }
        }
    }
}

@Composable
private fun WaveBar(delayMs: Int) {
    val transition = rememberInfiniteTransition()
    val h by transition.animateFloat(
        6f, 24f,
        infiniteRepeatable(tween(500, delayMillis = delayMs), RepeatMode.Reverse)
    )
    Box(Modifier.width(4.dp).height(h.dp).clip(RoundedCornerShape(2.dp)).background(NexusPrimary))
}
