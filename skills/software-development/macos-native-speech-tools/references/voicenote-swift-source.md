# VoiceNoteApp.swift — Complete Source

A minimal macOS menu bar app for voice notes. Compiles with swiftc, no Xcode needed.

## Key Design Decisions

- **Carbon hotkey (F5)** — no Accessibility permission required
- **No LSUIElement** — use `setActivationPolicy(.accessory)` instead (Carbon hotkeys break with LSUIElement)
- **SFSpeechRecognizer** — on-device, offline, Russian
- **Appends to ~/Handy_Voice_Notes.md**
- **~140KB binary**, ~170MB RSS at runtime

## Full Source

```swift
// VoiceNoteApp.swift
import SwiftUI
import AppKit
import Speech
import AVFoundation
import UserNotifications
import Carbon

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
            .keyboardShortcut("o", modifiers: .command)
            Divider()
            Button("Exit") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q", modifiers: .command)
        } label: {
            Image(systemName: service.isRecording ? "waveform.badge.mic" : "mic.fill")
                .foregroundStyle(service.isRecording ? .red : .primary)
        }
    }
}

@MainActor
class VoiceNoteService: ObservableObject {
    @Published var isRecording = false
    
    private let audioEngine = AVAudioEngine()
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let recognizer: SFSpeechRecognizer
    private var hotKeyRef: EventHotKeyRef?
    
    let notesPath: String
    
    init() {
        let locale = Locale(identifier: "ru-RU")
        self.recognizer = SFSpeechRecognizer(locale: locale) ?? SFSpeechRecognizer()!
        self.notesPath = NSHomeDirectory() + "/Handy_Voice_Notes.md"
        
        if !FileManager.default.fileExists(atPath: notesPath) {
            FileManager.default.createFile(atPath: notesPath, contents: nil)
        }
        
        requestPermissions()
        setupCarbonHotkey()  // CALL SYNCHRONOUSLY — not in DispatchQueue.main.async
        setupNotifications()
    }
    
    private func requestPermissions() {
        SFSpeechRecognizer.requestAuthorization { _ in }
    }
    
    private func setupNotifications() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert]) { _, _ in }
    }
    
    private func setupCarbonHotkey() {
        var hotKeyId = EventHotKeyID(signature: 0x564E, id: 1)
        let status = RegisterEventHotKey(
            UInt32(kVK_F5),   // F5 key code
            0,                 // no modifiers
            hotKeyId,
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )
        
        if status != noErr {
            print("VoiceNote: Hotkey registration failed (error \(status))")
            return
        }
        
        var eventType = EventTypeSpec(
            eventClass: OSType(kEventClassKeyboard),
            eventKind: UInt32(kEventHotKeyPressed)
        )
        
        let selfPtr = Unmanaged.passUnretained(self).toOpaque()
        
        InstallEventHandler(
            GetApplicationEventTarget(),
            { _, _, refcon in
                let service = Unmanaged<VoiceNoteService>.fromOpaque(refcon!).takeUnretainedValue()
                DispatchQueue.main.async {
                    if service.isRecording {
                        service.stopRecording()
                    } else {
                        service.startRecording()
                    }
                }
                return noErr
            },
            1,
            &eventType,
            selfPtr,
            nil
        )
        
        print("VoiceNote: Hotkey F5 registered via Carbon")
    }
    
    func toggleRecording() {
        if isRecording { stopRecording() } else { startRecording() }
    }
    
    func startRecording() {
        guard !isRecording else { return }
        
        let inputNode = audioEngine.inputNode
        let recordingFormat = inputNode.outputFormat(forBus: 0)
        
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        recognitionRequest?.shouldReportPartialResults = true
        recognitionRequest?.requiresOnDeviceRecognition = true
        
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
            self.recognitionRequest?.append(buffer)
        }
        
        audioEngine.prepare()
        try? audioEngine.start()
        
        isRecording = true
    }
    
    func stopRecording() {
        guard isRecording else { return }
        
        isRecording = false
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        
        recognitionTask = recognizer.recognitionTask(with: recognitionRequest!) { [self] result, error in
            if let result = result, result.isFinal {
                let text = result.bestTranscription.formattedString
                appendToFile(text)
                showNotification(text)
                self.recognitionTask?.cancel()
                self.recognitionTask = nil
                self.recognitionRequest = nil
            }
            if let error = error {
                print("VoiceNote: Error: \(error.localizedDescription)")
                self.recognitionTask?.cancel()
                self.recognitionTask = nil
                self.recognitionRequest = nil
            }
        }
    }
    
    private func appendToFile(_ text: String) {
        guard !text.isEmpty else { return }
        let date = DateFormatter()
        date.dateFormat = "yyyy-MM-dd HH:mm:ss"
        let timestamp = date.string(from: Date())
        let entry = "\n## \(timestamp)\n\n\(text)\n"
        
        if let handle = FileHandle(forWritingAtPath: notesPath) {
            handle.seekToEndOfFile()
            if let data = entry.data(using: .utf8) {
                handle.write(data)
            }
            try? handle.close()
        }
    }
    
    private func showNotification(_ text: String) {
        let content = UNMutableNotificationContent()
        content.title = "Voice Note"
        content.body = String(text.prefix(100)) + (text.count > 100 ? "…" : "")
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
```

## Info.plist (NO LSUIElement — Carbon hotkeys break with it)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key><string>VoiceNote</string>
    <key>CFBundleIdentifier</key><string>com.username.voicenote</string>
    <key>CFBundleName</key><string>VoiceNote</string>
    <key>CFBundlePackageType</key><string>APPL</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>LSMinimumSystemVersion</key><string>14.0</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>VoiceNote uses mic for voice notes</string>
    <key>NSSpeechRecognitionUsageDescription</key>
    <string>VoiceNote uses on-device speech recognition</string>
</dict>
</plist>
```

## Build Command

```bash
APP_DIR="/Applications/VoiceNote.app"
mkdir -p "$APP_DIR/Contents/MacOS"

xcrun swiftc \
  -parse-as-library \
  -o "$APP_DIR/Contents/MacOS/VoiceNote" \
  VoiceNoteApp.swift \
  -framework SwiftUI \
  -framework AppKit \
  -framework Speech \
  -framework AVFoundation \
  -framework UserNotifications \
  -target arm64-apple-macos14.0

cp Info.plist "$APP_DIR/Contents/"
open "$APP_DIR"
```
