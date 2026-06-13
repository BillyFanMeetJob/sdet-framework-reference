package com.billyfan.meetingtranscriber.data.model

/** Lifecycle of a single recording, surfaced in the list UI. */
enum class RecordingStatus {
    RECORDED,      // audio captured / imported, not yet transcribed
    TRANSCRIBING,  // request in flight
    DONE,          // transcript available
    FAILED         // transcription failed; audio is kept for retry
}
