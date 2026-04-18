package com.codedesigner.app.ui

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.window.layout.FoldingFeature
import androidx.window.layout.WindowInfoTracker
import kotlinx.coroutines.flow.map

@Composable
fun CodeDesignerApp() {
    val context = LocalContext.current
    val activity = context as? ComponentActivity

    val layoutInfoFlow = remember(activity) {
        activity?.let { WindowInfoTracker.getOrCreate(it).windowLayoutInfo(it) }
    }
    val foldingFeature by (layoutInfoFlow
        ?.map { info -> info.displayFeatures.filterIsInstance<FoldingFeature>().firstOrNull() }
        ?: kotlinx.coroutines.flow.flowOf(null))
        .collectAsState(initial = null)

    val isUnfolded = foldingFeature?.state == FoldingFeature.State.FLAT ||
        foldingFeature?.state == FoldingFeature.State.HALF_OPENED

    var selectedFile by remember { mutableStateOf("index.html") }
    var editorContent by remember {
        mutableStateOf(
            """
            <!doctype html>
            <html>
              <body>
                <h1>Hello from Code Designer</h1>
              </body>
            </html>
            """.trimIndent()
        )
    }

    Scaffold { padding ->
        Surface(modifier = Modifier.fillMaxSize().padding(padding)) {
            if (isUnfolded) {
                UnfoldedLayout(
                    selectedFile = selectedFile,
                    onSelectFile = { selectedFile = it },
                    editorContent = editorContent,
                    onEditorChange = { editorContent = it },
                )
            } else {
                FoldedLayout(
                    selectedFile = selectedFile,
                    onSelectFile = { selectedFile = it },
                    editorContent = editorContent,
                    onEditorChange = { editorContent = it },
                )
            }
        }
    }
}

@Composable
private fun UnfoldedLayout(
    selectedFile: String,
    onSelectFile: (String) -> Unit,
    editorContent: String,
    onEditorChange: (String) -> Unit,
) {
    Row(modifier = Modifier.fillMaxSize()) {
        Box(modifier = Modifier.width(240.dp).fillMaxSize()) {
            FileTreePane(selectedFile = selectedFile, onSelectFile = onSelectFile)
        }
        Box(modifier = Modifier.weight(1f).fillMaxSize()) {
            EditorPane(content = editorContent, onChange = onEditorChange)
        }
        Box(modifier = Modifier.weight(1f).fillMaxSize()) {
            PreviewPane(html = editorContent)
        }
    }
}

@Composable
private fun FoldedLayout(
    selectedFile: String,
    onSelectFile: (String) -> Unit,
    editorContent: String,
    onEditorChange: (String) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        Box(modifier = Modifier.fillMaxSize().weight(1f)) {
            EditorPane(content = editorContent, onChange = onEditorChange)
        }
        Spacer(modifier = Modifier.width(0.dp))
        Box(modifier = Modifier.fillMaxSize().weight(1f)) {
            PreviewPane(html = editorContent)
        }
    }
}
