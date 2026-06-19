---
name: macos-app-inspection
description: |
  Inspect a macOS .app bundle to find automation entry points —
  AppleScript, CDP, Accessibility API, network interception, config
  manipulation. Covers bundle analysis, Info.plist flags, Chromium
  detection, preference/config locations, network architecture
  tracing, and state-file inspection.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [macos, app-inspection, automation, reverse-engineering, chromium, apple-script]
    category: apple
    related_skills: [macos-computer-use, browser-content-extraction]
---

# macOS App Inspection for Automation

Use this skill when you need to programmatically interact with a macOS app
that doesn't have a documented API. The goal is to find a way in —
AppleScript, CDP, Accessibility, or direct HTTP.

## 1. Bundle Structure

Every macOS .app is a directory. Start here:

```bash
ls -la /path/to/App.app/Contents/
```

| Path | What to look for |
|------|-----------------|
| `Info.plist` | All automation flags (see below) |
| `MacOS/` | The actual binary |
| `Resources/` | script definitions, NIBs, assets |
| `PlugIns/` | XPC services |
| `Helpers/` | Sub-processes (renderers, utilities) |

## 2. Info.plist — Automation Flags

Parse with `plutil -p` or `cat | python3 -m json.tool`:

```bash
plutil -p /path/to/App.app/Contents/Info.plist
```

**Key flags:**

| Flag | What it means |
|------|--------------|
| `CFBundleSignature = "Cr24"` | **Chromium-based**. Likely supports CDP, has extension system, has `Local Storage/`, `Extensions/`, `Default/` profile dir |
| `NSAppleScriptEnabled = true` | AppleScript! Check for `OSAScriptingDefinition` path |
| `LSUIElement = "1"` | **LSUI (background only)** — no dock icon, no menu bar. Floating overlays, menu bar apps, agents |
| `LSBackgroundOnly = "1"` | True headless — no UI at all |
| `NSPrincipalClass = "BrowserCrApplication"` | Chromium app (uses BrowserCrApplication instead of NSApplication) |
| `OSAScriptingDefinition` | Path to `.sdef` file (relative to Resources/) |
| `CFBundleURLTypes[].CFBundleURLSchemes` | URL schemes the app registers (e.g., `doubao://`) |
| `NSMicrophoneUsageDescription` | Has voice input |
| `NSAudioCaptureUsageDescription` | Has audio recording |
| `NSCameraUsageDescription` | Has camera features |

**AppleScript check:**

```bash
# Check if .sdef file exists in Resources
ls /path/to/App.app/Contents/Resources/scripting.sdef 2>/dev/null

# If not found, check all .sdef and .applescript files
find /path/to/App.app -name '*.sdef' -o -name '*.applescript' 2>/dev/null
```

## 3. Chromium Detection & CDP

If `CFBundleSignature = "Cr24"` or `NSPrincipalClass = "BrowserCrApplication"`:

The app is Chromium-based. Check running processes for CDP:

```bash
ps aux | grep -i '<appname>' | grep 'remote-debugging-port'
```

If no CDP flag, you can relaunch with one (requires killing existing process):

```bash
# Kill first
pkill -f '<AppName>'

# Launch with remote debugging
/Applications/App.app/Contents/MacOS/App --remote-debugging-port=9223 &
```

**Chromium-specific paths** (under `~/Library/Application Support/<bundle-id>/`):

| Path | Contents |
|------|----------|
| `Default/` | User profile — Cookies, Local Storage, Bookmarks, History, Preferences, Login Data |
| `Default/Local Storage/leveldb/` | Web app local storage (leveldb format) |
| `Default/Bookmarks` | Bookmarks (JSON) — often contains the web app URL |
| `Default/Preferences` | Chromium preferences (JSON) |
| `Default/Cookies` | SQLite cookies — API tokens |
| `Default/Extensions/` | Installed Chrome extensions |
| `Local State` | Global Chromium state (JSON) |
| `Crashpad/` | Crash reports |

**Reading bookmarks for API endpoints:**

```python
python3 -c "
import json
with open('path/Bookmarks') as f:
    data = json.load(f)

def extract_urls(node, urls=[]):
    if isinstance(node, dict):
        if 'url' in node:
            urls.append(node['url'])
        for v in node.values():
            extract_urls(v, urls)
    elif isinstance(node, list):
        for v in node:
            extract_urls(v, urls)
    return urls

for u in extract_urls(data):
    print(u)
"
```

## 4. Config & Preferences Locations

| Type | Path | Format |
|------|------|--------|
| Preferences | `~/Library/Preferences/<bundle-id>.plist` | Binary plist |
| Application Support | `~/Library/Application Support/<bundle-id>/` | App-specific |
| Caches | `~/Library/Caches/<bundle-id>/` | Cache data |
| Saved State | `~/Library/Saved Application State/<bundle-id>.savedState/` | Window state |
| Containers | `~/Library/Containers/<bundle-id>/Data/` | Sandboxed apps only |
| Group Containers | `~/Library/Group Containers/<group-id>/` | Shared across apps |

```bash
# Fast search for app config dirs
ls ~/Library/Application\ Support/ | grep -i '<keyword>'
ls ~/Library/Preferences/ | grep -i '<bundle-id>'
```

## 5. Network Architecture Tracing

Trace how the app connects to the internet:

```bash
# Who has open TCP connections right now
lsof -i -P -n | grep -i '<appname>'

# What processes are listening
lsof -i -P -n | grep LISTEN

# Real-time per-process traffic monitoring
nettop -m tcp -P -n -s 2 -l 0
```

