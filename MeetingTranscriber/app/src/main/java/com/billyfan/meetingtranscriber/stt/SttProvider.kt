package com.billyfan.meetingtranscriber.stt

import com.billyfan.meetingtranscriber.data.model.Transcript
import java.io.File

/** Stable identifiers for the supported cloud STT providers. */
object ProviderId {
    const val ELEVENLABS = "elevenlabs"
    const val DEEPGRAM = "deepgram"

    val all = listOf(ELEVENLABS, DEEPGRAM)

    fun displayName(id: String): String = when (id) {
        ELEVENLABS -> "ElevenLabs Scribe"
        DEEPGRAM -> "Deepgram Nova-3"
        else -> id
    }
}

/** Options passed to a transcription request. */
data class SttOptions(
    val languageCode: String = "zh",
    val diarize: Boolean = true
)

/**
 * A cloud speech-to-text backend. Implementations call their vendor API directly
 * from the device and return a normalized [Transcript].
 *
 * M1 handles a single file in one request. Automatic chunking + merging for long
 * audio (M3) will live above this interface, not inside each provider.
 */
interface SttProvider {
    val id: String

    /** Transcribe [audioFile] in full. Throws [SttException] on failure. */
    suspend fun transcribe(audioFile: File, options: SttOptions): Transcript
}

/** Wraps any provider/network/auth failure with a user-presentable message. */
class SttException(message: String, cause: Throwable? = null) : Exception(message, cause)
