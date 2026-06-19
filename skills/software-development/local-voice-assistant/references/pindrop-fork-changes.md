# Pindrop Fork — Adding "Save to File" Feature

## Goal

Add a toggle to Pindrop menu bar that saves each transcription to `~/Handy_Voice_Notes.md` in addition to (or instead of) pasting into the active window.

## Files Modified

### 1. `Pindrop/Services/SettingsStore.swift`

Add two `@AppStorage` properties after the existing ones:

```swift
@AppStorage("saveTranscriptToFile", store: SettingsStoreRuntime.appStorageStore)
var saveTranscriptToFile: Bool = false
@AppStorage("saveTranscriptFilePath", store: SettingsStoreRuntime.appStorageStore)
var saveTranscriptFilePath: String = "~/Handy_Voice_Notes.md"
```

### 2. `Pindrop/AppCoordinator.swift`

**A)** Add callback wiring after `onToggleOutputMode`:

```swift
self.statusBarController.onToggleSaveToFile = { [weak self] in
    self?.handleToggleSaveToFile()
}
self.statusBarController.onSaveToFileStatus = { [weak self] in
    self?.settingsStore.saveTranscriptToFile ?? false
}
```

**B)** Add the file-save block after `outputSucceeded = true` in the transcription output pipeline:

```swift
try await outputManager.output(outputText)
outputSucceeded = true

// Save transcript to file if enabled
if settingsStore.saveTranscriptToFile {
    let filePath = (settingsStore.saveTranscriptFilePath as NSString).expandingTildeInPath
    let date = DateFormatter()
    date.dateFormat = "yyyy-MM-dd HH:mm:ss"
    let timestamp = date.string(from: Date())
    let entry = "\n## \(timestamp)\n\n\(finalText)\n"
    if let handle = FileHandle(forWritingAtPath: filePath) {
        handle.seekToEndOfFile()
        if let data = entry.data(using: .utf8) {
            handle.write(data)
        }
        try? handle.close()
    }
}
```

Use `finalText` (not `outputText` which may have trailing space). Appends with markdown `## timestamp` header.

**C)** Add handler method:

```swift
private func handleToggleSaveToFile() {
    settingsStore.saveTranscriptToFile.toggle()
    let status = settingsStore.saveTranscriptToFile ? "On" : "Off"
    let path = (settingsStore.saveTranscriptFilePath as NSString).expandingTildeInPath
    Log.app.info("Save to file: \(status), path: \(path)")
}
```

### 3. `Pindrop/UI/StatusBarController.swift`

**A)** Add property:

```swift
private var saveToFileItem: NSMenuItem?
```

**B)** Add callbacks:

```swift
var onToggleSaveToFile: (() -> Void)?
var onSaveToFileStatus: (() -> Bool)?
```

**C)** Add menu item in `setupMenu()` after `aiEnhancementItem`:

```swift
// Save to File
let saveToFileStatus = onSaveToFileStatus?() ?? false
let saveToFileLabel = saveToFileStatus
    ? localized("On", locale: locale)
    : localized("Off", locale: locale)
saveToFileItem = NSMenuItem(
    title: String(format: localized("Save to File: %@", locale: locale), saveToFileLabel),
    action: #selector(toggleSaveToFile),
    keyEquivalent: ""
)
saveToFileItem?.target = self
saveToFileItem?.image = NSImage(systemSymbolName: "doc.text", accessibilityDescription: nil)
menu.addItem(saveToFileItem!)
```

**D)** Add `@objc` handler:

```swift
@objc private func toggleSaveToFile() {
    onToggleSaveToFile?()
}
```

## Build Requirement

**Pindrop uses `.xcodeproj` format.** Building requires full Xcode.app (10+ GB). Command Line Tools + `xcodebuild` is NOT sufficient — it errors with:

```
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer directory
'/Library/Developer/CommandLineTools' is a command line tools instance
```

**Workaround:** Build on a Mac with Xcode installed, then copy the `.app` bundle. If the build Mac is on a different network, transfer via Thunderbolt Bridge, AirDrop, or USB.

## Verification

1. Build and run the app
2. Click menu bar icon → "Save to File: Off" should appear
3. Toggle it → should show "On"
4. Make a dictation → check `~/Handy_Voice_Notes.md` for the entry with timestamp
5. Toggle back to "Off" → dictation should only paste to active window, not append to file

## Notes

- The `onSaveToFileStatus` callback is polled each time the menu opens (since `setupMenu()` rebuilds the entire menu from scratch)
- File path is hardcoded to `~/Handy_Voice_Notes.md` by default. The path can be changed via `saveTranscriptFilePath` @AppStorage
- The file is created on first append if it doesn't exist (FileHandle creates, but it's safer to `touch` it during init)
