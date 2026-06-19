---
name: macos-voice-notes
description: "Configure local speech-to-text on macOS to save voice notes to markdown files. Covers Handy.app setup, external post-transcribe hooks, CLI integration, and config management."
tags: ["uncategorized"]
---

# macOS Voice Notes

Настройка локального распознавания речи (STT) на macOS для сохранения голосовых заметок в .md файл.

## Основной способ: VoiceNote.app (рекомендуется)

Нативное Swift приложение в меню-баре. Компилируется через `swiftc` (не требует Xcode, только Command Line Tools). Использует Apple SFSpeechRecognizer — встроенный, локальный, без скачивания моделей.

**Плюсы:**
- 0 зависимостей (только Apple frameworks)
- 140KB бинарник
- Не требует Accessibility доступа (использует Carbon API для хоткея)
- Сразу пишет в .md файл
- Меню-бар иконка + уведомления

**Минусы:**
- Качество SFSpeechRecognizer ниже, чем у Whisper/Canary
- Только один язык (можно сменить Locale)

### Компиляция

```bash
xcrun swiftc \
  -parse-as-library \
  -o "VoiceNote.app/Contents/MacOS/VoiceNote" \
  VoiceNoteApp.swift \
  -framework SwiftUI -framework AppKit -framework Speech \
  -framework AVFoundation -framework UserNotifications \
  -target arm64-apple-macos14.0
```

### Структура .app

```
VoiceNote.app/
  Contents/
    Info.plist    # CFBundleIdentifier, NSMicrophoneUsageDescription, etc.
    MacOS/
      VoiceNote   # compiled binary (swiftc output)
```

- LSUIElement не использовать — Carbon hotkey не работает с LSUIElement. Вместо этого: `NSApplication.shared.setActivationPolicy(.accessory)` в коде.
- Info.plist не должен содержать LSUIElement=true

### Хоткей (Carbon API)

Carbon `RegisterEventHotKey` работает **без Accessibility разрешения**, в отличие от CGEventTap.

```swift
var hotKeyId = EventHotKeyID(signature: 0x564E, id: 1)
let status = RegisterEventHotKey(
    UInt32(kVK_F5),           // keyCode
    UInt32(optionKey),        // modifiers (0, optionKey, cmdKey, shiftKey, controlKey)
    hotKeyId,
    GetApplicationEventTarget(),
    0,
    &hotKeyRef
)
```

**Обработчик:**
```swift
var eventType = EventTypeSpec(
    eventClass: OSType(kEventClassKeyboard),
    eventKind: UInt32(kEventHotKeyPressed)  // только keyDown
)
InstallEventHandler(
    GetApplicationEventTarget(),
    { _, _, refcon in ... return noErr },
    1, &eventType, selfPtr, nil
)
```

**Важно:**
- Carbon не ловит keyUp — только toggle (нажал/нажал), push-to-talk через Carbon невозможен
- На M1 Air кнопка верхнего ряда с микрофоном — аппаратная, а не F5. Для F5 использовать Fn+F5
- Option+F5 гарантированно работает на любой macOS
- Простой F5 (keyCode 96) может быть перехвачен системной диктовкой → отключить: `defaults write com.apple.HIToolbox AppleDictationEnabled -int 0`
- `setActivationPolicy(.accessory)` обязателен — иначе Carbon hotkey не регистрируется

### Распознавание (SFSpeechRecognizer)

```swift
let recognizer = SFSpeechRecognizer(locale: Locale(identifier: "ru-RU"))!
recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
recognitionRequest?.shouldReportPartialResults = true
recognitionRequest?.requiresOnDeviceRecognition = true

inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { buffer, _ in
    self.recognitionRequest?.append(buffer)
}

recognizer.recognitionTask(with: recognitionRequest!) { result, error in
    if let result = result, result.isFinal {
        let text = result.bestTranscription.formattedString
        // append to file
    }
}
```

### Полный код

См. `templates/VoiceNoteApp.swift` — полный исходник готового приложения.

### Разрешения

При первом запуске:
- Microphone — обязательно
- Speech Recognition — обязательно
- Accessibility **не нужен**

## Альтернатива: Handy.app

**Handy** — Rust + ONNX (com.pais.handy). NVIDIA Canary-1B локально. Push-to-talk.

### Конфиг
```
~/Library/Application Support/com.pais.handy/settings_store.json
```

### Перенаправление в .md файл через Handy

⚠️ `external_script_path` — Handy **НЕ запускает скрипт**. Поле игнорируется.
⚠️ `clipboard_handling: "copy"` — не влияет. Handy вставляет через Ctrl+V, не копирует в буфер.

✅ **Единственный рабочий метод:** мониторинг лога (`scripts/log-monitor.sh`)
Handy пишет в `~/Library/Logs/com.pais.handy/handy.log` строку `Transcription result: текст`.

## Carbon hotkey vs CGEventTap

| Метод | Требует Accessibility | keyUp | Примечание |
|-------|----------------------|-------|-----------|
| Carbon RegisterEventHotKey | Нет | Нет | Только keyDown. Не работает с LSUIElement. |
| CGEventTap | Да | Да | Полный контроль, push-to-talk. |
| NSEvent.addGlobalMonitor | Нет | Нет | Только mouse/flagsChanged. |

Всегда начинать с Carbon — не требует Accessibility, проще.

## Глобальный хоткей для SwiftUI MenuBarExtra

1. `setActivationPolicy(.accessory)` в init() — без дока, но с Carbon
2. Info.plist не должен содержать LSUIElement
3. Carbon — только toggle, не push-to-talk
4. Для push-to-talk (зажал/отпустил) — только CGEventTap + Accessibility
