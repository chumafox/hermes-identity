# Handy.app Configuration Reference

**Bundle ID:** com.pais.handy
**Path:** `/Applications/Handy.app`
**Config:** `~/Library/Application Support/com.pais.handy/settings_store.json`
**Logs:** `~/Library/Logs/com.pais.handy/handy.log`
**DB:** `~/Library/Application Support/com.pais.handy/history.db`
**Recordings:** `~/Library/Application Support/com.pais.handy/recordings/`
**Models:** `~/Library/Application Support/com.pais.handy/models/`

## Key settings (settings_store.json)

```json
{
  "settings": {
    "always_on_microphone": false,
    "app_language": "ru",
    "autostart_enabled": true,
    "bindings": {
      "cancel": { "current_binding": "escape" },
      "transcribe": { "current_binding": "option_left+space" },
      "transcribe_with_post_process": { "current_binding": "option+shift+space" }
    },
    "external_script_path": "/Users/jenyanovak/.handy-post-transcribe.sh",
    "paste_method": "ctrl_v",
    "clipboard_handling": "dont_modify",
    "selected_language": "ru",
    "selected_model": "canary-1b-v2",
    "push_to_talk": true
  }
}
```

## CLI usage

```bash
# Toggle transcription
/Applications/Handy.app/Contents/MacOS/Handy --toggle-transcription

# Toggle with post-processing
/Applications/Handy.app/Contents/MacOS/Handy --toggle-post-process

# Cancel
/Applications/Handy.app/Contents/MacOS/Handy --cancel

# Start hidden
/Applications/Handy.app/Contents/MacOS/Handy --start-hidden

# Debug mode
/Applications/Handy.app/Contents/MacOS/Handy --debug
```

## Post-transcribe note saving

### ⚠️ external_script_path does NOT work
Handy ignores `external_script_path`. The script is never executed after transcription.
`clipboard_handling: "copy"` also has no effect — Handy always uses CtrlV paste, never copies to clipboard.

### ✅ Working method: log monitor
Monitor the Handy log file in real-time. See `scripts/log-monitor.sh` in this skill.

```bash
# Start monitor (foreground)
bash ~/.handy-log-monitor.sh

# Start in background
bash ~/.handy-log-monitor.sh &

# Output file: ~/Handy_Voice_Notes.md
```

The monitor watches `~/Library/Logs/com.pais.handy/handy.log` via `tail -F`,
parses `Transcription result:` lines, and appends text with timestamps to the .md file.

**Must be started BEFORE recording.**
