---
name: chromium-app-automation
description: Reverse-engineer and automate Chromium-based desktop apps via CDP. Launch with remote debugging, inspect DOM, send input, read responses. Covers text chat, voice chat, and audio injection via BlackHole.
tags: [cdp, chromium, reverse-engineering, automation, websocket, audio-injection, blackhole]
---

# Chromium App Automation via CDP

Reverse-engineer and automate any Chromium-based desktop application (Doubao, 豆包, custom browsers, Electron apps, etc.) by launching with `--remote-debugging-port` and controlling via Chrome DevTools Protocol.

## When to use

- A desktop app is Chromium-based (check Info.plist for `CFBundleSignature = "Cr24"` or Chromium version strings)
- You need to send/receive messages from an app that has no API
- The app has a floating overlay, voice mode, or web-based UI
- The app is listed by `ps aux` with child renderer/GPU/network helper processes

## How to identify a Chromium-based app

```bash
# Check Info.plist for Chromium signature
grep -a "Cr24\|Chromium\|Chrome" /Applications/App.app/Contents/Info.plist

# Look for child processes: Renderer, GPU, NetworkService, etc.
ps aux | grep -i "appname" | grep -E "renderer|gpu|network|utility"
```

## Launch with CDP

```bash
# Kill existing instance
killall "AppName" 2>/dev/null
sleep 2

# Launch with remote debugging
"/Applications/AppName.app/Contents/MacOS/AppName" --remote-debugging-port=9223
```

The flag propagates to all child processes (Browser, Renderer, Accessory, etc.).

### Persistent CDP wrapper (browser always starts with CDP)

To make a browser ALWAYS launch with `--remote-debugging-port` (even when opened via Dock, Spotlight, or `open -a`), replace the binary with a shell wrapper:

```bash
cd /Applications/Brave\ Browser.app/Contents/MacOS/
sudo mv "Brave Browser" "Brave Browser.real"
sudo tee "Brave Browser" << 'WRAPPER'
#!/bin/bash
exec "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser.real" \
  --remote-debugging-port=9222 \
  "$@"
WRAPPER
sudo chmod +x "Brave Browser"
```

**Caveat:** Browser auto-updates may overwrite the wrapper. User should verify CDP still works after updates and re-apply if needed.

To revert:
```bash
cd /Applications/Brave\ Browser.app/Contents/MacOS/
sudo mv "Brave Browser.real" "Brave Browser"
```

## Discover available pages

```bash
curl -s http://127.0.0.1:9223/json | python3 -m json.tool
```

