package com.billyfan.meetingtranscriber

import android.app.Application
import android.content.Context
import com.billyfan.meetingtranscriber.data.RecordingRepository
import com.billyfan.meetingtranscriber.data.db.AppDatabase
import com.billyfan.meetingtranscriber.data.settings.SettingsStore
import com.billyfan.meetingtranscriber.stt.SttProviderFactory
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

/** Manual DI container — keeps M1 dependency-free of a DI framework. */
class AppContainer(context: Context) {

    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }

    // Long meetings can take several minutes to transcribe; allow generous timeouts.
    private val httpClient = OkHttpClient.Builder()
        .callTimeout(20, TimeUnit.MINUTES)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.MINUTES)
        .writeTimeout(20, TimeUnit.MINUTES)
        .build()

    val settings = SettingsStore(context)

    private val database = AppDatabase.get(context)
    private val providerFactory = SttProviderFactory(httpClient, json)

    val repository = RecordingRepository(
        context = context.applicationContext,
        dao = database.recordingDao(),
        settings = settings,
        providerFactory = providerFactory,
        json = json
    )
}

class MeetingTranscriberApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
