package com.billyfan.meetingtranscriber.data

import android.content.Context
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.provider.OpenableColumns
import com.billyfan.meetingtranscriber.data.db.RecordingDao
import com.billyfan.meetingtranscriber.data.db.RecordingEntity
import com.billyfan.meetingtranscriber.data.model.RecordingStatus
import com.billyfan.meetingtranscriber.data.model.Transcript
import com.billyfan.meetingtranscriber.data.settings.SettingsStore
import com.billyfan.meetingtranscriber.stt.SttOptions
import com.billyfan.meetingtranscriber.stt.SttProviderFactory
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import java.io.File
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.UUID

/**
 * Single source of truth for recordings: persists rows, copies imported files into
 * app storage, and runs the transcription pipeline (provider call → normalize → save).
 *
 * Failure policy (per spec): a recording's audio is never deleted on transcription
 * failure — the row is marked FAILED and can be retried via [transcribe].
 */
class RecordingRepository(
    private val context: Context,
    private val dao: RecordingDao,
    private val settings: SettingsStore,
    private val providerFactory: SttProviderFactory,
    private val json: Json
) {
    fun observeRecordings(): Flow<List<RecordingEntity>> = dao.observeAll()

    suspend fun getById(id: String): RecordingEntity? = dao.getById(id)

    /** Register a just-finished recording and kick off no work yet. */
    suspend fun addRecorded(file: File, durationMs: Long): String {
        val entity = RecordingEntity(
            id = UUID.randomUUID().toString(),
            title = defaultTitle(),
            filePath = file.absolutePath,
            createdAt = System.currentTimeMillis(),
            durationMs = durationMs,
            status = RecordingStatus.RECORDED.name,
            providerId = settings.current.providerId,
            transcriptJson = null,
            errorMessage = null,
            imported = false
        )
        dao.upsert(entity)
        return entity.id
    }

    /** Copy an external audio file into app storage and register it as a recording. */
    suspend fun importFrom(uri: Uri): String = withContext(Dispatchers.IO) {
        val dir = File(context.filesDir, IMPORTS_DIR).apply { mkdirs() }
        val name = queryDisplayName(uri) ?: "import_${System.currentTimeMillis()}"
        val dest = File(dir, "${System.currentTimeMillis()}_$name")

        context.contentResolver.openInputStream(uri)?.use { input ->
            dest.outputStream().use { output -> input.copyTo(output) }
        } ?: throw IllegalStateException("無法讀取選取的檔案")

        val entity = RecordingEntity(
            id = UUID.randomUUID().toString(),
            title = "匯入:$name",
            filePath = dest.absolutePath,
            createdAt = System.currentTimeMillis(),
            durationMs = durationOf(dest),
            status = RecordingStatus.RECORDED.name,
            providerId = settings.current.providerId,
            transcriptJson = null,
            errorMessage = null,
            imported = true
        )
        dao.upsert(entity)
        entity.id
    }

    /** Transcribe (or retry) a recording. Updates status as it progresses. */
    suspend fun transcribe(id: String) {
        val rec = dao.getById(id) ?: return
        val current = settings.current
        val provider = providerFactory.create(current.providerId, current)

        dao.update(
            rec.copy(
                status = RecordingStatus.TRANSCRIBING.name,
                providerId = current.providerId,
                errorMessage = null
            )
        )
        try {
            val transcript = provider.transcribe(
                File(rec.filePath),
                SttOptions(languageCode = current.languageCode, diarize = current.diarize)
            )
            dao.update(
                rec.copy(
                    status = RecordingStatus.DONE.name,
                    providerId = current.providerId,
                    transcriptJson = json.encodeToString(Transcript.serializer(), transcript),
                    errorMessage = null
                )
            )
        } catch (e: Exception) {
            // Keep the audio file; only mark the row failed so the user can retry.
            dao.update(
                rec.copy(
                    status = RecordingStatus.FAILED.name,
                    errorMessage = e.message ?: "轉譯失敗"
                )
            )
        }
    }

    suspend fun delete(id: String) {
        val rec = dao.getById(id) ?: return
        // Never touch the original of an imported file; only delete copies we own.
        runCatching { File(rec.filePath).takeIf { it.exists() }?.delete() }
        dao.delete(rec)
    }

    fun parseTranscript(jsonStr: String?): Transcript? =
        jsonStr?.let { runCatching { json.decodeFromString(Transcript.serializer(), it) }.getOrNull() }

    private fun durationOf(file: File): Long = runCatching {
        // MediaMetadataRetriever is AutoCloseable only on API 29+, so release() manually.
        val mmr = MediaMetadataRetriever()
        try {
            mmr.setDataSource(file.absolutePath)
            mmr.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)?.toLong() ?: 0L
        } finally {
            mmr.release()
        }
    }.getOrDefault(0L)

    private fun queryDisplayName(uri: Uri): String? =
        context.contentResolver.query(uri, null, null, null, null)?.use { cursor ->
            val idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
            if (idx >= 0 && cursor.moveToFirst()) cursor.getString(idx) else null
        }

    private fun defaultTitle(): String =
        "會議 " + SimpleDateFormat("MM/dd HH:mm", Locale.getDefault()).format(System.currentTimeMillis())

    private companion object {
        const val IMPORTS_DIR = "imports"
    }
}
