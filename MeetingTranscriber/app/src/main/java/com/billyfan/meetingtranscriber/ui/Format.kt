package com.billyfan.meetingtranscriber.ui

import java.util.Locale
import java.util.concurrent.TimeUnit

/** "mm:ss" or "h:mm:ss" for a duration in milliseconds. */
fun formatDuration(ms: Long): String {
    val totalSeconds = ms / 1000
    val hours = TimeUnit.SECONDS.toHours(totalSeconds)
    val minutes = TimeUnit.SECONDS.toMinutes(totalSeconds) % 60
    val seconds = totalSeconds % 60
    return if (hours > 0) {
        String.format(Locale.US, "%d:%02d:%02d", hours, minutes, seconds)
    } else {
        String.format(Locale.US, "%02d:%02d", minutes, seconds)
    }
}

/** Timestamp like "01:23" used as a clickable marker in front of a segment. */
fun formatTimestamp(ms: Long): String = formatDuration(ms)
