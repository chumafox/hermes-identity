// VoiceNoteApp.swift — macOS menu-bar dictation app
// Saves voice notes to ~/Handy_Voice_Notes.md
// Compile: see SKILL.md
//
// SwiftUI + MenuBarExtra + Carbon hotkey + SFSpeechRecognizer
// No Accessibility required. No Xcode needed (swiftc).

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
        // .accessory — без дока, но с Carbon hotkey (LSUIElement ломает Carbon)
        NSApplication.shared.setActivationPolicy(.accessory)
    }

    var body: some Scene {
        MenuBarExtra {
            Button(service.isRecording ? "⏹ Остановить" : "⏺ Записать (Option+F5)") {
                service.toggleRecording()
            }
            Divider()
            Button("📂 Открыть заметки") {
                NSWorkspace.shared.open(URL(fileURLWithPath: service.notesPath))
            }
            .keyboardShortcut("o", modifiers: .command)
            Divider()
            Button("Выход") {
                NSApplication.shared.terminate(nil)
            }
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
        setupCarbonHotkey()
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
            UInt32(kVK_F5),
            UInt32(optionKey),  // Option+F5. Для F5 без модификаторов: 0
            hotKeyId,
            GetApplicationEventTarget(),
            0,
            &hotKeyRef
        )

        if status != noErr {
            print("VoiceNote: Failed to register hotkey (error \(status))")
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
                    service.toggleRecording()
                }
                return noErr
            },
            1,
            &eventType,
            selfPtr,
            nil
        )

        print("VoiceNote: Hotkey registered (Carbon)")
    }

    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
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
        content.title = "Голосовая заметка"
        content.body = String(text.prefix(100)) + (text.count > 100 ? "…" : "")
        let request = UNNotificationRequest(
            identifier: UUID().uuidString,
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
