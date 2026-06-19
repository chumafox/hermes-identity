---
name: macos-screen-sharing
description: "Configure and troubleshoot macOS Screen Sharing (VNC) between Macs. Covers headless Mac issues (phantom menu bar clicks), Thunderbolt Bridge optimization, and connection diagnostics."
tags: ["apple"]
---

# macOS Screen Sharing

Configure, troubleshoot, and optimize Screen Sharing (VNC) between Macs, especially headless Macs without a physical monitor.

## Connection Basics

### Via Thunderbolt Bridge (preferred for local Mac-to-Mac)

Thunderbolt Bridge provides the lowest latency (<1ms) and highest bandwidth for Screen Sharing between two Macs connected via Thunderbolt cable.

**Known GUI quirk:** System Settings may show "Unknown state" for Thunderbolt Bridge even when it's fully active. Verified via CLI:

```bash
ifconfig bridge0 | grep status
# → status: active
```

**Check active Screen Sharing connection:**
```bash
sudo lsof -iTCP:5900 -P -n | grep ESTABLISHED
# → 192.168.2.2:5900->192.168.2.1:49431 (ESTABLISHED)
```

**Check all listening interfaces:**
```bash
sudo netstat -an -p tcp | grep ':5900'
```

## Headless Mac — Known Issues

### Problem: clicking Dock triggers Apple menu (top-left corner)

On a headless Mac (no physical monitor attached), Screen Sharing creates a "Screen Sharing Virtual Display". macOS in this mode can mis-handle mouse coordinates — clicking an app in the Dock sometimes registers as a click in the top-left corner, opening the Apple menu persistently.

**Root cause:** No EDID data from a physical monitor. macOS doesn't have a real display to bind coordinate space to.

**Pitfall:** `lsof -iTCP:5900 -P -n` **without sudo** shows only LISTEN entries via `fileport` — it will NOT show ESTABLISHED connections even if a VNC session is active. This is because `screensharing` uses `fileport=` descriptors for LISTEN sockets (readable without root), but ESTABLISHED connections use regular file descriptors that require root (sudo) to enumerate. Always use `sudo` to see active sessions:

```bash
# Shows only LISTEN (misleading — may think no session):
lsof -iTCP:5900 -P -n | grep ESTABLISHED  # likely empty

# Shows ESTABLISHED connections correctly:
sudo lsof -iTCP:5900 -P -n | grep ESTABLISHED
# → 192.168.2.2:5900->192.168.2.1:49431 (ESTABLISHED)
```

**Pitfall:** Hot corners, "Displays have separate Spaces", and Accessibility settings are usually NOT the cause — verify anyway:

```bash
# Check hot corners
defaults read com.apple.dock wvous-tl-corner 2>&1
# Check separate Spaces
defaults read com.apple.spaces spans-displays 2>&1
```

### Solutions

#### Option A: BetterDisplay (recommended — software EDID emulation)

BetterDisplay creates a virtual monitor with proper EDID, fixing coordinate mapping. Install on the headless Mac:

```bash
brew install --cask betterdisplay
```

Free version works for basic headless fix. Pro needed for advanced features.

#### Option B: HDMI dummy plug

Physical EDID emulator (~$5-10 on AliExpress). For M-series Macs with USB-C ports, a USB-C to HDMI adapter + HDMI dummy plug is needed.

#### Option C: Reset Screen Sharing (temporary workaround)

Sometimes restarting Screen Sharing on the headless Mac helps temporarily:

```bash
sudo killall screensharingagent
# Screen Sharing auto-restarts via launchd
```

### Browser Not Loading (CLI Works)

When a headless Mac has working internet (curl, ping, DNS from terminal) but Safari/Chrome doesn't load pages via Screen Sharing:

