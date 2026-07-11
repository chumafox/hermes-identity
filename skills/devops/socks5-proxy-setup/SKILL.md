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

## Go CLI clients и нечитаемые env vars

**Проблема:** Go-клиенты (agy/Antigravity CLI, некоторые тулы от Google) игнорируют `socks5h://` в `HTTP_PROXY`. Переменная `HTTP_PROXY=socks5h://127.0.0.1:1080` не работает — Go ожидает HTTP прокси.

### agy (Antigravity CLI) — известный баг #113

`agy` использует **кастомный HTTP транспорт** для OAuth token exchange — он **не читает** `http.ProxyFromEnvironment`. Даже если поднять HTTP→SOCKS5 мост и выставить `HTTP_PROXY=http://127.0.0.1:18888` — agy всё равно идёт напрямую.
Баг зарепорчен upstream: https://github.com/google-antigravity/antigravity-cli/issues/113

**Единственное надёжное решение для agy — TUN/VPN на уровне сети.** Переменные окружения и прокси-мосты не помогают. Нужно, чтобы TCP-соединение к `172.217.0.0/16` (Google) физически не могло уйти мимо TUN.

### TUN-based решение (sing-box)

Если sing-box TUN не перехватывает Google IP (`route -n get 172.217.x.x` показывает `interface: en0`, а не `utun`), добавить split-default маршруты:

```bash
sudo route add -net 0.0.0.0/1 -interface utun9
sudo route add -net 128.0.0.0/1 -interface utun9
```

Причина: `auto_route` + `strict_route` в gvisor стеке на macOS не всегда устанавливает TUN как default route. Split-default (`0/1` + `128/1`) покрывает весь IPv4 адресный простор — любой IP попадает либо в первый, либо во второй диапазон.

После добавления — проверить:
```bash
route -n get 172.217.216.95
# Должен показать: interface utun9
curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" https://oauth2.googleapis.com/token
# Должен вернуть 404 (но не timeout!)
```

**Перманентный фикс** — прописать в конфиг sing-box:

```json
"inbounds": [{
  "type": "tun",
  "auto_route": true,
  "strict_route": true,
  "stack": "gvisor",
  "route_address": ["0.0.0.0/1", "128.0.0.0/1"],
  "route_exclude_address": [
    "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12",
    "192.168.0.0/16", "224.0.0.0/4", "240.0.0.0/4"
  ]
}]
```

### Альтернатива: FakeIP DNS (самое чистое, но сложное решение)

Вместо split-default — перехватить DNS через sing-box с FakeIP. Он отдаёт системе фиктивный IP (из `198.18.0.0/15`) вместо реального IP Google. Подсеть гарантированно завернётся в TUN:

```json
"dns": {
  "servers": [
    {"tag": "fakeip", "address": "fakeip"}
  ],
  "rules": [
    {"outbound": "any", "server": "fakeip"}
  ],
  "fakeip": {
    "enabled": true,
    "inet4_range": "198.18.0.0/15"
  }
}
```

Параметры `sniff: true` и `sniff_override_destination: true` в inbound TUN заставляют sing-box вычитывать домен из TLS SNI пакета, даже если запрос пришёл по IP.

### Итог: что делать с "непослушными" Go-клиентами

| Уровень | Метод | Работает для agy? |
|---------|-------|-------------------|
| env vars | `HTTP_PROXY=http://...` | НЕТ (баг #113) |
| env vars | `ALL_PROXY=socks5://...` | НЕТ |
| HTTP→SOCKS5 bridge | порт 18888 | НЕТ |
| **TUN split-default** | route add 0/1 + 128/1 | **ДА** |
| **FakeIP DNS** | sing-box | **ДА** |

**Вывод:** для agy в Китае единственный рабочий метод — TUN, который гарантирует что трафик до Google не уйдёт напрямую в en0.

### Решение: HTTP→SOCKS5 мост на Python (чистый stdlib, без зависимостей):

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
