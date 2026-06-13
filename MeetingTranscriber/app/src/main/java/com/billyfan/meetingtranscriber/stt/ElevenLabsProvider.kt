package com.billyfan.meetingtranscriber.stt

import com.billyfan.meetingtranscriber.data.model.Transcript
import com.billyfan.meetingtranscriber.data.model.TranscriptSegment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

/**
 * ElevenLabs Scribe speech-to-text. The endpoint returns the full transcript in a
 * single synchronous response (no job polling needed), which keeps M1 simple.
 *
 * Docs: POST https://api.elevenlabs.io/v1/speech-to-text  (header: xi-api-key)
 */
class ElevenLabsProvider(
    private val apiKey: String,
    private val client: OkHttpClient,
    private val json: Json,
    // "scribe_v1" is the documented model id; swap here if the account is on a newer one.
    private val modelId: String = "scribe_v1"
) : SttProvider {

    override val id: String = ProviderId.ELEVENLABS

    override suspend fun transcribe(audioFile: File, options: SttOptions): Transcript =
        withContext(Dispatchers.IO) {
            if (apiKey.isBlank()) throw SttException("尚未設定 ElevenLabs API 金鑰,請到設定頁填入。")

            val mediaType = "application/octet-stream".toMediaTypeOrNull()
            val body = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("model_id", modelId)
                .addFormDataPart("language_code", options.languageCode)
                .addFormDataPart("diarize", options.diarize.toString())
                .addFormDataPart("timestamps_granularity", "word")
                .addFormDataPart("file", audioFile.name, audioFile.asRequestBody(mediaType))
                .build()

            val request = Request.Builder()
                .url("https://api.elevenlabs.io/v1/speech-to-text")
                .addHeader("xi-api-key", apiKey)
                .post(body)
                .build()

            try {
                client.newCall(request).execute().use { resp ->
                    val payload = resp.body?.string().orEmpty()
                    if (!resp.isSuccessful) {
                        throw SttException("ElevenLabs 轉譯失敗 (HTTP ${resp.code}): ${payload.take(300)}")
                    }
                    val parsed = json.decodeFromString<ElevenLabsResponse>(payload)
                    toTranscript(parsed, options)
                }
            } catch (e: SttException) {
                throw e
            } catch (e: Exception) {
                throw SttException("呼叫 ElevenLabs 時發生錯誤:${e.message}", e)
            }
        }

    /** Group consecutive words by speaker into readable, timestamped segments. */
    private fun toTranscript(resp: ElevenLabsResponse, options: SttOptions): Transcript {
        val segments = mutableListOf<TranscriptSegment>()
        var speaker: String? = null
        var startSec = 0.0
        var endSec = 0.0
        var open = false
        val text = StringBuilder()

        fun flush() {
            if (open && text.isNotBlank()) {
                segments += TranscriptSegment(
                    speaker = speaker?.let(::prettySpeaker),
                    startMs = (startSec * 1000).toLong(),
                    endMs = (endSec * 1000).toLong(),
                    text = text.toString().trim()
                )
            }
            text.setLength(0)
            open = false
        }

        for (w in resp.words) {
            if (w.type == "spacing") {
                if (open) text.append(w.text)
                continue
            }
            if (!open) {
                speaker = w.speakerId
                startSec = w.start ?: 0.0
            } else if (w.speakerId != speaker) {
                flush()
                speaker = w.speakerId
                startSec = w.start ?: 0.0
            }
            text.append(w.text)
            endSec = w.end ?: endSec
            open = true
        }
        flush()

        // Fall back to the flat text field if word-level data was unavailable.
        if (segments.isEmpty() && resp.text.isNotBlank()) {
            segments += TranscriptSegment(null, 0L, 0L, resp.text)
        }
        return Transcript(language = resp.languageCode ?: options.languageCode, segments = segments)
    }

    /** "speaker_0" -> "說話者 1" for display. */
    private fun prettySpeaker(raw: String): String {
        val n = raw.substringAfterLast('_').toIntOrNull()
        return if (n != null) "說話者 ${n + 1}" else raw
    }

    @Serializable
    private data class ElevenLabsResponse(
        @SerialName("language_code") val languageCode: String? = null,
        val text: String = "",
        val words: List<Word> = emptyList()
    )

    @Serializable
    private data class Word(
        val text: String = "",
        val start: Double? = null,
        val end: Double? = null,
        val type: String = "word",
        @SerialName("speaker_id") val speakerId: String? = null
    )
}