1. **Certificate interception in China** — curl may accept MITM certificates that browsers reject
2. **Safari iCloud Private Relay** — can break on China-routed connections
- **IPv6 interference** — Safari tries IPv6 first (Happy Eyeballs), curl uses IPv4
- **Headless click-coordinate bug** — user may think they're clicking URL bar but hitting top-left menu
- **Speedify / VPN Network Extension Active** — Speedify NE blocks browser traffic when not connected (detect via `systemextensionsctl list`)
- **VPN/Proxy app running in VPN mode** — Happ, ClashX, etc. in packet-tunnel mode intercept ALL traffic including Hermes API calls. When tunnel is unstable, Hermes itself stops working (see `china-networking` → VPN/proxy DNS section).

**Diagnostic: Python urllib vs curl**
```bash
# If this works — NE is likely NOT the cause (cert/MITM issue):
python3 -c "import urllib.request; print(urllib.request.urlopen('https://www.bing.com', timeout=10).status)"

# If this works but Safari doesn't — NE is the cause:
curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 https://www.bing.com
```
Python's `urllib` uses the same system network stack as Safari (NSURLSession). If curl works but both Python and Safari fail → MITM/cert issue. If curl works but Python AND Safari fail → NE/vpn issue.

See `references/browser-cli-discrepancy.md` for full diagnostics.

## Keyboard Layout Switching (Input Source) Through Screen Sharing

When you press **Cmd+Space** (or whatever your local shortcut is) inside a Screen Sharing window, macOS processes the shortcut **locally** (on the viewer Mac) — it never reaches the remote Mac. This makes switching keyboard layouts (e.g., EN → RU) unusable: you must exit the Screen Sharing window to change language.

**Solution: Use Caps Lock for input source switching on BOTH Macs.**

On both the local and remote Mac:
- System Settings → Keyboard → Input Sources → **Use Caps Lock to switch input source**
- This works through Screen Sharing because Caps Lock is sent as a hardware key event, not intercepted as a shortcut.

**To verify keyboard layouts on remote Mac via SSH:**
```bash
# Check current layouts
defaults read com.apple.HIToolbox AppleEnabledInputSources

# Expected output when Russian is added:
# {
#     InputSourceKind = "Keyboard Layout";
#     "KeyboardLayout ID" = 19456;
#     "KeyboardLayout Name" = Russian;
# }

# Russian layout ID is 19456, U.S. is 0
```

**Pitfall:** If Caps Lock stops working after rebooting, the setting may have been reset. Check in System Settings after reboot.

**Pitfall: Safari keyboard language issue may be caused by Speedify Network Extension, not Screen Sharing.**
If keyboard shortcuts *and* browsers fail in different ways — Safari shows "can't establish a secure connection" while Brave/curl work — the cause is Speedify.PacketTunnelSysExt, not Screen Sharing. See `china-networking` Speedify section.

## USB-C Direct Connection (Static IP Fallback)

When Thunderbolt Bridge isn't available (no TB cable), both Macs can connect via USB-C cable. macOS assigns dynamic Link-Local IPs (169.254.x.x) which change on every reconnect — unreliable for SSH/config.

**Solution: Assign static IP on USB-C interfaces on both Macs.**

### On the Headless Mac (remote, no monitor)

```bash
# 1. Find the Type-C interface
# Look for an interface with no service, 169.254.x.x IP
ifconfig | grep -B5 "inet 169.254" | grep -B5 "en"

# 2. Create a network service for it
sudo networksetup -createnetworkservice "USB-C Ethernet" en6

# 3. Assign static IP (use 192.168.3.x — doesn't conflict with 192.168.2.x TB or 172.20.10.x iPhone)
sudo networksetup -setmanual "USB-C Ethernet" 192.168.3.2 255.255.255.0 192.168.3.1

# 4. Restart the interface
sudo ifconfig en6 down
sleep 1
sudo ifconfig en6 up

# 5. Verify
ifconfig en6 | grep "inet "
# → inet 192.168.3.2 netmask 0xffffff00 broadcast 192.168.3.255
```

### On the Viewer Mac (local, has screen)

Sometimes `networksetup -createnetworkservice` fails because the USB-C interface isn't registered as a hardware port. Fallback: LaunchDaemon that assigns IP at boot.

