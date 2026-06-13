package com.billyfan.meetingtranscriber.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * A recording row. The transcript is stored as a JSON blob ([transcriptJson]) rather
 * than a relation — it's always read/written as a whole, so a blob keeps M1 simple.
 */
@Entity(tableName = "recordings")
data class RecordingEntity(
    @PrimaryKey val id: String,
    val title: String,
    val filePath: String,
    val createdAt: Long,
    val durationMs: Long,
    val status: String,
    val providerId: String,
    val transcriptJson: String?,
    val errorMessage: String?,
    /** True when [filePath] points at a user-imported file we must not delete. */
    val imported: Boolean = false
)