**Proxy chain detection:** Many Chinese apps route through local proxies.
Look for connections to `127.0.0.1:1080` (SOCKS5), `127.0.0.1:8888` (HTTP),
or other local proxy ports.

```bash
# Check if app uses local proxy
lsof -i -P -n | grep '127.0.0.1:1080\|127.0.0.1:8888'
```

**App-specific state files** often contain runtime status:

```bash
# Look for state JSON files in Application Support
find ~/Library/Application\ Support/<bundle-id>/ -name '*.state' -o -name '*_state' -o -name '*_status' 2>/dev/null
```

## 6. Electron / Asar Modification

Electron apps bundle their renderer code in a single archive file (`.asar`) inside `Contents/Resources/`. When you need to patch behavior (fix updater, change API endpoint, modify UI), use this workflow.

### 6.1 Locate the Asar

```bash
ls /path/to/App.app/Contents/Resources/*.asar
```

Electron apps can have one or more asar files. The main app code is usually `app.asar`.

### 6.2 Extract

```bash
npx asar e /path/to/App.app/Contents/Resources/app.asar /tmp/app-extract
```

### 6.3 Find the Code to Patch

Search for the behavior you want to change:

```bash
grep -r "checkForUpdates\|downloadUpdate\|update-error\|ERR_CONNECTION" /tmp/app-extract/out/ --include="*.js"
```

### 6.4 Patch and Repack

```bash
# Backup original first
cp /path/to/App.app/Contents/Resources/app.asar{,.bak}

# Edit, then repack
cd /tmp/app-extract && npx asar p . /path/to/App.app/Contents/Resources/app.asar
```

### 6.5 Re-Sign

Modifying the asar breaks the app's code signature. Re-sign ad-hoc:

```bash
codesign --remove-signature "/path/to/App.app"
codesign --sign - --force --deep "/path/to/App.app"
# Verify: no "Authority" lines, "TeamIdentifier=not set"
```

### 6.6 App Updates Overwrite Patches

When the app updates (via built-in updater or reinstall), the patched asar is replaced. Re-apply after update.

### 6.7 Common Electron App Paths

| Item | Path |
|------|------|
| App code | `Contents/Resources/app.asar` |
| Update config | `Contents/Resources/app-update.yml` |
| Updater logs | `~/Library/Application Support/<bundle-id>/logs/updater.log` |
| App data | `~/Library/Application Support/<bundle-id>/` |

### 6.8 Electron Updater Debugging

1. Check `updater.log` — `~/Library/Application Support/<bundle-id>/logs/updater.log`
2. Check `app-update.yml` — shows the GitHub repo (owner/repo)
3. **`net::ERR_CONNECTION_CLOSED`** — transient network failure. Fix: add retry with backoff to `checkForUpdates()` in the app's IPC handler (`out/main/index.js`)
4. **"Please check update first" cascade** — after failed check, `downloadUpdate()` enters dead state. Fix: make it call `checkForUpdates()` again before downloading
5. **Proxy** — Electron's `net` module ignores system proxy. Set `ELECTRON_HTTP_PROXY=socks5://127.0.0.1:1080` env var

### 6.9 Pitfalls

- Any byte change breaks code signature — always re-sign
- `npx asar` may need `npm install -g @electron/asar`
- App updates overwrite patches — save patch script for re-application
- Some apps have `app.asar` + `app.asar.unpacked/` — both may need modification

## 7. Hidden App Processes (LSUI/Background)

LSUIElement apps don't appear in the Dock. Find them via:

```bash
# All processes with accessibility/UI elements
ps aux | grep -v grep | grep -E 'Accessory|Agent|Helper|Menu'

# Check if a process is a background app
# LSUIElement apps won't have an icon in the Dock
# But they show in Activity Monitor and `ps aux`
```

## 8. Finding API Endpoints

Methods to discover backend API endpoints:

1. **Bookmarks** — Chromium apps store the main web app URL
2. **Cookies** — Check cookies SQLite DB for domain patterns
3. **Preferences** — Extract URLs with regex from Preferences JSON
4. **tcpdump** — Capture actual HTTPS traffic going through the proxy
5. **mitmproxy** — Set up transparent proxy to intercept API calls

```bash
# Extract URLs from Preferences JSON
python3 -c "
import json, re
d = json.load(open('path/Preferences'))
urls = re.findall(r'https?://[^\\'\"\\s,}]+', json.dumps(d))
for u in urls:
    if any(x in u for x in ['api','chat','graphql','v1','v2']):
        print(u)
"
```

## 9. Pitfalls

- **No CDP in production Chromium apps.** Most don't ship with
  `--remote-debugging-port`. You may need to kill and relaunch, which
  loses the user's session.
- **AppleScript .sdef file may not exist** even when `NSAppleScriptEnabled`
  is true — the Info.plist flag is aspirational.
- **Sandboxed apps** (Mac App Store) store data under
  `~/Library/Containers/<bundle-id>/Data/`, not directly in Application Support.
- **Binary plists** — use `plutil -convert json` or `plutil -p` for reading.
- **Chromium apps with multiple profiles** may have directories like
  `Profile 1/`, `Profile 2/` instead of `Default/`.
- **End-to-end encryption** — some apps (WeChat, WhatsApp) encrypt local
  storage. Traffic through their own tunnels won't show in lsof.
- **Voice-overlay apps** often have a separate "Accessory" process,
  launched with `--saman-from-chat=<pid>` flag (Doubao's internal name).
  The state file (e.g. `saman_app_state`) tracks visibility.
