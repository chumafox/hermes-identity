# Doubao (豆包) — Reverse Engineering Notes

Session: 2026-06-14. Doubao is ByteDance's AI assistant, Chromium-based (version 135).

## App Identity
- Bundle: `com.bot.pc.doubao`
- Path: `/Applications/Doubao.app`
- Signature: `Cr24` (Chromium)
- AppleScript enabled: yes (`NSAppleScriptEnabled=true`), but no scripting.sdef
- URL scheme: `doubao://`

## Process Architecture (from ps aux)

| Process | Role |
|---------|------|
| `Doubao` | Main Chromium wrapper |
| `Doubao Browser` | Browser window (`--saman-from-chat=<main_pid>`) |
| `Doubao Browser Accessory` | Floating overlay (LSUIElement, no dock) |
| `Doubao Browser Helper (network)` | Network service (all HTTP/S exit point) |
| `Doubao Browser Helper (Renderer)` | Page renderers |
| `Doubao Browser Helper (audio)` | Audio service |
| `Doubao Browser Helper (push)` | Push notification service (`saman.push.mojom`) |

## Network Architecture
- All traffic routes through `localhost:1080` (SOCKS5) or `localhost:8888` (HTTP proxy)
- External destination: `www.doubao.com:443`
- Images: `*.byteimg.com`
- Network service process is the single egress point

## CDP Pages (port 9223)

| URL | Type | Notes |
|-----|------|-------|
| `doubao://doubao-chat/chat/<id>` | page | Text chat UI |
| `doubao://doubao-launcher/chat?viewId=N` | page | Floating overlay (launcher) |
| `doubao://doubao-voice-chat/?enter_from=global&viewId=N` | page | Voice chat page |
| `doubao://doubao-background/` | page | Background (chrome://) |
| `doubao://doubao-chat/cross-site-support/` | other | Internal |

## UI Element Positions (launcher page, 400x600)

| Element | Position | Size | Description |
|---------|----------|------|-------------|
| Avatar button | (12,13) | 24x24 | User menu |
| Back/minimize | (44,12) | 26x26 | Window control |
| History/clock | (294,12) | 26x26 | History menu |
| **Phone icon** | **(328,12)** | **26x26** | **Voice chat trigger** |
| Settings/gear | (362,12) | 26x26 | Settings |
| Quick ("快速") | (81,540) | 72x32 | Quick action |
| More ("更多") | (157,540) | 64x32 | More menu |

## Text Chat UI
- Input field: `textarea.semi-input-textarea` (placeholder: "发消息...")
- Position: (330, 700), 760x24
- Send: Enter key (works via `Input.dispatchKeyEvent`)
- Chat appears in `document.body.innerText`

## Voice Chat UI
- Status text: "请开始说话" (idle) → "正在听..." (listening)
- Transcript in `document.body.innerText`
- No UI buttons except hang-up (SVG icon at ~140,241) and "复制" (copy)
- End call dialog: "结束并开始新通话" / "取消" at (20,266+) 240x36

## Config Files

| Path | Purpose |
|------|---------|
| `~/Library/Preferences/com.bot.pc.doubao.plist` | Language (zh_CN) |
| `~/Library/Application Support/Doubao/` | Full Chromium profile |
| `.../Default/Preferences` | Profile preferences |
| `.../Default/Bookmarks` | `www.doubao.com` |
| `.../Default/Cookies` | Session cookies |
| `.../Default/Local Storage/leveldb/` | Web app local storage |
| `.../saman_app_state` | **Chat overlay state** (`{"chat_app_state":{"visible":false}}`) |
| `.../ChatAppFeatureState` | Chromium feature flags |
| `.../saman_update_info` | Update metadata |
