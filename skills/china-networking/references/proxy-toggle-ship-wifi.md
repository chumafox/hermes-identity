# proxy_toggle — Ship WiFi / BT Tethering Switch

`~/bin/proxy_toggle` — one-command toggle between ship WiFi (SOCKS5 via SSH tunnel to pro Mac) and direct access (BT tethering).

## Usage

```bash
proxy_toggle on      # ship WiFi mode: SOCKS5 via SSH tunnel
proxy_toggle off     # BT tethering mode: direct access, no proxy
proxy_toggle         # show current status
```

## What it does

### proxy_toggle on
1. Checks pro Mac (192.168.103.70) is reachable
2. Starts SSH tunnel: `ssh -D 1080 admin@admin-remote`
3. Sets system SOCKS5 proxy: `127.0.0.1:1080`
4. Ensures HTTPS proxy is OFF (not needed — SOCKS5 handles both)

### proxy_toggle off
1. Kills SSH tunnel (via control socket + PID)
2. Disables ALL system proxies: HTTP, HTTPS, SOCKS5

## Why this exists

On a cruise ship with two Macs (dispo + pro), internet flows:

dispo → ship WiFi OR BT tethering → pro Mac (via SSH) → Shadowrocket TUN → ZTE modem

When switching from ship WiFi to BT tethering, the pro Mac becomes unreachable, SSH tunnel dies, and browsers cache stale proxy settings. The toggle handles cleanup and reconfiguration.

## Browser proxy cache

Chromium-based browsers (Brave, Yandex, Chrome) cache the system proxy setting at launch time. When the proxy dies mid-session:

1. Run `proxy_toggle off`
2. Restart browsers with `--no-proxy-server` flag:
   ```bash
   killall "Brave Browser"; open -a "Brave Browser" --args --no-proxy-server
   killall Yandex; open -a Yandex --args --no-proxy-server
   ```
3. To restore proxy: `proxy_toggle on` then restart browsers without the flag

For Safari, just killing and reopening is sufficient — no `--no-proxy-server` flag exists.

## HTTPS proxy trap

macOS has **separate** proxy settings for HTTP and HTTPS. Disabling only HTTP proxy (`-setwebproxystate`) does NOT disable HTTPS proxy. Always disable both:

```bash
networksetup -setwebproxystate Wi-Fi off       # HTTP
networksetup -setsecurewebproxystate Wi-Fi off  # HTTPS
networksetup -setsocksfirewallproxystate Wi-Fi off  # SOCKS5
```

Always verify via `scutil --proxy` (shows all proxy types at once) rather than `networksetup` (one query per service).