Each page has a `webSocketDebuggerUrl` (ws://...) for CDP interaction.

## Connect via WebSocket

**Critical: bypass proxy for localhost.** The `websockets` library respects HTTP_PROXY and will fail on localhost connections.

```bash
NO_PROXY="*" python3 << 'PYEOF'
import asyncio, json, websockets

WS = "ws://127.0.0.1:9223/devtools/page/<PAGE_ID>"

async def main():
    async with websockets.connect(WS, max_size=10_000_000) as ws:
        mid = [0]
        async def cdp(method, params=None):
            mid[0] += 1
            await ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
            return json.loads(await asyncio.wait_for(ws.recv(), 15))

        # Read page text
        r = await cdp('Runtime.evaluate', {
            'expression': 'document.body.innerText',
            'returnByValue': True
        })
        print(r['result']['result']['value'])

asyncio.run(main())
PYEOF
```

## Finding UI elements

### Method 1: Body text scan
```python
cdp('Runtime.evaluate', {'expression': 'document.body.innerText', 'returnByValue': True})
```

### Method 2: DOM query for interactable elements
```javascript
document.querySelectorAll('button, input, textarea, [role="button"], [contenteditable]')
```

### Method 3: SVG path analysis for icon-only buttons
SVG paths contain hints about icon type (phone, mic, settings, close). Use `getAttribute('d')` to grab path data.

### Method 4: Position-based (mouse coordinates)
```javascript
el.getBoundingClientRect()  // {x, y, width, height}
```
Click center: `x + width/2, y + height/2`

## Mouse input (click buttons)
```python
await cdp('Input.dispatchMouseEvent', {
    'type': 'mousePressed', 'x': X, 'y': Y,
    'button': 'left', 'clickCount': 1
})
await cdp('Input.dispatchMouseEvent', {
    'type': 'mouseReleased', 'x': X, 'y': Y,
    'button': 'left', 'clickCount': 1
})
```

## Keyboard input

### Method A: Focus + insertText (preferred for React/SPA apps)
```python
cdp('Runtime.evaluate', {'expression': 'document.querySelector("textarea").focus()'})
cdp('Input.insertText', {'text': 'message text'})
```

### Method B: Dispatch key events
```python
cdp('Input.dispatchKeyEvent', {
    'type': 'rawKeyDown', 'windowsVirtualKeyCode': 13,
    'key': 'Enter', 'code': 'Enter'
})
cdp('Input.dispatchKeyEvent', {
    'type': 'keyUp', 'windowsVirtualKeyCode': 13,
    'key': 'Enter', 'code': 'Enter'
})
```

## Reading chat responses
```python
cdp('Runtime.evaluate', {'expression': 'document.body.innerText', 'returnByValue': True})
```
The full conversation (user + AI messages) appears in innerText.

**⚠️ Voice chat timing trap:** When polling the voice chat transcript after audio injection, the FIRST new line is the user's ASR-transcribed speech, not the AI response. The AI response appears as 1+ subsequent lines. **Do NOT rely on a fixed "wait for 2+ new lines" check** — the AI may respond in English (1 line) or Chinese (1+ lines). Instead, use **stability-based polling**: wait until the transcript has no changes for 2 consecutive seconds, then return the last new line. This handles both EN and ZH responses, and filters out late-appearing dialog text ("挂断通话", "⌥+Q", etc.).

```python
NOISE = {"正在听...", "打断豆包", "复制", "请开始说话",
         "回答字幕将显示在这里", "挂断通话"}  # 挂断通话 = late dialog text
prev = cdp_read_body(vid)
stable = 0
last = ""
for i in range(30):
    await asyncio.sleep(1)
    body = cdp_read_body(vid)
    if body == prev:
        stable += 1
        if stable >= 2 and last:          # 2s stable → AI done speaking
            return last                    # return the last new line
        continue
    stable = 0
    lines = [l.strip() for l in body.split("\n")
             if l.strip() and l.strip() not in NOISE]
    old = set(l.strip() for l in prev.split("\n")
              if l.strip() and l.strip() not in NOISE)
    new = [l for l in lines if l not in old]
    if new:
        last = new[-1]                     # track most recent new line
        prev = body
return ""  # timeout
```

See `references/doubao-transcript-parsing-pitfalls.md` and the template `templates/doubao-web-bridge-server.py` for a complete implementation.

## Voice chat mode
Voice chat pages typically:
- Show "请开始说话" (please start speaking) before activation
- Show "正在听..." (listening...) when mic is active
- **No visible buttons** — pure WebRTC audio stream
- Transcriptions appear live in `document.body.innerText`
- Can be closed by clicking the SVG hang-up icon found via position

No `audio` or `canvas` elements — audio goes directly to the server via WebRTC.

## Audio injection via virtual audio device

For Chromium-based voice chat apps (Doubao voice, web call interfaces, etc.), you can inject audio by using a virtual audio loopback device.

### Prerequisites

```bash
brew install blackhole-2ch       # Virtual audio driver (creates loopback device)
brew install switchaudio-osx      # CLI for switching audio input device
brew install ffmpeg               # Audio playback into BlackHole
```

### Audio devices on this Mac

| Device | Type | Purpose |
|--------|------|---------|
| BlackHole 2ch (ID:58) | Virtual | Input for injection, Output for receiving |
| MacBook Air Microphone (ID:113) | Built-in | Normal microphone |
| Jenya Microphone (ID:118) | Custom | Additional mic |

### Workflow

```bash
# 1. Switch system default input to BlackHole
SwitchAudioSource -s "BlackHole 2ch" -t input

# 2. Open voice chat (via CDP, click phone button)
# The voice chat's getUserMedia() will now read from BlackHole

# 3. Play audio INTO BlackHole — it appears as mic input
# NOTE: Use -f audiotoolbox (output muxer), NOT -f avfoundation (input only)
ffmpeg -i /path/to/audio.aiff -f audiotoolbox -audio_device_index 0 ""

# 4. Read voice chat transcript via CDP
cdp('Runtime.evaluate', {'expression': 'document.body.innerText', 'returnByValue': True})

# 5. Restore microphone
SwitchAudioSource -s "MacBook Air Microphone" -t input
```

### SwitchAudioSource commands

```bash
SwitchAudioSource -a -t input                  # list input devices
SwitchAudioSource -c -t input                  # current input device
SwitchAudioSource -s "BlackHole 2ch" -t input  # set BlackHole as input
SwitchAudioSource -s "MacBook Air Microphone" -t input  # set mic as input
SwitchAudioSource -n -t input                  # cycle to next input
```

### Script: doubao-inject

A complete automation script lives at `~/bin/doubao-inject` (also in `scripts/doubao-inject.sh`). It wraps the full workflow:

```
doubao-inject start           — BlackHole + open voice chat via CDP
doubao-inject stop            — close voice chat + restore mic
doubao-inject tts "text"     — TTS + inject via BlackHole
doubao-inject speak <file>   — play audio file into BlackHole
doubao-inject read            — read voice chat transcript
doubao-inject toggle          — cycle audio input device
doubao-inject status          — show current state
```

### Audio device switcher: audiodev

A Swift+CoreAudio utility at `~/bin/audiodev` (compiled from `scripts/audiodev.swift`). Alternative to SwitchAudioSource when brew isn't available.

```bash
audiodev --list              # List input devices
audiodev --toggle             # Cycle between BlackHole and Microphone
audiodev --set "blackhole"    # Set BlackHole as input
audiodev --set "microphone"   # Set built-in mic as input
```

### How BlackHole injection works

1. `SwitchAudioSource -s "BlackHole 2ch" -t input` — system default input → BlackHole
2. Voice chat `getUserMedia()` reads audio from BlackHole's input side
3. **`ffmpeg -i file.aiff -f audiotoolbox -audio_device_index 0 ""`** plays audio TO BlackHole's output (verified working — full real-time 1x speed)
4. **⚠️ NOT `-f avfoundation`** — avfoundation is an INPUT format only, it fails as output muxer. Use **`-f audiotoolbox`** (AudioToolbox output) instead.
5. BlackHole loops the output signal back to its input → app hears it as mic input
6. Response transcript read via CDP: `document.body.innerText`

### Alternative: getUserMedia monkey-patch (no device switch)

For apps that cache the audio device at stream creation time, you can override `navigator.mediaDevices.getUserMedia` via CDP to return a custom MediaStream:

```javascript
const audioCtx = new AudioContext();
const dest = audioCtx.createMediaStreamDestination();
const osc = audioCtx.createOscillator();
osc.frequency.value = 440;
osc.connect(dest);
osc.start();

// Override getUserMedia to return our stream
const orig = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
navigator.mediaDevices.getUserMedia = async (constraints) => {
  if (constraints.audio) return dest.stream;
  return orig(constraints);
};
```

This works without system-level changes but must be injected BEFORE the app calls getUserMedia (i.e. before opening voice chat).

## Known pitfalls

- **Proxy interference:** The `websockets` library reads HTTP_PROXY/HTTPS_PROXY env vars and tries to route localhost through the proxy. Always use `NO_PROXY="*"` or `no_proxy="*"`.
- **React/SPA state:** Setting `element.value` directly may NOT trigger React state updates. Always use `Input.insertText` for reliable text input in React apps.
- **PID instability:** After restart, all PIDs change. Re-discover via `ps aux` or `curl /json`.
- **LSUIElement apps:** Some Chromium apps (floating overlays) have no Dock icon (`LSUIElement=true`). They still expose CDP pages.
- **CORS restrictions on custom protocol URLs:** Pages served from `appname://` schemes may restrict certain CDP methods. Standard ones (Runtime.evaluate, Input.*) work.
- **Reconnection:** CDP WebSocket connections drop on page navigation. Re-fetch page list from `/json` and reconnect.
- **Stale call state / auto-restoring pages:** Some Chromium apps auto-restore pages even after `Page.close`. Old call session text persists.
  ⚠️ **DO NOT navigate voice pages to `about:blank`** — this kills the floating overlay window (the Background process destroys the window). Instead, handle the end-call dialog via JS `.click()`:
  ```python
  # Click "结束并开始新通话" to end old call and start fresh
  await cdp_eval(vid, '''
    let els = document.querySelectorAll('div, button, span');
    for (let el of els) {
      if (el.textContent.includes('结束并开始新通话')) { el.click(); break; }
    }
  ''')
  ```
  **Important:** clicking "结束并开始新通话" already STARTS a new call. Don't then click the phone button again — use an `already_started` flag to guard the phone button click in `voice_open()`.
  Or click the phone/hang-up button on the launcher page to toggle the call (when no dialog is visible). Never navigate voice chat pages away — only their own UI buttons.
- **Bash `local` in case branches:** `local` only works inside functions. Case branches in bash scripts are NOT functions — use plain variable assignment instead.
- **macOS `say -o` only outputs AIFF:** The `say` command only outputs AIFF, not WAV. Use `.aiff` extension or convert via ffmpeg.
- **getUserMedia caches device at call time:** Switching the default input device won't affect an already-active microphone stream. Close and re-open the voice chat after switching.
- **ffmpeg background audio playback:** Use background terminal for long audio playback — don't block in foreground.
- **React dialog buttons are plain `<div>`s:** Dialogs ("end call", "cancel") may be rendered as `<div>` elements with no standard event attributes. Click detection fails with `querySelectorAll('button')`. Two approaches:

  **A) Primary: JS text content match + `.click()` (simpler, works with React synthetic events)**
  ```python
  r = await cdp('Runtime.evaluate', {'expression': '''
  (() => {
    let els = document.querySelectorAll('div, button, span, a');
    for (let el of els) {
      if (el.textContent.includes('结束并开始新通话') || el.textContent.includes('取消')) {
        el.click();
        return 'Clicked: ' + el.textContent.trim().slice(0, 50);
      }
    }
    return 'Button not found';
  })()
  ''', 'returnByValue': True})
  ```

  **B) Fallback:** `document.createTreeWalker` + `NodeFilter.SHOW_TEXT` to find text nodes, then get parent's `getBoundingClientRect()` for click coordinates.
