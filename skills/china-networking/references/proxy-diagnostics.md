# Proxy Diagnostics (China Networking)

How to check if a proxy/VPN is actually working on macOS in China, not just running.

## The One-Shot Diagnostic Command

Run this on the restricted Mac to test all proxy layers at once:

```bash
echo "=== ПРОЦЕССЫ ===" && ps aux | grep -iE "v2ray|shadow|microsocks|tinyproxy|ssh.*D\b" | grep -v grep && echo "=== ПОРТЫ ===" && for p in 1080 1082 1086 1087 1088 7890 7891 8001 10800; do lsof -i :$p 2>/dev/null | tail -1 | awk '{print "порт "$1": "$9" ("$1")"}' && (curl -s -o /dev/null --connect-timeout 2 --max-time 4 http://127.0.0.1:$p/ 2>/dev/null && echo "  отклик: да" || echo "  отклик: нет"); done && echo "=== ПРЯМОЙ ДОСТУП (без прокси) ===" && curl -s -o /dev/null -w "httpbin: %{http_code} (%{time_total}s)\n" --max-time 10 http://httpbin.org/ip 2>&1 && curl -s -o /dev/null -w "github: %{http_code} (%{time_total}s)\n" --max-time 10 https://github.com 2>&1 && echo "=== ЧЕРЕЗ SOCKS5 ===" && for p in 1080 1082; do curl -x socks5h://127.0.0.1:$p -s -o /dev/null -w "socks5 $p: %{http_code} (%{time_total}s)\n" --max-time 10 https://github.com 2>&1; done && echo "=== ЧЕРЕЗ HTTP ===" && for p in 1080 1082; do curl -x http://127.0.0.1:$p -s -o /dev/null -w "http $p: %{http_code} (%{time_total}s)\n" --max-time 10 https://github.com 2>&1; done && echo "=== GIT PROXY ===" && echo "http: $(git config --global --get http.proxy 2>/dev/null || echo 'не задан')" && echo "https: $(git config --global --get https.proxy 2>/dev/null || echo 'не задан')" && echo "=== DNS GITHUB ===" && nslookup github.com 2>/dev/null | grep -A1 "Name:" || host github.com 2>/dev/null
```

## Interpreting the Output

| Signal | Meaning |
|--------|---------|
| `000` on direct + `000` on proxy | No internet at all (ship WiFi down, cable not connected) |
| `000` direct but proxy `200` | Proxy is correctly routing traffic ✓ |
| `SSL_ERROR_SYSCALL` on TLS handshake | TCP tunnel is up but remote proxy node is disconnected |
| lsof shows port but curl says "отклик: нет" | Stale/zombie process — no actual proxying |
| `200` on httpbin + direct | Mac has unfiltered internet — proxy unnecessary |
| `503` on CONNECT tunnel (git pull) | Proxy is running but remote gateway rejects connection |

## Common Proxy Apps on macOS in China

| App | Process Name | Default Port(s) | TUN Interface | Notes |
|-----|-------------|----------------|---------------|-------|
| **Shadowrocket** | `MacPacketTunnel` | 1082 (SOCKS) | utun4 | Needs GUI to configure node; sub-process survives parent app quit |
| **V2rayU** | `v2ray` or `V2rayU` | 1087 (SOCKS), 8001 (HTTP) | utun4 | Config in `~/.V2rayU/` |
| **ClashX / Clash Meta** | `clash*` | 7890 (HTTP/SOCKS) | utun | Auto-route mode common |
| **Surge** | `Surge` | 6152 (HTTP/SOCKS) | utun | Paid only |

## Pitfalls

### MacPacketTunnel Zombie Process

Shadowrocket's network extension (`MacPacketTunnel`) continues running as a system process even after the Shadowrocket GUI is quit or crashed. Symptoms:
- `lsof -i :1082` shows `MacPacketTunnel` LISTEN
- `ifconfig utun4` shows UP
- curl to any external site returns `000` timeout or `SSL_ERROR_SYSCALL`

**Fix:** Relaunch Shadowrocket GUI and verify node connection:
```bash
open /Applications/Shadowrocket.app
# Check the green "Connected" indicator in the app window
```

### utun4 UP But No Traffic

When utun4 is UP and curl resolves github.com to `198.18.x.x` (TUN subnet) but gets `000` or `SSL_ERROR_SYSCALL`:
- The TUN interface IS routing traffic through the proxy app
- But the proxy app's **remote server connection** is broken (wrong node, expired subscription, server down)
- Fix: reconfigure the proxy app's remote node, not the network interface

### Shadowrocket Double Traffic

When `internet_pro` (SSH tunnel) AND Shadowrocket are both active on the same Mac, traffic may be double-proxied: SSH tunnel → Shadowrocket TUN → remote proxy → internet. This halves throughput. Disable one:
- For `internet_pro`: kill the SSH tunnel (`ssh -S /tmp/internet_pro.socks -O exit admin@admin-remote`)
- For Shadowrocket: quit the app (`osascript -e 'quit app "Shadowrocket"'`)

### Git Proxy Points to Dead Port

After a proxy app restart or IP change, `git config http.proxy` may still point to a port that no longer listens:
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```
If the proxy app provides its own TUN (utun4), you don't need git proxy at all — traffic is auto-routed.

### Local git proxy (in-repo config) survives global unset

`git config --global --unset` очищает только глобальный конфиг. Репозиторий может иметь **локальный** `http.proxy` в `.git/config`:
```bash
# Проверить оба уровня
git config --global --get http.proxy   # глобальный — может быть пусто
git config --local --get http.proxy    # локальный — может всё ещё висеть

# Удалить локальный
git config --local --unset http.proxy
git config --local --unset https.proxy
```

Проверять оба уровня при диагностике ошибки `CONNECT tunnel failed, response 503`.
