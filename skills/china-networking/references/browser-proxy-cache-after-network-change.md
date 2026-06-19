# Browser Proxy Cache After Network Change

When switching networks (ship WiFi → BT tethering → iPhone USB → different WiFi), Chromium-based browsers (Yandex, Brave, Chrome) cache old system proxy settings in their Network Service process. Disabling the system proxy via `networksetup` on the Wi-Fi service is NOT sufficient if the OS selects a different network service as active.

## Symptoms

- `curl` works (baidu.com returns 200, 8.8.8.8 pings fine)
- Browsers show `ERR_PROXY_CONNECTION_FAILED`
- System proxy shows `Enabled: No` on Wi-Fi service
- `networksetup -listnetworkserviceorder` shows a different service (ZTE, iPhone USB, etc.) at the top

## Fix

```bash
# 1. Kill ALL browser processes (not just window)
killall "Brave Browser" "Yandex" "Safari" 2>/dev/null
# Also kill background helpers
pgrep -li "brave\|yandex\|chrome" 2>/dev/null | awk '{print $1}' | xargs kill -9 2>/dev/null
sleep 2

# 2. Disable proxy on ALL network services (not just Wi-Fi)
for svc in $(networksetup -listallnetworkservices 2>/dev/null | grep -v "^\*" | grep -v "An asterisk"); do
    networksetup -setwebproxystate "$svc" off 2>/dev/null
    networksetup -setsocksfirewallproxystate "$svc" off 2>/dev/null
done

# 3. Relaunch Chromium browsers WITH --no-proxy-server flag
open -a "Brave Browser" --args --no-proxy-server
open -a "Yandex" --args --no-proxy-server
# Safari doesn't support --no-proxy-server, relies on system settings

# 4. Verify
curl -s --max-time 5 https://bing.com -o /dev/null -w "%{http_code}\n"
# Should return 200 (not 000 or ERR_PROXY_CONNECTION_FAILED)
```

## For Chromium automation (CDP browsers)

When launching Brave/Chrome/Yandex with `--remote-debugging-port` for CDP automation, ALWAYS also pass `--no-proxy-server` unless you explicitly need the proxy:

```bash
open -a "Brave Browser" --args --remote-debugging-port=9222 --no-proxy-server
```

This prevents the browser from caching stale proxy settings that break when the network changes mid-session.

## Root cause

macOS has multiple network services (Wi-Fi, USB, BT, Thunderbolt Bridge, ZTE, Shadowrocket TUN). The system routes traffic through the first active service in the network service order. When you switch networks (e.g. from ship WiFi to iPhone BT tethering), the active service changes. `networksetup -getwebproxy Wi-Fi` shows the proxy setting for the Wi-Fi service specifically — not for the currently active service. The proxy may still be enabled on the now-inactive service, but the browser's Network Service process cached the proxy configuration before the switch and doesn't re-check.

The `--no-proxy-server` flag tells Chromium to never use a system proxy, regardless of network state.

## Verified test (this Mac)

| Action | Result |
|--------|--------|
| Ship WiFi → BT tethering | SSH tunnel broke, proxy 1080/8888 unreachable |
| `networksetup -setwebproxystate Wi-Fi off` | No effect on browsers (different active service) |
| Kill + relaunch Brave with `--no-proxy-server` | ✅ bing.com loaded: "Search - Microsoft Bing" |
| Safari without flag | Still broken (not Chromium, didn't support flag) |
| System-wide proxy disable on all services | ✅ Both browsers work |
