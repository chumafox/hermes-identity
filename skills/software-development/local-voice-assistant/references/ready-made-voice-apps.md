# Ready-made Open-Source macOS Dictation / Voice Note Apps

GitHub alternatives for local, private speech-to-text on macOS. All free, open-source, and run entirely offline.

## TypeNo — marswaveai/TypeNo ★873

**Link:** https://github.com/marswaveai/TypeNo

Minimal voice input app. Press Ctrl to start recording, press again to stop — text is transcribed locally and pasted into the active app + clipboard.

- **Language:** Swift (SwiftUI)
- **Engine:** col (sherpa-onnx, via npm)
- **Hotkey:** Ctrl (short-press toggle)
- **Dependencies:** Node.js + `npm install -g @marswave/coli` + ffmpeg
- **macOS:** Any (not Silicon-specific)
- **Output:** Pastes into active app + copies to clipboard
- **Size:** ~100KB app binary, model downloads on first use
- **License:** MIT

**Pros:** Dead simple, zero config after setup, signed & notarized
**Cons:** Requires Node.js runtime for the STT engine, not pure native

## Pindrop — watzon/pindrop ★527

**Link:** https://github.com/watzon/pindrop

Menu bar dictation app using WhisperKit for local speech recognition. Pure Swift/SwiftUI, optimized for Apple Silicon.

- **Language:** Swift (SwiftUI, Swift Packages only)
- **Engine:** WhisperKit (Apple's CoreML-optimized Whisper, runs on ANE + GPU)
- **Hotkey:** Global (configurable)
- **Dependencies:** None (pure Swift/Xcode build)
- **macOS:** 14.0+, Apple Silicon
- **Output:** Pastes into active app
- **Size:** ~15MB app
- **License:** MIT

**Pros:** Pure native Swift, no external deps, optimized for Apple Silicon, best code quality
**Cons:** Requires Xcode to build (no prebuilt binary available from README), macOS 14+

## MacParakeet — moona3k/macparakeet ★299

**Link:** https://github.com/moona3k/macparakeet

Fast local voice app for Mac — system-wide dictation, file & YouTube transcription, meeting recording.

- **Language:** Swift (Swift 6)
- **Engine:** Parakeet TDT (Neural Engine optimized, by NVIDIA)
- **Hotkey:** Global (configurable)
- **Dependencies:** None (downloadable DMG)
- **macOS:** 14.2+, Apple Silicon
- **Output:** Pastes into active app + file transcription
- **License:** GPL-3.0
- **Download:** https://downloads.macparakeet.com/MacParakeet.dmg

**Pros:** Most feature-rich (dictation + file transcription + meeting recording), DMG download, Parakeet TDT is fast
**Cons:** GPL license, more heavyweight than needed for simple notes

## Comparison

| Feature | TypeNo | Pindrop | MacParakeet |
|---------|--------|---------|-------------|
| Stars | ★873 | ★527 | ★299 |
| Pure native? | ❌ (needs Node.js) | ✅ (Swift only) | ✅ (Swift only) |
| Prebuilt download | ✅ | ❌ | ✅ |
| macOS min | Any | 14.0 | 14.2 |
| Silicon optimized | ❌ | ✅ (ANE+GPU) | ✅ (ANE) |
| Save to file | ❌ (paste only) | ❌ (paste only) | ❌ (paste only) |
| Extra features | — | — | File/YouTube transcription |
| Best for | Quick voice typing | Privacy-first native | All-in-one transcription |
