---
name: socks5-proxy-setup
description: "Set up microsocks SOCKS5 proxy on a headless Mac to share internet with iPhone/client devices over LAN. No app needed on client — just system proxy settings."
tags: [socks5, proxy, iphone, microsocks, headless-mac, networking]
---

# SOCKS5 Proxy Setup (microsocks)

Run a lightweight SOCKS5 server on a headless Mac so iPhone or other LAN devices can use it as a system proxy — no app required on the client.

## Quick start

```bash
# On the headless Mac (pro):
cd /tmp
curl -sL https://github.com/rofl0r/microsocks/archive/refs/tags/v1.0.4.tar.gz | tar xz
cd microsocks-1.0.4
cc -O2 -o /tmp/microsocks *.c -lpthread
sudo cp /tmp/microsocks /usr/local/bin/microsocks

# Start (port 1082, all interfaces):
nohup microsocks -i 0.0.0.0 -p 1082 > /dev/null 2>&1 &

# Verify:
nc -z 127.0.0.1 1082 && echo "✓ OK"
```

## Client setup (iPhone)

Settings → Wi-Fi → (i) next to network → HTTP Proxy → Manual:
- Server: `<headless-mac-IP>`
- Port: `1082`
- Authentication: Off

Works system-wide — Safari, apps, everything.

## Security

**microsocks runs without auth by default.** Anyone on the same LAN can use it. Options:

1. **No auth (default):** fine for trusted home/office LAN
2. **User/password:** `microsocks -i 0.0.0.0 -p 1082 -u admin -P <password>`
3. **Bind to specific IP:** `microsocks -i 192.168.103.70 -p 1082` (only that interface)

## Comparison: microsocks vs alternatives

| Tool | Type | Size | Built-in auth | Best for |
|------|------|------|---------------|----------|
| **microsocks** | SOCKS5 | ~30KB binary | yes | iPhone, lightweight |
| **tinyproxy** | HTTP proxy | ~100KB | yes | Older devices, HTTP-only |
| **SSH -D tunnel** | SOCKS5 | built-in | via SSH key | Single device, ad-hoc |

## Compatibility with existing Internet Pro

On this setup:
- **Internet Pro (inpro):** SSH tunnel dispo→pro, SOCKS5 on :1080, HTTP bridge on :8888
- **microsocks:** Direct SOCKS5 on :1082, for LAN clients (iPhone)
- **No conflict** — different ports, different purposes

## Pitfalls

- **Firewall:** macOS firewall may block incoming connections. Check with `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate`. Add exception or disable.
- **China network:** microsocks uses pro's internet. If pro is in China, blocked sites still won't load unless pro has its own proxy (V2rayU utun4).
- **No persistence:** `nohup` process dies on reboot. For auto-start, create a launchd plist.
- **Compilation:** `cc` (clang) is included with Xcode CLI tools (`xcode-select --install`). Without it, use `brew install microsocks`.

## Auto-start with launchd

```bash
cat > /tmp/com.microsocks.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.microsocks</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/microsocks</string>
        <string>-i</string>
        <string>0.0.0.0</string>
        <string>-p</string>
        <string>1082</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF
sudo cp /tmp/com.microsocks.plist /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.microsocks.plist
```
