# Doubao (豆包) — Mac App Inspection Notes

**Bundle ID:** `com.bot.pc.doubao`
**Type:** Chromium-based (Chromium 135.0.7049.72, CFBundleSignature Cr24)
**Backend:** `www.doubao.com`
**Version in use:** 135.0.7049.72
**Path:** `/Applications/Doubao.app/`
**Config root:** `~/Library/Application Support/Doubao/`

## Process Architecture

| Process | PID | Role |
|---------|-----|------|
| `Doubao` | 95689 | Main app |
| `Doubao Browser` | 95694 | Browser window (--saman-from-chat=95689) |
| `Doubao Browser Accessory` | 95701 | **Floating overlay icon** (LSUIElement, no dock) |
| `Doubao Browser Helper (network)` | 95702 | Network service (Chromium's network.mojom.NetworkService) |
| `Doubao Browser Helper (renderer)` | 95705, 95706 | Renderer processes |
| `Doubao Browser Helper (GPU)` | 95700 | GPU process |
| `Doubao Browser Helper (audio)` | 95796 | Audio service |
| `Doubao Browser Helper (push)` | 95837 | Push server (saman.push.mojom.PushServerService) |

**"saman"** — Doubao's internal codename for the chat overlay feature.
Flag: `--saman-from-chat=<main-pid>` passed to overlay processes.

## Network Architecture

- Traffic routes through **internet_pro** (SOCKS5 on 127.0.0.1:1080, HTTP proxy on 127.0.0.1:8888)
- Network service (PID 95702) makes the external connections via the proxy
- External endpoints: `www.doubao.com` (API), `byteimg.com` (images)

## Automation Surface

- **AppleScript:** `NSAppleScriptEnabled=true` in Info.plist but no `scripting.sdef` found in Resources — AppleScript likely non-functional
- **CDP:** No `--remote-debugging-port` flag on running processes
- **State file:** `~/Library/Application Support/Doubao/saman_app_state` — tracks `browser_app_state.has_browser_window` and `chat_app_state.visible` (JSON)
- **API:** www.doubao.com — undocumented HTTPS API

## Key Config Files

- `~/Library/Preferences/com.bot.pc.doubao.plist` — minimal (just AppleLanguages)
- `~/Library/Application Support/Doubao/Local State` — Chromium global state
- `~/Library/Application Support/Doubao/Default/Bookmarks` — main web app URL
- `~/Library/Application Support/Doubao/Default/Cookies` — SQLite cookies
- `~/Library/Application Support/Doubao/Default/Preferences` — Chromium profile prefs
- `~/Library/Application Support/Doubao/saman_app_state` — overlay visibility state
- `~/Library/Application Support/Doubao/saman_update_info` — update info

## Automation Approach Options

1. **mitmproxy** — intercept HTTPS to www.doubao.com, discover REST/GraphQL API
2. **CDP relaunch** — kill Doubao, relaunch with `--remote-debugging-port=9223` ✅ **CONFIRMED WORKING** (see `chromium-app-automation` skill for full CDP workflow, voice chat automation, and audio injection via BlackHole)
3. **State file manipulation** — write `chat_app_state.visible=true` to saman_app_state
4. **Accessibility** — click the floating overlay via macOS Accessibility API

## Voice Chat & Translation (Verified June 14, 2026)

- **Voice chat** activated via phone-icon button on launcher page (x=328, y=12 on 400x600 overlay)
- **ASR** supports English and Chinese (confirmed — no other languages tested)
- **AI model** translates EN↔ZH bidirectionally via voice
- **Language bundles:** Only `zh` loaded in localStorage (`i18nextLng: zh`). UI keys reference 19+ language codes (en, ja, ko, ru, fr, de, es, pt, ar, id, th, vi, it, tr, hi, ms, nl, pl) suggesting i18n coverage for at least those markets
- `Audio_chat_lang_reject` message triggers when ASR can't parse the spoken language ("不好意思我没听懂，可以用中文再说一遍吗？") — suggests ASR has limited language support beyond EN/ZH
- **Product name:** "Doubao" in China, "Cici" internationally

## References

- All info from live inspection of running Doubao app (June 14, 2026)
- Chromium version 135.0.7049.72
