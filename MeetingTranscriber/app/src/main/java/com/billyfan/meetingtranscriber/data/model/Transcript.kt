package com.billyfan.meetingtranscriber.data.model

import kotlinx.serialization.Serializable

/**
 * Provider-agnostic transcript. Every STT provider normalizes its raw response
 * into this shape so the rest of the app never depends on a specific vendor.
 */
@Serializable
data class Transcript(
    val language: String,
    val segments: List<TranscriptSegment>
) {
    /** Plain-text view of the whole transcript, for copy/search. */
    val fullText: String
        get() = segments.joinToString("\n") { seg ->
            val who = seg.speaker?.let { "$it: " } ?: ""
            "$who${seg.text}"
        }
}

/** One contiguous chunk of speech attributed to a single speaker. */
@Serializable
data class TranscriptSegment(
    val speaker: String?,
    val startMs: Long,
    val endMs: Long,
    val text: String
)
