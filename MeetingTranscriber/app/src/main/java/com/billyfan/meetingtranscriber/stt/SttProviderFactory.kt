package com.billyfan.meetingtranscriber.stt

import com.billyfan.meetingtranscriber.data.settings.AppSettings
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient

/** Builds the configured [SttProvider]. Adding a vendor means one more branch here. */
class SttProviderFactory(
    private val client: OkHttpClient,
    private val json: Json
) {
    fun create(providerId: String, settings: AppSettings): SttProvider = when (providerId) {
        ProviderId.ELEVENLABS -> ElevenLabsProvider(settings.elevenLabsKey, client, json)
        ProviderId.DEEPGRAM -> DeepgramProvider(settings.deepgramKey, client, json)
        else -> throw SttException("未知的供應商:$providerId")
    }
}
