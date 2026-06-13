package com.billyfan.meetingtranscriber.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.billyfan.meetingtranscriber.MeetingTranscriberApp
import com.billyfan.meetingtranscriber.data.db.RecordingEntity
import com.billyfan.meetingtranscriber.data.model.Transcript
import com.billyfan.meetingtranscriber.data.settings.AppSettings
import com.billyfan.meetingtranscriber.recording.AudioRecorder
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class MainViewModel(app: Application) : AndroidViewModel(app) {

    private val container = (app as MeetingTranscriberApp).container
    private val repository = container.repository
    private val recorder = AudioRecorder(app)

    val settings: StateFlow<AppSettings> = container.settings.state

    val recordings: StateFlow<List<RecordingEntity>> =
        repository.observeRecordings()
            .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private val _isRecording = MutableStateFlow(false)
    val isRecording: StateFlow<Boolean> = _isRecording.asStateFlow()

    /** One-shot user messages (errors / confirmations) for a snackbar. */
    private val _messages = MutableSharedFlow<String>(extraBufferCapacity = 4)
    val messages = _messages.asSharedFlow()

    fun startRecording() {
        if (_isRecording.value) return
        runCatching { recorder.start() }
            .onSuccess { _isRecording.value = true }
            .onFailure { emit("無法開始錄音:${it.message}") }
    }

    fun stopRecording() {
        if (!_isRecording.value) return
        val result = recorder.stop()
        _isRecording.value = false
        if (result == null) {
            emit("錄音太短或發生錯誤,未儲存。")
            return
        }
        viewModelScope.launch {
            val id = repository.addRecorded(result.file, result.durationMs)
            repository.transcribe(id)
        }
    }

    fun importFile(uri: Uri) {
        viewModelScope.launch {
            runCatching { repository.importFrom(uri) }
                .onSuccess { id ->
                    emit("已匯入,開始轉譯…")
                    repository.transcribe(id)
                }
                .onFailure { emit("匯入失敗:${it.message}") }
        }
    }

    /** Transcribe or retry a recording. */
    fun transcribe(id: String) {
        viewModelScope.launch { repository.transcribe(id) }
    }

    fun delete(id: String) {
        viewModelScope.launch { repository.delete(id) }
    }

    fun updateSettings(transform: (AppSettings) -> AppSettings) {
        container.settings.update(transform)
    }

    fun parseTranscript(entity: RecordingEntity?): Transcript? =
        repository.parseTranscript(entity?.transcriptJson)

    private fun emit(message: String) {
        viewModelScope.launch { _messages.emit(message) }
    }
}
