package com.billyfan.meetingtranscriber.stt

import com.billyfan.meetingtranscriber.data.model.Transcript
import com.billyfan.meetingtranscriber.data.model.TranscriptSegment
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import java.io.File

/**
 * Deepgram Nova-3 pre-recorded transcription. Cheaper per-minute backup provider.
 *
 * Docs: POST https://api.deepgram.com/v1/listen  (header: Authorization: Token <key>)
 * Raw audio is sent as the request body; query params drive model/lang/diarization.
 */
class DeepgramProvider(
    private val apiKey: String,
    private val client: OkHttpClient,
    private val json: Json,
    private val model: String = "nova-3"
) : SttProvider {

    override val id: String = ProviderId.DEEPGRAM

    override suspend fun transcribe(audioFile: File, options: SttOptions): Transcript =
        withContext(Dispatchers.IO) {
            if (apiKey.isBlank()) throw SttException("尚未設定 Deepgram API 金鑰,請到設定頁填入。")

            val url = "https://api.deepgram.com/v1/listen".toHttpUrl().newBuilder()
                .addQueryParameter("model", model)
                .addQueryParameter("language", options.languageCode)
                .addQueryParameter("diarize", options.diarize.toString())
                .addQueryParameter("punctuate", "true")
                .addQueryParameter("smart_format", "true")
                .build()

            val request = Request.Builder()
                .url(url)
                .addHeader("Authorization", "Token $apiKey")
                .post(audioFile.asRequestBody("application/octet-stream".toMediaTypeOrNull()))
                .build()

            try {
                client.newCall(request).execute().use { resp ->
                    val payload = resp.body?.string().orEmpty()
                    if (!resp.isSuccessful) {
                        throw SttException("Deepgram 轉譯失敗 (HTTP ${resp.code}): ${payload.take(300)}")
                    }
                    toTranscript(json.decodeFromString<DeepgramResponse>(payload), options)
                }
            } catch (e: SttException) {
                throw e
            } catch (e: Exception) {
                throw SttException("呼叫 Deepgram 時發生錯誤:${e.message}", e)
            }
        }

    private fun toTranscript(resp: DeepgramResponse, options: SttOptions): Transcript {
        val alt = resp.results?.channels?.firstOrNull()?.alternatives?.firstOrNull()
        val words = alt?.words.orEmpty()

        val segments = mutableListOf<TranscriptSegment>()
        var speaker: Int? = null
        var startSec = 0.0
        var endSec = 0.0
        var open = false
        val text = StringBuilder()

        fun flush() {
            if (open && text.isNotBlank()) {
                segments += TranscriptSegment(
                    speaker = speaker?.let { "說話者 ${it + 1}" },
                    startMs = (startSec * 1000).toLong(),
                    endMs = (endSec * 1000).toLong(),
                    text = text.toString().trim()
                )
            }
            text.setLength(0)
            open = false
        }

        for (w in words) {
            val token = w.punctuatedWord ?: w.word
            if (!open) {
                speaker = w.speaker
                startSec = w.start ?: 0.0
            } else if (w.speaker != speaker) {
                flush()
                speaker = w.speaker
                startSec = w.start ?: 0.0
            }
            if (text.isNotEmpty()) text.append(' ')
            text.append(token)
            endSec = w.end ?: endSec
            open = true
        }
        flush()

        if (segments.isEmpty() && !alt?.transcript.isNullOrBlank()) {
            segments += TranscriptSegment(null, 0L, 0L, alt!!.transcript)
        }
        return Transcript(language = options.languageCode, segments = segments)
    }

    @Serializable
    private data class DeepgramResponse(val results: Results? = null)

    @Serializable
    private data class Results(val channels: List<Channel> = emptyList())

    @Serializable
    private data class Channel(val alternatives: List<Alternative> = emptyList())

    @Serializable
    private data class Alternative(
        val transcript: String = "",
        val words: List<Word> = emptyList()
    )

    @Serializable
    private data class Word(
        val word: String = "",
        @SerialName("punctuated_word") val punctuatedWord: String? = null,
        val start: Double? = null,
        val end: Double? = null,
        val speaker: Int? = null
    )
}
