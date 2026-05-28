# Browser Not Loading (CLI Connectivity Fine) — Headless Mac

## Scenario
- **curl, ping, nslookup** all work from terminal
- **Safari / Chrome** shows blank page, spinning wheel, or "cannot open page"
- Happens on headless Mac (no physical monitor) connected via Screen Sharing

## Root Causes

### 1. Certificate Interception (Great Firewall MITM)

China's firewall performs TLS interception on many domains. Terminal tools (curl) may accept the injected certificate or bypass it, but browsers enforce stricter certificate validation.

**Test:**
```bash
# Compare behavior:
curl -v https://google.com 2>&1 | grep -i "certificate"
```

**Fix:** Open Keychain Access → System → find the China-issued root CA → trust it for all uses. Or use a VPN/Speedify to bypass interception entirely.

### 2. Safari iCloud Private Relay

If iCloud+ Private Relay is enabled, Safari routes traffic through Apple's proxy. On a China-routed iPhone USB connection, this can fail silently (Apple proxy servers may be blocked).

**Fix:** System Settings → Apple ID → iCloud → Private Relay → Off

### 3. DNS-over-HTTPS in Browser

Safari/Chrome may use DoH with a different resolver than system DNS. If the DoH endpoint (e.g. `mozilla.cloudflare-dns.com`) is blocked in China, browser DNS fails while system DNS works.

**Check in Safari:** Safari → Settings → Advanced → DNS settings.

### 4. Safari Uses IPv6 First (Happy Eyeballs)

If the iPhone tethering provides an IPv6 address but routing is broken, Safari attempts IPv6 first (RFC 8305), times out, and may give up before trying IPv4. curl uses IPv4 by default.

**Test:**
```bash
curl -4 https://google.com  # If this works but Safari doesn't, it's an IPv6 issue
```

**Fix:** Disable IPv6 on the iPhone USB interface:
```bash
sudo networksetup -setv6off "iPhone USB"
```

### 5. QUIC/HTTP3 Blocking (New — Most Likely)

China Mobile and other carriers often block QUIC (UDP on port 443) used by HTTP/3. Safari aggressively tries HTTP/3 while curl may fall back to HTTP/2. This manifests as "Safari can't establish a secure connection" while curl gets HTTP 200.

**Test:**
```bash
# Compare HTTP/2 vs HTTP/1.1 in curl:
curl --http2 -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 https://huggingface.co
curl --http1.1 -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 https://huggingface.co
```

**Fix globally (** works over SSH **):**
```bash
sudo defaults write /Library/Preferences/com.apple.networkd EnableQuic -bool false
```

### 6. Safari Sandbox + osascript SSH Limitation

**If you're trying to automate Safari over SSH** — it won't work. See dedicated reference: `safari-sandbox-ssh-limitations.md` (in `china-networking` skill).

Key summary:
- `defaults write com.apple.Safari ...` fails over SSH (sandbox container protected)
- `osascript -e 'tell app "Safari"'` fails over SSH (-2753 error, no GUI session access)
- `sudo launchctl asuser $GUI_UID osascript ...` is the workaround

### 7. Safari Content Blockers

Some ad/content blockers misbehave on headless Mac screen sharing.

**Test:** Safari → Settings → Extensions → Disable all content blockers.

### 8. Speedify (or other VPN/NE) Network Extension Active

If `curl`, `ping`, and even Python's `urllib` all work but **every** browser (Safari, Chrome, Brave) fails the same way — "can't establish a secure connection" — the most likely cause is a **System Extension / Network Extension** that's intercepting traffic.

Speedify and similar VPN-like apps install a `PacketTunnelSysExt` network extension. If the app is installed but **not connected/logged in**, the extension sits in a half-activated state that **blocks all browser traffic** while allowing direct socket access (curl, ping).

**Detection:**
```bash
# List all system extensions — look for enabled+active network extensions
systemextensionsctl list

# Key output to look for:
# enabled	active	teamID	bundleID (version)	name
# *	*	42L9495X72	com.connectify.Speedify.PacketTunnelSysExt	PacketTunnelSysExt	[activated enabled]
```

