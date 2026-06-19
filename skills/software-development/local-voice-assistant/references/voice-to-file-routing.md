# Voice-to-File Routing on macOS

How to get speech recognition output saved to a specific .md file (e.g. `~/Handy_Voice_Notes.md`) instead of being typed into the active window.

## Approaches Tested

### 1. Handy.app + Log Monitor (WORKING)

**Handy** (com.pais.handy) is a Rust/ONNX menu-bar dictation app using NVIDIA Canary 1B model. It writes transcription results to `~/Library/Logs/com.pais.handy/handy.log`.

**Log monitor script** — tail the log and append to file:

```bash
#!/bin/bash
LOG="$HOME/Library/Logs/com.pais.handy/handy.log"
FILE="$HOME/Handy_Voice_Notes.md"
touch "$FILE"

tail -F -n0 "$LOG" 2>/dev/null | while read -r line; do
    if echo "$line" | grep -q 'Transcription result:'; then
        TEXT=$(echo "$line" | sed -n 's/.*Transcription result: //p')
        if [ -n "$TEXT" ]; then
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
            printf "\n## %s\n\n%s\n" "$TIMESTAMP" "$TEXT" >> "$FILE"
        fi
    fi
done
```

**What did NOT work:**
- `external_script_path` in Handy's `settings_store.json` — Handy reads this setting but never invokes the script
- `clipboard_handling: "copy"` — Handy still uses Ctrl+V paste method, doesn't populate clipboard

**Pros:** Uses Handy's excellent Canary 1B model (Russian quality is very good). Zero changes to Handy.
**Cons:** Background process must run continuously (use LaunchAgent for autostart). Handy is closed-source, non-free.

**LaunchAgent for autostart (so monitor survives reboot):**
```bash
cat > ~/Library/LaunchAgents/com.user.handy-log-monitor.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.handy-log-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/handy-log-monitor.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
PLIST
launchctl load ~/Library/LaunchAgents/com.user.handy-log-monitor.plist
```

### 2. Apple Dictation + Shortcuts (PARTIAL)

macOS built-in Dictation (F5/Fn+F5) works system-wide. Attempted to chain into a Shortcut:

**Blocked:** macOS 14+ refuses to import unsigned `.shortcut` files. Creating shortcuts programmatically requires:
- Shortcuts.app GUI (user must build manually)
- Signed .shortcut via Apple Developer account
  - Using `shortcuts` CLI: only `run` and `list` commands, no `create`

**Workaround:** Build an Automator Quick Action (.workflow) that runs a script, but Automator doesn't have a "Dictate Text" action — only Shortcuts.app does.

**If user builds the Shortcut manually via Shortcuts.app GUI:**
1. New Shortcut → add "Dictate Text" (lang: Russian)
2. Add "Append to File" → `~/Handy_Voice_Notes.md`
3. Assign keyboard shortcut in System Settings → Keyboard → Shortcuts → Services

**Pros:** Zero dependencies, Apple-native.
**Cons:** Requires manual GUI setup. Dictation quality is lower than dedicated solutions.

### 3. Custom Swift MenuBar App (swiftc, no Xcode)

Build a minimal app with `swiftc` (no Xcode required). See `references/native-swift-voicenote-app.md` for full source.

```bash
xcrun swiftc \
  -parse-as-library \
  -o "/Applications/VoiceNote.app/Contents/MacOS/VoiceNote" \
  VoiceNoteApp.swift \
  -framework SwiftUI -framework AppKit -framework Speech -framework AVFoundation \
  -target arm64-apple-macos14.0
```

**Two hotkey approaches:**
- **CGEventTap** — needs Accessibility permission (System Settings → Privacy → Accessibility)
  - Supports push-to-talk (keyDown → start, keyUp → stop)
  - `CGEvent.tapCreate()` returns nil if permission denied — check return value
- **Carbon RegisterEventHotKey** — no Accessibility needed
  - Toggle only (keyDown fires, keyUp unreliable)
  - `RegisterEventHotKey()` returns status code — non-zero = already taken

### 4. Forking Existing Open-Source App (THEORETICAL)

Apps like Pindrop (watzon/pindrop) or TypeNo (marswaveai/TypeNo) can be forked to add file save:

**Pindrop** (Swift, xcodeproj):
- Add `@AppStorage("saveTranscriptToFile", ...)` + `@AppStorage("saveTranscriptFilePath", ...)` 
- After `outputManager.output(text)` in AppCoordinator.swift → `appendToFile(text)`
- Add menu bar toggle item in StatusBarController.swift
- **Requires:** Full Xcode.app (10+ GB) to build — `xcodebuild` doesn't work with CLI tools only

**For fork changes see:** `references/pindrop-fork-changes.md` (if created)

### 5. External Script + Clipboard Monitor (GENERIC)

For any app that copies text to clipboard (e.g. Handy with clipboard_handling, or any app that writes to clipboard):

```bash
#!/bin/bash
FILE="$HOME/Handy_Voice_Notes.md"
LAST=""

while true; do
    CURRENT=$(pbpaste)
    if [ "$CURRENT" != "$LAST" ] && [ -n "$CURRENT" ]; then
        # Check if this looks like a transcription (not a copy from elsewhere)
        # Simple heuristic: only capture if Handy/Pindrop process is running
        if pgrep -i "Handy" >/dev/null || pgrep -i "Pindrop" >/dev/null; then
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
            printf "\n## %s\n\n%s\n" "$TIMESTAMP" "$CURRENT" >> "$FILE"
            LAST="$CURRENT"
        fi
    fi
    sleep 2
done
```

**Pros:** Works with any dictation app.
**Cons:** Polling overhead, false positives from normal copy operations.
