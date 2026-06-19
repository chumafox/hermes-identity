---
name: macos-native-speech-tools
description: "Build lightweight macOS native speech-to-text apps and utilities using only Apple frameworks (SFSpeechRecognizer, AVFoundation, SwiftUI MenuBarExtra, Carbon hotkeys). No Xcode needed — compile with swiftc. Fully offline, Apple Silicon optimized."
tags: ["software-development"]
---

# macOS Native Speech-to-Text Tools

Build minimal, zero-dependency macOS apps for speech-to-text using only built-in Apple frameworks. These apps work entirely offline, use on-device recognition, and compile to ~140KB binaries with `swiftc` — no Xcode required.

## Architecture Pattern

```
MenuBarExtra (SwiftUI) → Carbon hotkey (global F-key shortcut) → AVAudioEngine (mic) → SFSpeechRecognizer (on-device) → append to .md file
```

## Hotkey Approaches — Comparison

| Method | Requires Accessibility | Works with LSUIElement | Reliable |
|--------|----------------------|----------------------|----------|
| **CGEventTap** | ✅ Yes | ✅ Yes | Falls back silently if no permission |
| **Carbon RegisterEventHotKey** | ❌ No | ❌ **Breaks with LSUIElement=true** | Reliable with `.accessory` activation policy |

**Rule:** If using Carbon hotkeys, do NOT set LSUIElement=true in Info.plist. Instead use:
```swift
@main
struct MyApp: App {
    init() {
        NSApplication.shared.setActivationPolicy(.accessory)
    }
    // ... MenuBarExtra body
}
```

This keeps the app out of the Dock but allows Carbon hotkeys to register.

## Quick Start — VoiceNote.app (reference implementation)

See `references/voicenote-swift-source.md` for the complete VoiceNoteApp.swift source — a minimal menu bar app that:
- Lives in the menu bar (🎤 icon)
- Global hotkey **F5** (toggle: press to record, press again to stop and transcribe)
- Uses **SFSpeechRecognizer** (Russian, on-device, offline)
- Appends text to `~/Handy_Voice_Notes.md`
- Shows notification on completion
- ~140KB binary

### Build

```bash
APP_DIR="/Applications/VoiceNote.app"
mkdir -p "$APP_DIR/Contents/MacOS"

xcrun swiftc \
  -parse-as-library \
  -o "$APP_DIR/Contents/MacOS/VoiceNote" \
  /path/to/VoiceNoteApp.swift \
  -framework SwiftUI \
  -framework AppKit \
  -framework Speech \
  -framework AVFoundation \
  -framework UserNotifications \
  -target arm64-apple-macos14.0

open "$APP_DIR"
```

### Info.plist — CRITICAL: do NOT use LSUIElement

```xml
<key>CFBundleIdentifier</key><string>com.username.voicenote</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<!-- LSUIElement must be ABSENT — Carbon hotkeys break with it -->
<!-- Use setActivationPolicy(.accessory) in code instead -->
<key>NSMicrophoneUsageDescription</key>
<string>VoiceNote uses mic for voice notes</string>
<key>NSSpeechRecognitionUsageDescription</key>
<string>VoiceNote uses on-device speech recognition</string>
```

## Core Components

### 1. Global Hotkey via Carbon API (no Accessibility needed)

```swift
import Carbon

private var hotKeyRef: EventHotKeyRef?

private func setupCarbonHotkey() {
    var hotKeyId = EventHotKeyID(signature: 0x564E, id: 1)
    let status = RegisterEventHotKey(
        UInt32(kVK_F5),            // keyCode (F5 = 96)
        0,                          // modifiers: 0 = no mods, optionKey for Option
        hotKeyId,
        GetApplicationEventTarget(),
        0,
        &hotKeyRef
    )
    guard status == noErr else { print("Hotkey failed: \(status)"); return }

    var eventType = EventTypeSpec(
        eventClass: OSType(kEventClassKeyboard),
        eventKind: UInt32(kEventHotKeyPressed)
    )
    let selfPtr = Unmanaged.passUnretained(self).toOpaque()
    
    InstallEventHandler(
        GetApplicationEventTarget(),
        { _, _, refcon in
            let service = Unmanaged<VoiceNoteService>.fromOpaque(refcon!).takeUnretainedValue()
            DispatchQueue.main.async { service.toggleRecording() }
            return noErr
        },
        1, &eventType, selfPtr, nil
    )
    
    print("VoiceNote: Hotkey registered via Carbon")
}
```

**Key codes:** F5=96, F6=97, F7=98, Space=49, Escape=53

**Modifiers:** `0` = no modifier, `optionKey`, `shiftKey`, `cmdKey`, `controlKey` (Carbon constants)

**CRITICAL:** Call `setupCarbonHotkey()` **synchronously** in `init()`, NOT inside `DispatchQueue.main.async`. Carbon event handler installation requires the main run loop to be set up but the RegisterEventHotKey call itself must happen synchronously before the first run loop iteration.

### 2. MenuBarExtra (SwiftUI, macOS 13+)

```swift
@main
struct VoiceNoteApp: App {
    @State private var service = VoiceNoteService()
    
    init() {
        NSApplication.shared.setActivationPolicy(.accessory)
    }
    
    var body: some Scene {
        MenuBarExtra {
            Button(service.isRecording ? "⏹ Stop" : "⏺ Record (F5)") {
                service.toggleRecording()
            }
            Divider()
            Button("📂 Open notes") {
                NSWorkspace.shared.open(URL(fileURLWithPath: service.notesPath))
            }
            Button("Exit") { NSApplication.shared.terminate(nil) }
        } label: {
            Image(systemName: service.isRecording ? "waveform.badge.mic" : "mic.fill")
        }
    }
}
```