**Curl vs Python urllib vs Safari divergence (diagnostic flow):**

The key diagnostic question: **does Python's `urllib` work?**

```bash
python3 -c "import urllib.request; print(urllib.request.urlopen('https://www.bing.com', timeout=10).status)"
```

Python's `urllib.request.urlopen` uses the **same system network stack as Safari** (NSURLSession on macOS, or CFNetwork). This means:

| curl | Python urllib | Safari | Likely cause |
|------|---------------|--------|-------------|
| ✅ Works | ✅ Works | ❌ Fails | **Safari sandbox corruption** or Safari-specific config (not NE) |
| ✅ Works | ❌ Fails | ❌ Fails | **Speedify NE / VPN extension** blocking NSURLSession traffic |
| ❌ Fails | ❌ Fails | ❌ Fails | **Network / DNS / proxy** issue |
| ✅ Works | ✅ Works | ✅ Works | **Everything fine** — user error or click-coordinate bug |

**Key insight:** Python urllib is NOT a reliable NE bypass — it goes through the same system stack as Safari. If Python urllib returns HTTP 200, the NE is NOT blocking traffic, and the problem is Safari-specific (sandbox corruption, config, or iCloud Private Relay).

**Fix:**
```bash
# 1. Stop the daemon
sudo pkill -9 -f speedify

# 2. Move the app to trash
sudo mv /Applications/Speedify.app ~/Trash/

# 3. Remove extension staging directory (may be SIP-protected on M-series)
sudo rm -rf /Library/SystemExtensions/*Speedify*

# 4. Edit extension DB (may be SIP-protected)
sudo plutil -remove "extensions.0" /Library/SystemExtensions/db.plist

# 5. REBOOT — extension stays active until reboot even after app removal
sudo shutdown -r now
```

**If SIP prevents deletion** (M1/M2 Mac, `rm: Operation not permitted` on System Extensions):
- Reboot is still required — sometimes booting clears the staging
- Or deploy a configuration profile blocking the extension (via MDM)
- Or reinstall the app, properly disconnect/disengage the extension, then uninstall

**Prevention:** Before installing Speedify/any VPN on a headless Mac, understand that its NE:
- Survives app deletion (cached by SIP-protected System Extensions db)
- Blocks browser traffic when not connected
- Requires reboot to fully clear after removal

### 10. Safari Sandbox Container Corruption (SIP-Protected)

When Safari's sandbox container (`~/Library/Containers/com.apple.Safari/`) is corrupted, Safari can fail to load **any** page with "can't establish a secure connection" even though:
- `curl` works
- Python `urllib` works
- Brave Browser or Chrome works
- Ping, DNS all work

**Critical limitation:** On macOS 14+ with SIP enabled (default on Apple Silicon), the Safari sandbox container is **fully unreachable from CLI** — even `sudo rm -rf` returns `Operation not permitted`. This means:
- Cannot clear Safari's cache, history, or preferences via SSH
- Cannot reset Safari via `defaults write` (sandbox redirect)
- `osascript` targeting Safari fails over SSH (no GUI session, error -2753)

**Detection:**
```bash
# Both of these will fail with "Operation not permitted" even as root:
sudo ls -la ~/Library/Containers/com.apple.Safari/Data/Library/Safari/
sudo rm -rf ~/Library/Containers/com.apple.Safari/

# Confirm it's NOT a network issue:
python3 -c "import urllib.request; print(urllib.request.urlopen('https://www.bing.com', timeout=10).status)"
# → 200 (Safari still fails)

curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 https://www.bing.com
# → 200
```

**Workarounds (none ideal):**
1. **Use Brave Browser** instead — it works on the same Mac (confirmed working)
2. **Clear Safari data via GUI** — user must interact with Safari directly through Screen Sharing:
   - Safari → Settings → Privacy → Manage Website Data → Remove All
   - History → Clear History → Clear
3. **Create a new macOS user** — new user gets a clean Safari sandbox
4. **Reboot into Safe Mode** (hold Shift at boot) — may clear extension caches
5. **Nuke from Recovery Mode** — boot to Recovery, disable SIP, remove container, re-enable SIP

