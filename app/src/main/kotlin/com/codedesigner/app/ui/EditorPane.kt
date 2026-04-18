package com.codedesigner.app.ui

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.OutlinedTextField
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun EditorPane(
    content: String,
    onChange: (String) -> Unit,
) {
    OutlinedTextField(
        value = content,
        onValueChange = onChange,
        modifier = Modifier.fillMaxSize().padding(8.dp),
    )
}
