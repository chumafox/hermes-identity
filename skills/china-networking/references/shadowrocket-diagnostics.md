# Shadowrocket Diagnostics & Speed Testing Through Proxy Chains

## Shadowrocket Diagnostics (headless Mac)

When a headless Mac runs Shadowrocket but internet seems slow:

```bash
# Check Shadowrocket status
ssh <host> "source ~/.zshrc && sr status"

# Check routing mode (Config=Rule, Proxy=Global)
ssh <host> 'plutil -p ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist | grep GlobalRoutingMethod'

# Switch to Global Proxy mode
ssh <host> 'defaults write ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket "group.com.liguangming.GlobalRoutingMethod" -string "Proxy"'

# Check selected server
ssh <host> 'plutil -p ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist | grep -i SelectedServer'

# List all servers in subscription
ssh <host> 'python3 -c "
import plistlib
with open(\"/tmp/servers.plist\", \"rb\") as f:
    data = plistlib.load(f)
for obj in data.get(\"\$objects\", []):
    if isinstance(obj, str) and len(obj) > 5 and not obj.startswith(\"http\") and not obj.startswith(\"ss:\"):
        print(obj)
"'

# Decode subscription URL (if dead, returns placeholder servers)
echo '<base64>' | base64 -d

# Restart Shadowrocket
ssh <host> "source ~/.zshrc && sr off && sleep 2 && sr on"

# Kill and restart VPN process (if stuck)
ssh <host> "killall -9 MacPacketTunnel Shadowrocket 2>/dev/null; sleep 1; source ~/.zshrc && sr on"
```

## Speed Testing Through Proxy Chains

When testing internet speed through a multi-hop chain (Air → SSH tunnel → headless Mac → Shadowrocket → proxy server):

### Local network speed (between Macs)
```bash
# On target Mac: start iperf3 server
ssh <host> "iperf3 -s -1 -D"

# On source Mac: run client
iperf3 -c <target-ip> -t 10
```

### Internet speed through SOCKS5 tunnel
```bash
# Download test (Cloudflare)
curl --socks5-hostname 127.0.0.1:1080 -s -o /dev/null -w "Download: %{speed_download} B/s\n" --max-time 30 "https://speed.cloudflare.com/__down?bytes=52428800"

# Multiple samples for accuracy
for i in 1 2 3; do
  curl --socks5-hostname 127.0.0.1:1080 -s -o /dev/null -w "%{speed_download}\n" --max-time 20 "https://speed.cloudflare.com/__down?bytes=26214400"
done
```

### Speedtest on headless Mac via SSH
```bash
# Install speedtest-cli
ssh <host> "pip3 install speedtest-cli --break-system-packages"

# Run (SSL_CERT_FILE needed if certs not found)
ssh <host> "SSL_CERT_FILE=/opt/homebrew/lib/python3.14/site-packages/certifi/cacert.pem speedtest --secure 2>&1"

# Ookla speedtest binary (does NOT work through SOCKS5 proxy — DNS fails)
# Use direct internet or system proxy instead
```

## Pitfalls

- **Ookla speedtest binary** cannot resolve servers through SOCKS5 proxy — use `speedtest-cli` (Python) instead
- **speedtest-cli** may fail with SSL_CERT_VERIFY_FAILED on macOS — set `SSL_CERT_FILE` to certifi's cacert.pem
- **curl-based tests** to httpbin.org or GitHub Releases may show low speed even when proxy works — these domains may be routed Direct by proxy rules. Use Cloudflare speed test or speedtest.net servers instead
- **iperf3** measures raw WiFi/LAN speed, not internet speed — combine with curl-based tests for full picture
- **Speedtest.app** (GUI) on macOS cannot be driven from CLI — use terminal tools instead
- **Subscription dead check:** if Shadowrocket servers all point to `127.0.0.1:12345` with placeholder names, the subscription URL is dead — update it in the app
