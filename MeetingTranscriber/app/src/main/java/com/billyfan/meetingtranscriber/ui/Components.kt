package com.billyfan.meetingtranscriber.ui

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import com.billyfan.meetingtranscriber.data.model.RecordingStatus

/** Small colored pill that conveys a recording's transcription state. */
@Composable
fun StatusChip(status: RecordingStatus) {
    val (label, color) = when (status) {
        RecordingStatus.RECORDED -> "待轉譯" to MaterialTheme.colorScheme.outline
        RecordingStatus.TRANSCRIBING -> "轉譯中" to MaterialTheme.colorScheme.tertiary
        RecordingStatus.DONE -> "完成" to MaterialTheme.colorScheme.primary
        RecordingStatus.FAILED -> "失敗" to MaterialTheme.colorScheme.error
    }
    Surface(
        color = color.copy(alpha = 0.12f),
        contentColor = color,
        shape = MaterialTheme.shapes.small
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp)
        ) {
            Dot(color)
            Spacer(Modifier.width(6.dp))
            Text(label, style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable
private fun Dot(color: Color) {
    Spacer(
        Modifier
            .size(8.dp)
            .background(color, CircleShape)
    )
}
