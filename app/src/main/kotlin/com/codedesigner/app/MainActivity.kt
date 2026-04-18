package com.codedesigner.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.codedesigner.app.ui.CodeDesignerApp
import com.codedesigner.app.ui.theme.CodeDesignerTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            CodeDesignerTheme {
                CodeDesignerApp()
            }
        }
    }
}
