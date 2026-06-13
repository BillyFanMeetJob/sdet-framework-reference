package com.billyfan.meetingtranscriber.data.settings

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.billyfan.meetingtranscriber.stt.ProviderId
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Immutable snapshot of user settings, including per-provider API keys. */
data class AppSettings(
    val providerId: String = ProviderId.ELEVENLABS,
    val elevenLabsKey: String = "",
    val deepgramKey: String = "",
    val languageCode: String = "zh",
    val diarize: Boolean = true
) {
    fun apiKeyFor(provider: String): String = when (provider) {
        ProviderId.ELEVENLABS -> elevenLabsKey
        ProviderId.DEEPGRAM -> deepgramKey
        else -> ""
    }

    val activeKeyConfigured: Boolean get() = apiKeyFor(providerId).isNotBlank()
}

/**
 * Persists settings — most importantly the STT API keys — in
 * [EncryptedSharedPreferences] so keys are never stored in plaintext, even though
 * this is a personal-use app. Exposes a [StateFlow] so Compose reacts to changes.
 */
class SettingsStore(context: Context) {

    private val prefs: SharedPreferences = run {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context,
            "secure_settings",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    private val _state = MutableStateFlow(load())
    val state: StateFlow<AppSettings> = _state.asStateFlow()

    val current: AppSettings get() = _state.value

    fun update(transform: (AppSettings) -> AppSettings) {
        val next = transform(_state.value)
        prefs.edit()
            .putString(KEY_PROVIDER, next.providerId)
            .putString(KEY_ELEVENLABS, next.elevenLabsKey)
            .putString(KEY_DEEPGRAM, next.deepgramKey)
            .putString(KEY_LANGUAGE, next.languageCode)
            .putBoolean(KEY_DIARIZE, next.diarize)
            .apply()
        _state.value = next
    }

    private fun load() = AppSettings(
        providerId = prefs.getString(KEY_PROVIDER, ProviderId.ELEVENLABS) ?: ProviderId.ELEVENLABS,
        elevenLabsKey = prefs.getString(KEY_ELEVENLABS, "") ?: "",
        deepgramKey = prefs.getString(KEY_DEEPGRAM, "") ?: "",
        languageCode = prefs.getString(KEY_LANGUAGE, "zh") ?: "zh",
        diarize = prefs.getBoolean(KEY_DIARIZE, true)
    )

    private companion object {
        const val KEY_PROVIDER = "provider"
        const val KEY_ELEVENLABS = "elevenlabs_key"
        const val KEY_DEEPGRAM = "deepgram_key"
        const val KEY_LANGUAGE = "language"
        const val KEY_DIARIZE = "diarize"
    }
}
