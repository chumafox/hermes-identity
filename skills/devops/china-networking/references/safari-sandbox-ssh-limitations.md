# Safari Sandbox + osascript SSH Limitations on Headless Mac in China

## The Problem

On macOS 14+ (Sonoma), Safari runs in an App Sandbox container. Combined with SSH remote access to a headless Mac in China, this creates several hard restrictions:

1. **Can't modify Safari preferences via SSH** — `defaults write` targets the wrong path
2. **Can't clear Safari caches via SSH** — container path is protected
3. **Can't run osascript targeting Safari over SSH** — no GUI session access

## SIP Protection on Container Path (macOS 14+)

In addition to sandbox restrictions, the container path `~/Library/Containers/com.apple.Safari/` is now **protected by System Integrity Protection (SIP)**:

```bash
# Even as root over SSH:
sudo rm -rf /Users/admin/Library/Containers/com.apple.Safari
# → rm: /Users/admin/Library/Containers/com.apple.Safari: Operation not permitted

sudo rm -rf /Users/admin/Library/Caches/com.apple.Safari
# → rm: /Users/admin/Library/Caches/com.apple.Safari: Operation not permitted
```

This means there is **no CLI way** to fully reset Safari on macOS 14+ without:
1. Disabling SIP (requires Recovery Mode boot — complex on M-series)
2. Creating a new macOS user account (clean Safari for that user)
3. Using the Safari GUI menus (Clear History..., Manage Website Data)

Safari's data lives at:
```
~/Library/Containers/com.apple.Safari/Data/Library/
  ├── Safari/           ← history, bookmarks, LocalStorage, etc.
  └── Preferences/
      └── com.apple.Safari.plist  ← user preferences
```

**This path is PROTECTED** — even `sudo` cannot read/write it over SSH:
```bash
# Over SSH — ALL FAIL:
ls ~/Library/Containers/com.apple.Safari/Data/Library/Safari
# → Operation not permitted

defaults write com.apple.Safari WarnAboutFraudulentWebsites -bool false
# → Could not write domain .../com.apple.Safari; exiting

rm -rf ~/Library/Containers/com.apple.Safari/Data/Library/Safari/LocalStorage
# → Operation not permitted
```

**Why:** App Sandbox on macOS restricts container access to the app itself and the user's GUI session. SSH sessions (even as the same user) are considered separate security contexts.

## osascript Over SSH NEVER Targets Safari

```bash
# Over SSH — ALWAYS fails:
osascript -e 'tell application "Safari" to set URL of document 1 to "https://example.com"'
# → execution error: The variable Safari is not defined. (-2753)
```

The error `-2753` means "application not found in this session context." Safari is running in the user's GUI session (Aqua/window server), and SSH creates a separate session without access to that context.

### The `launchctl asuser` Workaround

Run osascript in the user's GUI session via launchd:

```bash
# Get the GUI user's UID
GUI_UID=$(ps -o uid= -p $(pgrep -x Dock) | tr -d ' ')
echo "GUI UID: $GUI_UID"

# Run osascript as that user
sudo launchctl asuser $GUI_UID osascript -e '
tell application "Safari"
    set URL of document 1 to "https://huggingface.co"
end tell
'
```

**Prerequisites:**
- The target user must be logged into the GUI (through Screen Sharing or physically)
- Safari must already be running in that GUI session
- `sudo` must be available (the headless Mac user must have sudo rights)

**Pitfall:** This injects Apple Events into the running Safari process. If the system TCC database blocks automation (privacy controls), it may still fail silently.

## Safari Preference Path (System-Level — Works Over SSH)

System-level Safari/WebKit preferences are NOT sandboxed and CAN be set over SSH:

```bash
# WORKS over SSH — system-level settings:
sudo defaults write /Library/Preferences/com.apple.networkd EnableQuic -bool false

# Safari-specific sandbox-escaped keys (may or may not apply):
# ~/Library/Preferences/com.apple.Safari.plist
# (this is the OLD path, before sandbox — might still work for some keys)
defaults write ~/Library/Preferences/com.apple.Safari WebKitDisableHTTPSUpgrade -bool YES
```

## Practical Implications for China Headless Mac

| Action | Over SSH | Via Screen Sharing Terminal |
|--------|----------|---------------------------|
| Clear Safari cache | ❌ Operation not permitted | ✅ rm ~/Library/Containers/... |
| Disable Fraudulent Warnings | ❌ Sandbox write error | ✅ Click in Safari Settings |
| Navigate to URL | ❌ osascript -2753 error | ✅ osascript OR Safari->URL bar |
| Click "Visit Website" on cert error | ❌ | ✅ Manually via Screen Sharing |
| Disable QUIC system-wide | ✅ sudo defaults write | ✅ Same |
| Check Safari process state | ✅ pgrep -fl Safari | ✅ Same |

## Best Practice for Safari Certificate Errors (China)

When Safari shows "This Connection Is Not Private" or "can't establish secure connection" on headless Mac:

### Step 1: Rule Out Speedify Network Extension

If **ALL** websites fail in Safari (bing.com, google.com, fast.com, etc.) but curl works:

```bash
# Check if Speedify NE is active and blocking
systemextensionsctl list
# See: Speedify.PacketTunnelSysExt [activated enabled]?

# Test system network stack via Python (uses NSURLSession like Safari)
python3 -c "
import urllib.request
try:
    r = urllib.request.urlopen('https://www.bing.com', timeout=10)
    print(f'Status: {r.status}')
except Exception as e:
    print(f'Error: {e}')
"
```

If systemextensionsctl shows Speedify and Python urllib fails (but curl succeeds) → Speedify NE is the cause. See main skill's Speedify section for removal.

### Step 2: Try Brave Browser

If Safari fails but system networking works, open Brave Browser:
```bash
open -a "Brave Browser" https://www.bing.com
```

If Brave works, the issue is Safari-specific (sandbox corruption, cert cache, or Speedify NE targeting Safari's NSURLSession).

When Safari shows "This Connection Is Not Private" or "can't establish secure connection" on headless Mac:

1. **Use Screen Sharing** terminal to run osascript (not SSH)
2. Or **tell the user** what to click:
   - "This Connection Is Not Private" → Show Details → Visit this website
   - "can't establish secure connection" → check if QUIC is blocking (disable via SSH)
3. If QUIC is suspected, disable system-wide via SSH and restart Safari:
   ```bash
   sudo defaults write /Library/Preferences/com.apple.networkd EnableQuic -bool false
   killall Safari
   # Then reopen Safari via Screen Sharing
   ```