### 3. SFSpeechRecognizer (on-device, no internet)

```swift
private let audioEngine = AVAudioEngine()
private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
private var recognitionTask: SFSpeechRecognitionTask?
private let recognizer: SFSpeechRecognizer

init() {
    let locale = Locale(identifier: "ru-RU")  // or "en-US", "de-DE", etc.
    self.recognizer = SFSpeechRecognizer(locale: locale) ?? SFSpeechRecognizer()!
    SFSpeechRecognizer.requestAuthorization { _ in }
}

func startRecording() {
    let inputNode = audioEngine.inputNode
    let recordingFormat = inputNode.outputFormat(forBus: 0)
    
    recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
    recognitionRequest?.shouldReportPartialResults = true
    recognitionRequest?.requiresOnDeviceRecognition = true  // KEY: offline
    
    inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
        self.recognitionRequest?.append(buffer)
    }
    audioEngine.prepare()
    try? audioEngine.start()
}

func stopRecording() {
    audioEngine.stop()
    audioEngine.inputNode.removeTap(onBus: 0)
    recognitionRequest?.endAudio()
    
    recognitionTask = recognizer.recognitionTask(with: recognitionRequest!) { result, error in
        if let result = result, result.isFinal {
            let text = result.bestTranscription.formattedString
            // save to file, show notification, etc.
        }
    }
}
```

### 4. Append to File

```swift
private func appendToFile(_ text: String) {
    guard !text.isEmpty else { return }
    let df = DateFormatter()
    df.dateFormat = "yyyy-MM-dd HH:mm:ss"
    let entry = "\n## \(df.string(from: Date()))\n\n\(text)\n"
    
    let path = NSHomeDirectory() + "/Handy_Voice_Notes.md"
    if !FileManager.default.fileExists(atPath: path) {
        FileManager.default.createFile(atPath: path, contents: nil)
    }
    if let handle = FileHandle(forWritingAtPath: path) {
        handle.seekToEndOfFile()
        if let data = entry.data(using: .utf8) { handle.write(data) }
        try? handle.close()
    }
}
```

## Permissions Required

| Permission | Info.plist key | Notes |
|-----------|---------------|-------|
| **Microphone** | `NSMicrophoneUsageDescription` | Prompts on first `AVAudioEngine.start()` |
| **Speech Recognition** | `NSSpeechRecognitionUsageDescription` | Prompts on first `recognitionTask` |
| **Accessibility** | Not needed | Carbon hotkeys work without it |

## References

- `references/voicenote-swift-source.md` — Full VoiceNoteApp.swift source code
- `templates/Info.plist` — Base Info.plist (WITHOUT LSUIElement)

## Pitfalls

### Build-time
- **swiftc requires `-parse-as-library`** with `@main` struct.
- **xcodebuild** requires full Xcode.app, not just Command Line Tools. Use `swiftc` for CLI-tools-only machines.
- Pindrop-style Xcode projects CANNOT be built without Xcode.app. Only single-file swiftc projects work.

### Hotkey
- **Carbon hotkeys BREAK with LSUIElement=true.** Use `setActivationPolicy(.accessory)` in code instead.
- **Carbon RegisterEventHotKey must be called synchronously** — NOT inside `DispatchQueue.main.async`. The install happens on the current thread; the event handler fires on the main run loop after that.
- **CGEventTap requires Accessibility permission** — if the user hasn't granted it, `CGEvent.tapCreate` returns nil silently. Always check the return value.
- **Some F-keys are intercepted by macOS** (F5 = Dictation, F11 = Show Desktop, F12 = Dashboard). Recommend Option+F5 or Cmd+F5 for reliability, or ask user to disable system shortcuts.
- **Fn modifier (push-to-talk)** is hardware-level on Mac keyboards — cannot be reliably captured in software. Use toggle mode (press/release) instead.

### Speech Recognition
- **SFSpeechRecognizer.requiresOnDeviceRecognition = true** must be set explicitly.
- **First recognition loads language model (~100ms-2s).** Subsequent recognitions are faster.
- **AVAudioSession does NOT exist on macOS** — remove all `try AVAudioSession.sharedInstance().setCategory(...)` calls when porting from iOS.
- **SFSpeechRecognizer** supports these locales on-device: ru-RU, en-US, de-DE, fr-FR, es-ES, zh-CN, ja-JP, ko-KR. Check `supportedLocales()` at runtime.

### File I/O
- **FileHandle(forWritingAtPath:) does NOT create the file** if it doesn't exist. Always call `FileManager.default.createFile(atPath:)` first.
- **Memory on M1 8GB:** VoiceNote.app uses ~70MB RSS + ~100MB language model = ~170MB. Acceptable for 8GB but monitor with `memory_pressure`.

### Third-party exploration
- **Handy** (`com.pais.handy`, closed-source, Rust): external_script_path in settings_store.json is recognized by the app but NEVER executes the script. clipboard_handling="copy" also has no effect. Only reliable approach is external log-monitoring (`tail -F` on handy.log, parsing "Transcription result:" lines).
- **Pindrop** (open-source, Swift): excellent codebase reference for architecture (OutputManager, HotkeyManager, SettingsStore patterns). Building requires Xcode.app, not CLI tools alone.

## Related Skills

- `local-siri` — Distributed voice assistant architecture (VAD + STT on display Mac, LLM + TTS on headless)
- `local-voice-assistant` — Full voice assistant with MLX Whisper + Ollama
