package com.billyfan.meetingtranscriber.recording

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import java.io.File

/**
 * Minimal single-file recorder for M1: AAC in an .m4a container, 16 kHz mono —
 * the STT "sweet spot" that keeps long-meeting files small.
 *
 * M2 will move capture into a foreground service for long, screen-off recording.
 */
class AudioRecorder(private val context: Context) {

    private var recorder: MediaRecorder? = null
    private var outputFile: File? = null
    private var startedAtMs: Long = 0L

    val isRecording: Boolean get() = recorder != null

    /** Begin capturing. Returns the destination file. Caller must hold RECORD_AUDIO. */
    fun start(): File {
        check(recorder == null) { "Recorder already running" }

        val dir = File(context.filesDir, RECORDINGS_DIR).apply { mkdirs() }
        val file = File(dir, "rec_${System.currentTimeMillis()}.m4a")

        @Suppress("DEPRECATION")
        val r = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            MediaRecorder()
        }
        r.setAudioSource(MediaRecorder.AudioSource.MIC)
        r.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        r.setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        r.setAudioSamplingRate(16_000)
        r.setAudioChannels(1)
        r.setAudioEncodingBitRate(48_000)
        r.setOutputFile(file.absolutePath)
        r.prepare()
        r.start()

        recorder = r
        outputFile = file
        startedAtMs = System.currentTimeMillis()
        return file
    }

    /** Stop capturing. Returns the finished file and its duration in ms, or null on error. */
    fun stop(): Result? {
        val file = outputFile
        val durationMs = System.currentTimeMillis() - startedAtMs
        return try {
            recorder?.apply {
                stop()
                release()
            }
            if (file != null) Result(file, durationMs) else null
        } catch (e: Exception) {
            // A too-short or failed recording leaves a corrupt file; drop it.
            file?.delete()
            null
        } finally {
            recorder = null
            outputFile = null
        }
    }

    data class Result(val file: File, val durationMs: Long)

    companion object {
        const val RECORDINGS_DIR = "recordings"
    }
}
