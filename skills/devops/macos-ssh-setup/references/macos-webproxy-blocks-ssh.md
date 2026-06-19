# macOS Web Proxy Blocks SSH

## Symptom
- SSH connects successfully from localhost but times out from the network
- `nc -vz <ip> 22` hangs
- `lsof -i :22 -P -n` shows `*:22 (LISTEN)` — port is open
- `sudo systemsetup -getremotelogin` shows `Remote Login: On`
- Connected devices can ping each other successfully

## Cause
macOS System Preferences → Network → Wi-Fi (or any active service) may have
**Web Proxy** enabled with an **empty server** (`Server:` blank, `Port: 0`).

macOS treats `Enabled: Yes` with empty Server/Port as a **blocking proxy** —
it intercepts all TCP connections (including SSH) and immediately drops them
because the proxy server address is invalid.

## Detection
```bash
# Check all network services for proxy state
networksetup -getwebproxy "Wi-Fi"          # most common culprit
networksetup -getwebproxy "Thunderbolt Bridge"
networksetup -getwebproxy "iPhone USB"

# Look for: Enabled: Yes with empty Server
```

## Fix
```bash
sudo networksetup -setwebproxystate "Wi-Fi" off
```

Replace `"Wi-Fi"` with the actual service name. Repeat for all services showing
`Enabled: Yes` with empty server.

## Prevention
Check proxy state as a routine part of SSH troubleshooting — it's a macOS quirk
that's easy to miss because everything else (ping, port listeners, firewall state)
looks normal.
