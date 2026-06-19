---
name: wechat-automation
description: Interact with WeChat for macOS via AppleScript and accessibility tools
title: WeChat Automation on macOS
---

# WeChat Automation on macOS

## When to use
User wants to interact with WeChat desktop app on macOS:
- Send messages to WeChat contacts
- Read chat content
- Contact support via WeChat

## Sending Messages (AppleScript — ✅ Works)

WeChat for macOS accepts keystroke input via System Events.
This works reliably for **sending** but cannot **read** messages.

## AppleScript approach (basic)
```
tell application "WeChat" to activate
delay 0.5
tell application "System Events"
    keystroke "your message text"
    keystroke return
end tell
```

## Limitations — AppleScript can SEND but CANNOT READ
WeChat for macOS does not expose chat content via AppleScript Accessibility API.
- `keystroke` + `return` works for sending ✅
- Reading incoming messages via `value of static text` returns empty ❌
- The window hierarchy is opaque to System Events

## Reading WeChat content (requires cua-driver)
1. Install: `hermes computer-use install` or `brew install cua-driver` (if available)
2. Give Screen Recording permission (System Settings → Privacy & Security → Screen Recording)
3. Use `cua-driver screenshot` commands to capture the window as an image
4. Use vision_analyze to read content from the screenshot

## WeChat API alternatives
WeChat for macOS has no official API. Options for programmatic read/write:
- **Windows VM + wcf** (WeChatChatroomFramework) — injects into WeChat process, provides HTTP/gRPC API
- **PlayCover** (M1/M2 Mac) — runs iOS WeChat as a Mac app, but still no read API
- **cua-driver screenshots** — works on any macOS app, requires Screen Recording permission

## Tests
- Verify WeChat is running: `pgrep -f WeChat`
- Send test: `osascript -e '...'` (see AppleScript above)
- Read via cua: `cua-driver list_windows` → find WeChat window_id → `cua-driver screenshot`
## Reading Messages (cua-driver — ⚠️ Requires Screen Recording permission)

WeChat does NOT expose chat content via Apple Accessibility API (staticText reads empty).
Use cua-driver screenshot instead, piping JSON via stdin:

```bash
# 1. List WeChat windows
cua-driver list_windows | python3 -c "import sys,json; data=json.load(sys.stdin); [print(w['window_id'],w['title']) for w in data['windows'] if 'WeChat' in w['app_name']]"

# 2. Screenshot the main WeChat window (window_id from step 1)
printf '{"window_id":WINID}' | cua-driver screenshot 2>&1
```

PITFALL: cua-driver requires `printf '{"window_id":N}'` stdin format, not CLI flags like `window_id=N`.
PITFALL: The output contains a non-base64 prefix line. Must use `grep -v "^✅"` or `tail -1` before base64 decode.
PITFALL: If the output is ~58 bytes (ASCII text saying "Missing permission"), Screen Recording is not granted.

**Fix Screen Recording:**
```bash
# Open System Settings → Privacy & Security → Screen Recording
# Add the app that runs cua-driver (usually Terminal or cua-driver itself)
open "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"
```

## Verified Commands from Real Sessions

```bash
# Check cua-driver is installed and working
cua-driver --version

# List running applications 
cua-driver list_apps

# List all windows (including WeChat)
cua-driver list_windows

# Screenshot specific window (CORRECT format)
printf '{"window_id":16202}' | cua-driver screenshot

# Save screenshot to file
printf '{"window_id":16202}' | cua-driver screenshot | grep -v "^✅" | base64 -D > /tmp/wechat.png
```

## Limitations

| Operation | Works? | Method |
|-----------|--------|--------|
| Send message | ✅ | AppleScript keystroke |
| Read messages | ⚠️ | cua-driver screenshot + vision (needs Screen Recording perm) |
| List contacts | ❌ | No API available |
| Switch chat | ❌ | Need user to select chat first |
| Read without permissions | ❌ | Neither AX API nor screenshot works |

## Alternative: Windows VM + wcf (ComWeChatRobot)

For full bidirectional WeChat API (send AND read), the most reliable approach:
1. Set up Windows VM (UTM recommended on M1/M2/M3, 2-4 GB RAM, minimal resources)
2. Install WeChat for Windows
3. Install wcf (WeChatChatroomFramework) — injects into WeChat memory
4. wcf exposes HTTP/gRPC endpoints for full read/write/manage
5. Connect from macOS via HTTP over LAN to VM's IP

## When NOT to use
- Simple test message → AppleScript is enough
- Autonomous conversation → won't work on macOS natively without Windows VM + wcf
- Screen Recording not granted → skip reading, ask user to read messages manually
