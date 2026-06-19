# Native macOS VoiceNote App — SwiftUI + SFSpeechRecognizer

Minimal menu-bar app for push-to-talk voice transcription. Records speech, transcribes via Apple's on-device SFSpeechRecognizer, appends to `~/Handy_Voice_Notes.md`.

**Unlike the full local-voice-assistant:** no VAD, no LLM, no TTS, no Wake Word. Just record → transcribe → save. 146KB binary, ~72MB RAM, 0 dependencies.

## Source Code

Location: `~/.voice-note/VoiceNoteApp.swift` (single file)
App bundle: `/Applications/VoiceNote.app`

## Architecture

```
MenuBarExtra (SwiftUI) → VoiceNoteService
  ├── CGEventTap (global hotkey F5 with Option)
  │   ├── keyDown → startRecording()
  │   └── keyUp → stopRecording()
  ├── AVAudioEngine (microphone tap)
  ├── SFSpeechRecognizer (on-device, ru-RU)
  │   └── recognitionTask → appendToFile()
  └── FileHandle (append to ~/Handy_Voice_Notes.md)
```

## Key Code Patterns

### Menu-Bar Only App (no dock icon, no window)

```swift
@main
struct VoiceNoteApp: App {
    var body: some Scene {
        MenuBarExtra {
            Button("Записать") { service.toggleRecording() }
            Divider()
            Button("Выход") { NSApplication.shared.terminate(nil) }
        } label: {
            Image(systemName: isRecording ? "waveform.badge.mic" : "mic.fill")
        }
    }
}
```

**Info.plist:** Do NOT use `LSUIElement = true` — it breaks Carbon `RegisterEventHotKey` on macOS 14+. Instead, call `NSApplication.shared.setActivationPolicy(.accessory)` in the app's `init()`:

```swift
@main
struct VoiceNoteApp: App {
    @State private var service = VoiceNoteService()
    
    init() {
        NSApplication.shared.setActivationPolicy(.accessory)
    }
    // ...
}
```

This hides the dock icon while keeping Carbon hotkey registration working. Remove `LSUIElement` from Info.plist entirely.

### Push-to-Talk via CGEventTap (global hotkey)

```swift
let eventMask = (1 << CGEventType.keyDown.rawValue) | (1 << CGEventType.keyUp.rawValue)
let selfPtr = Unmanaged.passUnretained(self).toOpaque()

guard let tap = CGEvent.tapCreate(
    tap: .cgSessionEventTap,
    place: .headInsertEventTap,
    options: .defaultTap,
    eventsOfInterest: CGEventMask(eventMask),
    callback: { proxy, type, event, refcon in
        let service = Unmanaged<VoiceNoteService>.fromOpaque(refcon!).takeUnretainedValue()
        let keyCode = event.getIntegerValueField(.keyboardEventKeycode)
        
        if type == .keyDown {
            service.startRecording()
            return nil  // swallow event
        } else if type == .keyUp {
            service.stopRecording()
            return nil
        }
        return Unmanaged.passUnretained(event)
    },
    userInfo: selfPtr
) else {
    print("VoiceNote: No Accessibility access — CGEventTap.create failed")
    return
}

let runLoopSource = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
CFRunLoopAddSource(CFRunLoopGetCurrent(), runLoopSource, .commonModes)
```

**Key codes (macOS Virtual Key Codes):**
- F5 = 96
- Space = 49
- Return = 36
- Escape = 53

**Modifier flags:** `.maskCommand`, `.maskAlternate` (Option), `.maskControl`, `.maskShift`

**Requires:** System Settings → Privacy & Security → Accessibility — the app must be granted permission for CGEventTap. First call returns nil silently if denied.

### Alternative: Carbon RegisterEventHotKey (NO Accessibility needed)

If you want to avoid the Accessibility permission, use the older Carbon API. It registers a global hotkey without any special permissions:

```swift
import Carbon

var hotKeyRef: EventHotKeyRef?
var hotKeyId = EventHotKeyID(signature: 0x564E, id: 1) // "VN"

let status = RegisterEventHotKey(
    UInt32(kVK_F5),          // keyCode
    UInt32(optionKey),       // modifiers: cmdKey, optionKey, controlKey, shiftKey
    hotKeyId,
    GetApplicationEventTarget(),
    0,
    &hotKeyRef
)

// Handler for key pressed
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
    1,
    &eventType,
    selfPtr,
    nil
)
```