- **ffmpeg output to BlackHole:** Use `-f audiotoolbox` (not `-f avfoundation`) for playing audio TO a macOS audio device. avfoundation is input-only. Device index 0 from listing: `ffmpeg -f lavfi -i "sine=frequency=440:duration=1" -f audiotoolbox -list_devices true -audio_device_index -1 dummy 2>&1 | grep Black`.
- **ASR is bilingual only:** Doubao voice chat ASR supports ONLY English and Chinese (verified across 19 languages). Other languages produce garbled forced-fit text or silence. The LLM handles any language in text mode — the bottleneck is the speech-to-text frontend.
- **App-level mute overrides system audio injection:** If the app's own microphone mute is enabled (Doubao: Option+T, or any app-internal toggle/button), audio injected via BlackHole is silently dropped — the app receives the audio stream but ignores it. System `SwitchAudioSource` still shows BlackHole as input, but the app's software mute overrides. **Verify app mic is unmuted before injecting.** If muted, unmute via CDP or UI interaction before proceeding. This is NOT the same as system input device selection.
- **Python version mismatch for user-run scripts:** The user's default `python3` may differ from the Hermes agent's. On this Mac, `/opt/homebrew/bin/python3` (Homebrew 3.14) and `/usr/local/bin/python3` (Python.org 3.13) coexist. Deps installed from one shell may not be available from the other. When deploying scripts the user will run manually: use absolute path or create a `run.sh` that hardcodes the correct Python, and verify dependencies from the user's shell via `python3 -c "import <module>"`.
- **Web UI dictation tool compatibility:** Two separate issues block macOS dictation tools (Handy, built-in speech) in CDP bridge web UIs. First: `onkeydown` handlers on `<input>` elements intercept key events before the browser can process dictation insertion. Second: `input.disabled = true` blocks ALL text insertion including from dictation tools. Fix both: use `<form>` + `submit` event listener, and never disable the input — only disable the send button.
- **App-level mute overrides system audio injection:** If the app's own microphone mute is enabled (Doubao: Option+T, or any app-internal toggle/button), audio injected via BlackHole is silently dropped — the app receives the audio stream but ignores it. System SwitchAudioSource still shows BlackHole as input, but the app's software mute overrides. Verify app mic is unmuted before injecting. This is NOT the same as system input device selection.
- **Voice dialog appears AFTER phone click, not just before:** The end-call dialog ("是否要挂断通话") may appear on the voice page AFTER the launcher phone button is clicked — not only before. Always check the voice page for the dialog text BOTH before and after the click. Use a pattern with `handle_end_call_dialog()` + `click_phone_launcher()` + `already_started` flag.
- **System HTTPS proxy lifecycle:** macOS has SEPARATE proxy settings for HTTP and HTTPS. Disabling HTTP proxy via `networksetup -setwebproxystate Wi-Fi off` does NOT disable HTTPS proxy. Always use `setsecurewebproxystate` as well. Check actual state via `scutil --proxy` (shows all proxy types in one dict) rather than `networksetup` (one query per service). To re-enable: `networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8888`. When switching networks (WiFi → BT tethering), all SSH tunnels/keepalive sockets become stale — must restart.

