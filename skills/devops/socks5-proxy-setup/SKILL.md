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

## Go CLI клиенты и HTTP_PROXY

**Проблема:** Go-клиенты не поддерживают `socks5://` в `HTTP_PROXY` — Go ожидает HTTP-прокси (CONNECT). `ALL_PROXY=socks5://...` тоже игнорируется большинством Go-приложений.

### Решение: sing-box mixed inbound (проще всего)

Добавить в sing-box inbound типа `mixed` — он слушает и HTTP (CONNECT), и SOCKS5 на одном порту:

```json
{
  "type": "mixed",
  "tag": "mixed-in",
  "listen": "127.0.0.1",
  "listen_port": 1083
}
```

После перезапуска sing-box:
```bash
export HTTP_PROXY=http://127.0.0.1:1083
export HTTPS_PROXY=http://127.0.0.1:1083
agy  # работает
```

Трафик: Go-app → localhost:1083 (HTTP CONNECT) → sing-box → outbound → internet.
Go-приложение видит HTTP-прокси (работает), sing-box внутри может форвардить через SOCKS5.

**Проверка:** `curl -s --proxy http://127.0.0.1:1083 https://ipinfo.io/json` — должен вернуть US IP.

**Актуально для:** agy (Antigravity CLI), Claude Code, OpenCode, любые Go-бинарники.

### Альтернатива: Python HTTP→SOCKS5 мост (когда sing-box не вариант)

Если нет sing-box, можно поднять простой HTTP CONNECT прокси, который форвардит в SOCKS5:

```python
# /tmp/http2socks.py — HTTP CONNECT прокси, форвардит в SOCKS5
import socket, select, struct

SOCKS_HOST, SOCKS_PORT = '127.0.0.1', 1080
BIND_PORT = 18888

def socks5_connect(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((SOCKS_HOST, SOCKS_PORT))
    s.sendall(b'\x05\x01\x00')
    assert s.recv(2)[0] == 5
    hn = host.encode()
    req = b'\x05\x01\x00\x03' + bytes([len(hn)]) + hn + struct.pack('>H', port)
    s.sendall(req)
    assert s.recv(4)[:2] == b'\x05\x00'
    t = s.recv(1)[0]  # skip remaining addr
    extra = {1:6, 3:s.recv(1)[0]+2, 4:18}[t]
    if extra: s.recv(extra)
    return s

def handle(c):
    try:
        d = c.recv(4096)
        if not d: return
        m, url = d.split(b'\r\n')[0].decode().split()[:2]
        if m == 'CONNECT':
            h, p = url.split(':'); p = int(p)
            r = socks5_connect(h, p)
            c.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            socks = [c, r]
            while socks:
                rr, _, _ = select.select(socks, [], [], 300)
                for s in rr:
                    o = r if s is c else c
                    try:
                        ch = s.recv(65536)
                        if not ch: raise ConnectionError
                        o.sendall(ch)
                    except: socks.remove(s); s.close()
        else: c.sendall(b'HTTP/1.1 400\r\n\r\n')
    except: pass
    finally:
        try: c.close()
        except: pass

s = socket.socket()
s.setsockopt(1, 2, 1)
s.bind(('127.0.0.1', BIND_PORT))
s.listen(50)
while True:
    c, _ = s.accept(); handle(c)
```

Запуск:
```bash
python3 /tmp/http2socks.py &
export HTTP_PROXY=http://127.0.0.1:18888
export HTTPS_PROXY=http://127.0.0.1:18888
# Теперь запускай любой Go-клиент
agy  # или другой CLI
```

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
