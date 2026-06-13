package com.billyfan.meetingtranscriber

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.lifecycle.viewmodel.compose.viewModel
import com.billyfan.meetingtranscriber.ui.AppNavigation
import com.billyfan.meetingtranscriber.ui.MainViewModel
import com.billyfan.meetingtranscriber.ui.theme.MeetingTranscriberTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MeetingTranscriberTheme {
                val viewModel: MainViewModel = viewModel()
                AppNavigation(viewModel)
            }
        }
    }
}