## Scripts

- `scripts/audiodev.swift` — Swift+CoreAudio utility for switching audio input devices without brew. Compile: `swiftc -o ~/bin/audiodev scripts/audiodev.swift`.
- `scripts/doubao-inject.sh` — Bash wrapper for the full Doubao voice-chat injection pipeline. Install to `~/bin/doubao-inject`.

## Multi-language bridge (Russian ↔ Chinese via English)

Since Doubao Voice Chat ASR only supports **English and Chinese**, you can use the agent as a language bridge for other languages:

**Pattern: Russian text → EN TTS → Doubao (EN ASR → AI ZH/EN response) → RU text**

```bash
# 1. User types Russian text (e.g. "Как тебя зовут?")
# 2. Agent translates RU → EN via explicit translate_ru_to_en() → TTS → inject via BlackHole
# 3. Wait for AI response (Chinese OR English — depends on context)
# 4. Read transcript via CDP, translate via translate_to_russian() (auto-detects ZH/EN)
# 5. Present Russian result to user
```

**Critical:** The AI may respond in Chinese OR English:
- Questions about itself (name, capabilities, duration) → often English
- Translation commands → Chinese
- Conversational follow-ups → mixed

Always auto-detect the source language when translating back to Russian. Use a function with an auto-detect prompt rather than hardcoding `zh → ru`.

