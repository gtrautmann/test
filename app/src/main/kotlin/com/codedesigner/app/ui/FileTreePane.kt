package com.codedesigner.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.ListItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

private val sampleFiles = listOf("index.html", "styles.css", "app.js")

@Composable
fun FileTreePane(
    selectedFile: String,
    onSelectFile: (String) -> Unit,
) {
    Column(modifier = Modifier.fillMaxSize().padding(8.dp)) {
        Text("Files")
        HorizontalDivider()
        sampleFiles.forEach { file ->
            ListItem(
                headlineContent = { Text(file) },
                modifier = Modifier,
                trailingContent = if (file == selectedFile) { { Text("●") } } else null,
            )
        }
    }
}
