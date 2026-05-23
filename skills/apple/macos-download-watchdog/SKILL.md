---
name: macos-download-watchdog
description: |
  Monitor stalled downloads from desktop apps (LM Studio, browsers) on
  macOS and automatically resume them via their CLI or accessibility API.
  Covers nettopt/lsof network monitoring, .part file tracking, and
  app-specific CLI resume commands.
version: 1.0.0
platforms: [macos]
---

# macOS Download Watchdog

Monitor and automatically resume stalled file downloads on macOS.

## Quick network activity check

```bash
# Top bandwidth consumers (real-time)
nettop -m tcp -J bytes_in -t wifi -l 1 2>/dev/null | head -40

# Established TCP connections with remote IPs
lsof -iTCP -sTCP:ESTABLISHED -P -n 2>/dev/null | awk 'NR==1 || /->/' | head -30
```

## Detecting stalled downloads

### Step 1 — Find download-in-progress files

```bash
find ~/.lmstudio -name "*.part" -o -name "*.download" 2>/dev/null
find ~/Downloads -name "*.part" -o -name "*.download" -o -name "*.tmp" 2>/dev/null
```

Many apps use `.part` suffix for in-progress downloads. Track size changes:

```bash
watch -n 10 'stat -f "%z %Sm %N" ~/.lmstudio/**/*.part 2>/dev/null'
```

### Step 2 — Identify the downloading process

```bash
ps aux | grep -i "LM Studio" | grep -v grep
```

Cross-reference PIDs with `nettop` output to confirm which process is actively
transferring data.

## LM Studio download resume (primary pattern)

LM Studio 0.4.12+ ships a `lms` CLI at `~/.lmstudio/bin/lms` that handles
**resumable downloads** from Hugging Face Hub.

### Resume a stalled download

```bash
~/.lmstudio/bin/lms get "https://huggingface.com/ORG/MODEL" --yes --mlx
```

The `--yes` flag auto-accepts prompts. `--mlx` filters to MLX variants on Apple
Silicon. The `--gguf` flag works for GGUF models. If no format flag is given,
the system default for your hardware is used.

`lms get` will detect existing `.part` files and resume from where they left
off. It outputs a progress bar with MB/s and ETA.

### Check what's installed

```bash
~/.lmstudio/bin/lms ls
```

### Watchdog script (runs every 60s, restarts stalled downloads)

```bash
#!/bin/bash
MODEL_PATH="$HOME/.lmstudio/models/lmstudio-community/gemma-4-E4B-it-MLX-8bit"
LMS="$HOME/.lmstudio/bin/lms"
HF_URL="https://huggingface.co/lmstudio-community/gemma-4-E4B-it-MLX-8bit"

while true; do
  # Check if any .part files still exist (download not complete)
  PART_FILES=$(find "$MODEL_PATH" -name "*.part" 2>/dev/null)
  if [ -z "$PART_FILES" ]; then
    echo "Download complete. Exiting."
    exit 0
  fi

  # Check if download is actively running via lsof/netstat
  ACTIVE=$(lsof -iTCP -sTCP:ESTABLISHED -P -n 2>/dev/null | grep "lmstudio\|104.26\|172.67" | wc -l)
  if [ "$ACTIVE" -lt 2 ]; then
    echo "Download appears stalled. Restarting..."
    $LMS get "$HF_URL" --yes --mlx 2>&1 | head -3
  fi
  sleep 60
done
```

## Browsers and other apps

For Safari, Chrome, or other browsers — the browser CLI usually doesn't support
resume. Options:

1. **Kill and restart the browser** — it will resume HTTP downloads with
   `Range:` headers if the server supports it.
2. **Use `curl -C -`** for direct HTTP downloads:
   ```bash
   curl -C - -O "https://example.com/large-file.zip"
   ```
3. **Use `aria2c`** (install via brew) — supports multi-connection resume:
   ```bash
   brew install aria2
   aria2c -c "https://example.com/large-file.zip"
   ```

## AppleScript / Accessibility (if CLI unavailable)

If the app has no CLI, macOS Accessibility API can click "Resume" buttons:

```bash
osascript -e '
tell application "System Events"
  tell process "AppName"
    -- Click first button named "Resume"
    click (first button whose name contains "Resume")
  end tell
end tell
'
```

Requires **System Settings > Privacy & Security > Accessibility** permission
for Terminal (or the process running the script). Test with:

```bash
osascript -e 'tell application "System Events" to get name of every process'
```

If this fails with error -1728, the permission hasn't been granted yet.

## Pitfalls

- **`lms get` resolves downloads via LM Studio Hub registry.** Models from
  HuggingFace directly need the full `https://huggingface.co/...` URL.
  Short names like `org/model` look up LM Studio Hub which may not have the
  model registered.
- **`xcrun` errors** from macOS indicate Command Line Tools are missing/broken.
  Run `xcode-select --install` or download from Apple Developer site.
  In China, use mirrors or Apple's CDN directly.
- **Multiple simultaneous `lms get` calls** will conflict — the CLI detects
  "This download is already in progress" and shares the same progress tracker.
- **`.part` files are locked** by the downloading process; deleting them while
  the app is running may cause undefined behavior.
- **Sleep/Wake interruptions** often cause HTTP downloads to stall. The resume
  command re-establishes the TCP connection and sends `Range:` headers.