See `references/doubao-ru-bridge-pipeline.md` for the full verified workflow.

Any language with text input can be bridged through EN/ZH this way. The ASR bottleneck is the only limitation — the LLM handles any language in text.

## Web UI Bridge Pattern

For long-running or multi-step CDP workflows, build a local web server with WebSocket instead of repeatedly typing CDP commands. This provides:

- **Real-time status** during multi-step pipelines (translation → TTS → injection → reading → translation)
- **Persistent UI** that survives session restarts
- **Dual-mode** switching between fast (text CDP) and rich (voice TTS) interaction

### Architecture

```
[Browser UI] ←WS→ [aiohttp server] ─CDP→ [Doubao/Chromium app]
                         │
                         ├─ TTS (say) → ffmpeg → BlackHole
                         └─ Translation API (DeepSeek etc.)
```

### When to use vs. direct CDP

| Scenario | Use |
|----------|-----|
| One-shot automation | Direct CDP (terminal) |
| Interactive session with status feedback | Web UI bridge |
| Voice + text mode switching | Web UI bridge |
| Multiple back-to-back queries | Web UI bridge |

### Templates included

- `templates/doubao-web-bridge-server.py` — ready-to-run aiohttp backend
- `templates/doubao-web-bridge-ui.html` — dark-theme HTML frontend (form-submit input for dictation tool compatibility)
- Live project at `~/projects/active/doubao-chat-bridge/` (run.sh included)

To deploy: copy both templates to a project dir, install deps (`pip install aiohttp websockets` for the target Python), and run.

See `references/doubao-web-bridge-ui.md` for full WebSocket protocol and pipeline details.

## Reference files

- `references/doubao-reverse-engineering.md` — full architecture, page types, UI element positions, and config paths for ByteDance's Doubao app.
- `references/brave-cdp-page-tab-direct.md` — direct page-tab WebSocket connection (workaround when Hermes caches stale browser WS ID), Network.setCookie before navigation, and Safaridriver W3C HTTP fallback.
- `references/doubao-inject-test-transcript.md` — verified test transcript with EN↔ZH bilingual translation pipeline.
- `references/doubao-asr-language-test.md` — comprehensive ASR language support test across 19 languages. Only EN and ZH work.
- `references/doubao-ru-bridge-pipeline.md` — verified Russian bridge workflow: RU text → EN TTS → Doubao voice chat → ZH response → RU text.
- `references/doubao-web-bridge-ui.md` — local web UI bridge pattern: build a full WebSocket+HTML interface wrapping a CDP-controlled app (aiohttp backend + dark-theme chat UI).
- `references/doubao-transcript-parsing-pitfalls.md` — critical bug fix: voice chat ASR text appears before AI response. Polling must wait for 2+ new lines. Includes code samples for both voice and text chat modes.
- Session documentation: `/Users/jenyanovak/projects/shelf/doubao-reverse-engineering.md` (also at `/Users/jenyanovak/reverseproxy/hermes_reverse.md` — older copy)