**Note:** Safari may spontaneously recover after a few days of use or after an OS update. This is consistent with container corruption that the OS eventually self-heals.

On a headless Mac with the phantom-click issue (clicking Dock triggers Apple menu), the user may *think* they're clicking a URL in the browser but actually triggering the top-left menu. This is not a network issue — it's the click-coordinate bug.

**Test:** Type a URL directly in Safari's address bar and press Enter (no mouse click). If the page loads, the issue is click coordinates, not network.

**Fix:** See main SKILL.md — BetterDisplay or HDMI dummy plug.

### 11. Selective Interception Pattern (China Mobile)

Some domains are intercepted by China Mobile, some are not:

| Domain | curl result | Safari result |
|--------|-------------|---------------|
| speedtest.net | HTTP 200 | "Not Private" (cert intercept) |
| huggingface.co | HTTP 200 (CloudFront) | "can't establish" (TLS block) |
| google.com | HTTP 200 | Works |
| fast.com | Works | "Not Private" (cert intercept) |
| hf-mirror.com | Works (via CDN) | "Not Private" (cert intercept) |

The interception is per-domain, not based on IP. Same CloudFront IP range may be blocked for one domain and allowed for another.

**Safari error messages as diagnostic signal:**
- **"This Connection Is Not Private"** → certificate interception (MITM) by carrier. Safari shows the cert details, user can click "Visit Website" to bypass.
- **"Safari can't establish a secure connection"** → TCP/TLS handshake failure or network extension blocking. Safari cannot even reach the server. The "Visit Website" button is NOT present — the page entirely failed to load.
- If curl works but Safari shows "can't establish" → suspect **Safari sandbox corruption** or **Speedify NE** (see sections 8 and 10).

| Domain | curl result | Safari result | Error type |
|--------|-------------|---------------|------------|
| speedtest.net | HTTP 200 | "Not Private" (cert intercept) | Certificate |
| huggingface.co | HTTP 200 (CloudFront) | "can't establish" (TLS block) | Connection |
| google.com | HTTP 200 | Works | — |
| fast.com | Works | "Not Private" (cert intercept) | Certificate |
| bing.com | HTTP 200 | "can't establish" (container corruption) | Connection |

In this session, all domains worked via curl. The "can't establish" errors for huggingface.co and bing.com were caused by Safari sandbox container corruption (see section 10), **not** by selective blocking.

## Systematic Diagnostic (run on headless Mac via SSH)

```bash
echo "=== 1. Basic connectivity ==="
ping -c 2 -W 3 8.8.8.8
echo "=== 2. HTTP via curl ==="
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 https://google.com
echo "=== 3. IPv4-only curl ==="
curl -4 -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 https://google.com
echo "=== 4. Compare HTTP/2 vs HTTP/1.1 ==="
curl --http2 -s -o /dev/null -w "HTTP/2: %{http_code} %{time_total}s\n" --max-time 10 https://huggingface.co
curl --http1.1 -s -o /dev/null -w "HTTP/1.1: %{http_code} %{time_total}s\n" --max-time 10 https://huggingface.co
echo "=== 5. IPv6 status ==="
ifconfig en7 | grep inet6
echo "=== 6. QUIC status ==="
sudo defaults read /Library/Preferences/com.apple.networkd EnableQuic 2>&1
echo "=== 7. Proxy settings ==="
networksetup -getwebproxy "iPhone USB"
echo "=== 8. Plain HTTP test ==="
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" --max-time 10 http://neverssl.com
echo "=== 9. DNS resolution from browser perspective ==="
nslookup google.com 1.0.0.1
```

If items 1-5 pass (including Python urllib returning 200) but Safari still fails, the cause is almost certainly:

1. **Safari sandbox container corruption** (section 10) → recommend using Brave Browser instead
2. **Click coordinate issue** (headless Mac) → the page loaded but the user couldn't click the address bar properly
3. **Certificate interception** → User must click "Visit Website" in Safari via Screen Sharing
