# CLAUDE.md

Guidance for AI assistants working in this repository.

## Project Overview

**Code Designer** — a native Android code editor/designer targeting the Samsung Galaxy Z Fold 7 and other foldables. MVP features:

- File tree (left pane when unfolded)
- Code editor (center pane)
- Live HTML/CSS/JS preview via WebView (right pane)
- Fold-aware layout: three-pane split when unfolded, stacked editor + preview when folded

## Tech Stack

- **Language:** Kotlin
- **UI:** Jetpack Compose + Material 3
- **Foldable APIs:** `androidx.window` (`WindowInfoTracker`, `FoldingFeature`)
- **Preview:** `android.webkit.WebView` hosted in Compose via `AndroidView`
- **Min SDK:** 30 · **Target/Compile SDK:** 35
- **JVM target:** 17

## Repository Structure

```
.
├── build.gradle.kts              # Root Gradle config
├── settings.gradle.kts           # Module registration
├── gradle.properties             # Gradle + AndroidX flags
├── app/
│   ├── build.gradle.kts          # App module config
│   └── src/main/
│       ├── AndroidManifest.xml
│       ├── kotlin/com/codedesigner/app/
│       │   ├── MainActivity.kt
│       │   └── ui/
│       │       ├── CodeDesignerApp.kt    # Fold-aware root layout
│       │       ├── FileTreePane.kt
│       │       ├── EditorPane.kt
│       │       ├── PreviewPane.kt        # WebView-backed preview
│       │       └── theme/Theme.kt
│       └── res/values/            # strings.xml, themes.xml
└── CLAUDE.md
```

## Development Commands

Gradle wrapper is **not yet committed** — generate it once with a local Gradle install (`gradle wrapper --gradle-version 8.9`) before the commands below work.

- **Build debug APK:** `./gradlew :app:assembleDebug`
- **Install on connected device:** `./gradlew :app:installDebug`
- **Run unit tests:** `./gradlew test`
- **Run instrumented tests:** `./gradlew connectedAndroidTest`
- **Lint:** `./gradlew lint`
- **Clean:** `./gradlew clean`

## Architecture Notes

- `CodeDesignerApp` observes `WindowInfoTracker.windowLayoutInfo(activity)` and branches on the presence/state of a `FoldingFeature`.
  - **Unfolded (FLAT or HALF_OPENED):** three-column `Row` (file tree · editor · preview).
  - **Folded / no feature:** vertical `Column` with editor on top, preview below.
- State currently lives in `CodeDesignerApp` (`editorContent`, `selectedFile`) as plain `remember { mutableStateOf(...) }`. Promote to a `ViewModel` before adding persistence, multi-file editing, or undo history.
- `PreviewPane` re-renders on every keystroke via `AndroidView`'s `update` block. Debounce before this becomes a performance issue with larger documents.

## Conventions

- Package root: `com.codedesigner.app`; UI under `ui/`, theme under `ui/theme/`.
- Source directory: `app/src/main/kotlin/...` (not `java/`) — configured in `app/build.gradle.kts`.
- Prefer Material 3 components; use `material-icons-extended` for icons.
- Compose composables: `PascalCase`, no `@Composable` side effects outside `LaunchedEffect` / `remember`.
- Keep panes as focused, stateless composables that accept state + callbacks (already the pattern for `EditorPane`, `FileTreePane`, `PreviewPane`).

## Git Workflow

- Active development branch: `claude/add-claude-documentation-Iqz5u`.
- Commit focused, descriptive changes; never `--no-verify` without user approval.
- Do **not** open PRs automatically — wait for explicit user request.

## Known Gaps / Next Steps

- No Gradle wrapper committed yet.
- No syntax highlighting in `EditorPane` — currently a plain `OutlinedTextField`. Candidate libraries: [compose-richeditor](https://github.com/MohamedRejeb/compose-rich-editor) or a custom `visualTransformation`.
- File tree is a hardcoded sample list — no real filesystem/project abstraction yet.
- No persistence: editor contents reset on process death.
- No tests yet.
- Preview WebView is unsandboxed and loads via `loadDataWithBaseURL(null, ...)` — review before enabling JS or remote content.

## Notes for AI Assistants

- Prefer editing existing files over adding new ones; respect the pane-per-file layout already established.
- When adding a new editor capability, add the state to `CodeDesignerApp` (or a future `ViewModel`) and pass it down — don't reach into panes via singletons.
- Update this file alongside any change to structure, tooling, or conventions so it stays accurate.