**Pitfalls:**
- `kEventHotKeyReleased` (key up) does NOT work reliably with Carbon — use toggle pattern (press to start, press again to stop) instead of push-to-talk
- Carbon hotkeys are system-wide and NOT swallowed — the event still reaches the active app
- `RegisterEventHotKey` can fail silently if the key combo is already taken (returns non-zero status). Check `status != noErr`.
- **F5 is captured by system Dictation** — On MacBooks, F5 triggers Dictation by default. Before using F5 as a hotkey, disable Dictation:
  ```bash
  defaults write com.apple.HIToolbox AppleDictationEnabled -int 0
  defaults write com.apple.symbolichotkeys AppleSymbolicHotKeys -dict-add 10 "{ enabled = 0; }"
  ```
  Alternative: use `Option+F5` (add `UInt32(optionKey)` modifier) to bypass system capture.
- Only supports simple modifier combinations (cmd/option/ctrl/shift + one key), no Fn
- **Push-to-talk vs toggle:** CGEventTap supports push-to-talk (hold to record, release to stop) with keyDown/keyUp events, but requires Accessibility permission. Carbon supports only toggle (press to start, press to stop) but needs NO Accessibility permission. User preference: push-to-talk.

### On-Device Speech Recognition

```swift
let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "ru-RU"))!
let request = SFSpeechAudioBufferRecognitionRequest()
request.shouldReportPartialResults = true
request.requiresOnDeviceRecognition = true  // force offline

// Wire to AVAudioEngine
audioEngine.inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
    request.append(buffer)
}

// Transcribe
let task = recognizer.recognitionTask(with: request) { result, error in
    if let result = result, result.isFinal {
        let text = result.bestTranscription.formattedString
        // save to file...
    }
}
```

**Pitfalls:**
- `requiresOnDeviceRecognition = true` — if model not downloaded, first call triggers download (~50MB, Russian). Subsequent calls are instant.
- Russian dictation model may not be installed by default on Mac. If SFSpeechRecognizer returns unavailable, open System Settings → Keyboard → Dictation and trigger a download by toggling Russian dictation on.
- `SFSpeechRecognizer.requestAuthorization { _ in }` must be called before first use.

### Compile with swiftc (no Xcode)

```bash
xcrun swiftc \
  -parse-as-library \
  -o "/Applications/VoiceNote.app/Contents/MacOS/VoiceNote" \
  VoiceNoteApp.swift \
  -framework SwiftUI \
  -framework AppKit \
  -framework Speech \
  -framework AVFoundation \
  -framework UserNotifications \
  -target arm64-apple-macos14.0
```

**Flags explained:**
- `-parse-as-library` — needed because `@main` attribute conflicts with top-level code in a single file
- `-target arm64-apple-macos14.0` — minimum deployment target. Change to `15.0` for newer APIs.
- Frameworks: include ALL frameworks used, even transitive ones (SwiftUI needs AppKit, etc.)

### Append to File

```swift
private func appendToFile(_ text: String) {
    let entry = "\n## \(timestamp)\n\n\(text)\n"
    if let handle = FileHandle(forWritingAtPath: notesPath) {
        handle.seekToEndOfFile()
        if let data = entry.data(using: .utf8) {
            handle.write(data)
        }
        try? handle.close()
    }
}
```

## App Bundle Structure

```
VoiceNote.app/
  Contents/
    Info.plist        # LSUIElement=true, NSMicrophoneUsageDescription, NSSpeechRecognitionUsageDescription
    MacOS/
      VoiceNote       # 146KB arm64 executable
```

## Permissions Required

| Permission | When | System Settings Path |
|---|---|---|
| Microphone | First startRecording() | Privacy → Microphone |
| Speech Recognition | First recognitionTask() | Privacy → Speech Recognition |
| Accessibility | First CGEventTap | Privacy → Accessibility |

## Notifications

Use `UserNotifications.framework` (not deprecated `NSUserNotification`):

```swift
import UserNotifications

let content = UNMutableNotificationContent()
content.title = "Голосовая заметка"
content.body = text
let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
UNUserNotificationCenter.current().add(request)
```
