package com.nexusai.app.ui.component

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
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
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nexusai.app.ui.theme.*
import kotlin.math.cos
import kotlin.math.sin

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
    val pulse by transition.animateFloat(1f, 1.12f, infiniteRepeatable(tween(900), RepeatMode.Reverse))

    Box(
        modifier.fillMaxWidth().height(220.dp).clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        // radar sweep + ticks (estilo HUD do filme)
        Canvas(modifier = Modifier.size(190.dp)) {
            val cx = center.x
            val cy = center.y
            val r = size.minDimension / 2f - 6.dp.toPx()
            for (i in 0 until 72) {
                val a = (i * 5) * Math.PI / 180.0
                val major = i % 6 == 0
                val r2 = if (major) r - 9.dp.toPx() else r - 4.dp.toPx()
                drawLine(
                    color = NexusPrimary.copy(alpha = if (major) 0.55f else 0.22f),
                    start = Offset(cx + (r) * cos(a).toFloat(), cy + (r) * sin(a).toFloat()),
                    end = Offset(cx + (r2) * cos(a).toFloat(), cy + (r2) * sin(a).toFloat()),
                    strokeWidth = 1.5f
                )
            }
            // varredura (fatia preenchida)
            rotate(rot1) {
                drawArc(
                    color = NexusPrimary.copy(alpha = 0.35f),
                    startAngle = 0f,
                    sweepAngle = 70f,
                    useCenter = true,
                    topLeft = Offset(cx - r, cy - r),
                    size = Size(r * 2f, r * 2f)
                )
            }
        }

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