```bash
# 1. Find the Type-C interface
route -n get admin-admin.local | grep interface
# → interface: en7

# 2. Create a LaunchDaemon (survives reboot, SIP-safe)
sudo tee /Library/LaunchDaemons/com.local.usb-c-ip.plist > /dev/null << 'PLISTEOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.usb-c-ip</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/ifconfig</string>
        <string>en7</string>
        <string>inet</string>
        <string>192.168.3.1</string>
        <string>netmask</string>
        <string>255.255.255.0</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLISTEOF

# 3. Load it
sudo launchctl load -w /Library/LaunchDaemons/com.local.usb-c-ip.plist

# 4. Verify
sudo launchctl list | grep usb-c
# → -   0   com.local.usb-c-ip
ping -c 2 192.168.3.2
```

### Pitfalls

- **Static IP vs Link-Local** — after setting static IP, mDNS hostname (`admin-admin.local`) still resolves but to the old 169.254.x.x. Use the static IP (192.168.3.2) for SSH/SCP.
- **Interface number may change** — `en6`/`en7` can shift if other USB devices are plugged/unplugged. Verify with `ifconfig | grep 192.168.3` after reboot.
- **Thunderbolt Bridge still preferred** — 192.168.2.x / TB has <1ms latency vs ~1.4ms for USB-C. Both work for SSH/Screen Sharing.

## Auto-Start After Reboot

Screen Sharing is a system launchd service — it auto-starts on macOS boot:

```bash
# Verify it's registered in launchctl
sudo launchctl list | grep screensharing
# → <PID>	0	com.apple.screensharing

# Confirm Remote Login is on
sudo systemsetup -getremotelogin
# → Remote Login: On

# The launchd plist lives at:
ls /System/Library/LaunchDaemons/com.apple.screensharing.plist
```

No additional configuration needed — Screen Sharing survives reboot natively on macOS.

### iCloud Private Relay Interference

If iCloud Private Relay is enabled on the headless Mac, Safari may route all traffic through blocked relay servers (common in China). Disable in System Settings → Apple ID → iCloud → Private Relay, or use Brave/Chrome as a workaround.

## Performance Notes

- Thunderbolt Bridge is optimal for Screen Sharing — <1ms latency, no WiFi interference
- Verify both Macs have `status: active` on their bridge0 interface
- Headless Mac creates "Screen Sharing Virtual Display" at 3840x2160 (4K) by default — this is normal
- For best results, ensure both Macs are on the same Thunderbolt Bridge subnet (e.g. 192.168.2.x)

### Battery Drain Warning

Screen Sharing (VNC) between Macs **significantly drains battery** on the viewer Mac (the one running the Screen Sharing app). This is because macOS keeps the GPU active and continuously encodes/transmits screen frames, even when the content is static.

- Viewer-side Mac: GPU stays active → high power draw → battery drain visible in Activity Monitor
- The headless (remote) Mac uses minimal power — it's just exporting its frame buffer
- **Mitigation:** Disconnect Screen Sharing when not actively needed. Use SSH for CLI-only tasks.
- If Screen Sharing is essential, consider a wired Thunderbolt/USB-C connection — the network stack draws less power than WiFi for the constant frame stream.

### TCC File Access via Screen Sharing

When Screen Sharing is active but you need to copy files from the remote Mac's ~/Documents, SSH will fail with `Operation not permitted` on macOS 15+. See the TCC workaround reference:

```bash
skill_view(name="macos-screen-sharing", file_path="references/tcc-file-access.md")
```

### MDM/DEP Enrollment Bypass

Headless Macs with DEP enrollment (e.g. Walmart/Jamf) will persistently show enrollment windows. Even with DNS blocks on Apple+Jamf servers, the enrollment triggers **locally** from SIP-protected `.cloudConfig*` files in `/var/db/ConfigurationProfiles/Settings/`. See:

```bash
skill_view(name="macos-screen-sharing", file_path="references/mdm-dep-bypass.md")
```
