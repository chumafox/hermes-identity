# Proxy/VPN Leak Verification — macOS

Проверка, что система (macOS) не утекает DNS, WebRTC, timezone или локальный IP,
когда работает через прокси/VPN для региона США.

## Быстрая проверка (curl)

```bash
# IP + геолокация
curl -s https://ipinfo.io/json

# Проверить что DNS не утекает (должен быть Cloudflare/Google US)
# Сравни с: networksetup -getdnsservers Wi-Fi (должен быть чист)
```

## Полная проверка в браузере

Открыть `https://ipleak.net` и проверить:

- **Your IP addresses** — должен быть US IP (не NL, не CN)
- **WebRTC detection** — не должен показывать реальный IP (Brave блокирует по умолчанию)
- **DNS Addresses** — все серверы должны быть Cloudflare/Google **в США**
- **IPv6** — должен быть недоступен или отключён

## Проверка timezone (JS)

Главный сигнал для Google — несовпадение IP и timezone.

```javascript
// JS timezone — должен совпадать с регионом IP
Intl.DateTimeFormat().resolvedOptions().timeZone

// Должно быть: America/Chicago или America/New_York
// НЕ ДОЛЖНО быть: Asia/Shanghai
```

## System timezone (macOS)

```bash
# Проверить
date
systemsetup -gettimezone

# Сменить на US Central (Техас)
sudo systemsetup -settimezone "America/Chicago"

# Альтернатива при error -99 (более надёжно):
sudo ln -sf /var/db/timezone/zoneinfo/America/Chicago /etc/localtime

# Или US East
sudo systemsetup -settimezone "America/New_York"

# Или US West
sudo systemsetup -settimezone "America/Los_Angeles"
```

**Питфолл:** `systemsetup -settimezone` может выдать `Error: -99` — это нормально, timezone меняется, несмотря на ошибку. Проверить можно `date` и в браузере `Intl.DateTimeFormat().resolvedOptions().timeZone`.

**Питфолл:** timezone может сброситься обратно на Asia/Shanghai при некоторых условиях. После смены всегда проверять `date` или `python3 -c "from datetime import datetime; print(datetime.now().astimezone().tzinfo)"`.

После смены — перепроверить в браузере (нужен reload страницы, т.к. timezone может кешироваться).

## Cookie clearing after proxy change

После смены прокси/региона — Google cookie содержат старую сессию. Почистить через CDP:

```bash
curl -s -X PUT "http://localhost:9222/json/new" | python3 -c "import sys,json; print(json.load(sys.stdin)['webSocketDebuggerUrl'])"
# → ws://localhost:9222/devtools/page/<ID>
```

Через Python `websockets`:
```python
import json, asyncio, websockets
async def main():
    async with websockets.connect("ws://localhost:9222/devtools/page/<ID>") as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        await ws.recv()
        await ws.send(json.dumps({"id": 2, "method": "Network.clearBrowserCookies", "params": {}}))
        print(await ws.recv())
asyncio.run(main())
```

Или одной командой:
```python
python3 -c "
import json, asyncio, websockets
async def main():
    import httpx
    tab = httpx.put('http://localhost:9222/json/new').json()
    async with websockets.connect(tab['webSocketDebuggerUrl']) as ws:
        for m in [{'id':1,'method':'Network.enable','params':{}}, {'id':2,'method':'Network.clearBrowserCookies','params':{}}]:
            await ws.send(json.dumps(m)); print(json.loads(await ws.recv()))
asyncio.run(main())
"
```

## CDP browser fallback when browser_navigate fails

Если `browser_navigate` выдаёт `"CDP WebSocket connect failed: HTTP error: 404 Not Found"`, значит:
- URL в `config.yaml` (секция `browser.cdp_url`) закеширован при старте TUI
- После перезапуска Brave изменился WebSocket URL бразуера
- `hermes config set browser.cdp_url <новый_WS_URL>` сохраняет в config.yaml, но **текущая TUI-сессия не перечитывает config** — изменение вступит в силу только при следующем старте TUI

**Workaround:** использовать прямой CDP page-level WebSocket (код ниже) — он не требует конфига, подключается к любому живому page target'у через `http://localhost:9222/json`.

**Workaround:** использовать прямой CDP page-level WebSocket.

```python
import json, asyncio, websockets, httpx

async def main():
    # 1. Получить существующий page target
    tabs = httpx.get("http://localhost:9222/json").json()
    page = next(t for t in tabs if t["type"] == "page")
    
    # 2. Подключиться напрямую к page WS
    async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
        msg_id = 1
        async def send(m, p=None):
            nonlocal msg_id
            i = msg_id; msg_id += 1
            await ws.send(json.dumps({"id": i, "method": m, "params": p or {}}))
            return json.loads(await ws.recv())
        
        # 3. Навигация
        await send("Page.enable")
        await send("Page.navigate", {"url": "https://ipleak.net"})
        
        # 4. Ждать загрузки
        for _ in range(20):
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.0))
                if msg.get("method") == "Page.frameStoppedLoading":
                    break
            except (asyncio.TimeoutError, json.JSONDecodeError):
                pass
        
        # 5. Получить контент
        result = await send("Runtime.evaluate", {
            "expression": "document.body?.innerText || ''",
            "returnByValue": True
        })
        print(result["result"]["result"]["value"][:2000])

asyncio.run(main())
```

**Новая вкладка** (если закрыты все):
```bash
curl -s -X PUT "http://localhost:9222/json/new?url=https://ipleak.net" | python3 -c "
import sys,json
t=json.load(sys.stdin)
print(t['webSocketDebuggerUrl'])
print(t['id'])
"
```

## ipleak.net dual-IP artifact

На странице ipleak.net есть **две разные секции**, показывающие разные IP:

- **"Your IP addresses"** — реальный IP твоего браузера. Прокси работает корректно.
- **"IP Address details"** — может показывать другой IP (вторичный запрос к geo-API или IP сервера дата-центра). Не является утечкой.

Если "Your IP addresses" показывает US IP, а "IP Address details" = NL — всё в порядке. Ориентироваться на первую секцию.

## Go CLI proxy handling

`agy` / `antigravity` — Go-приложения. Go **не поддерживает** `SOCKS5_PROXY` (все_прокси) через переменные окружения. Работает только `HTTP_PROXY` / `HTTPS_PROXY` для **HTTP(S) прокси**, НЕ для SOCKS5.

Если системный прокси — SOCKS5 (как в Ship mode):

```bash
# Не работает — Go не знает SOCKS5
SOCKS5_PROXY=socks5://127.0.0.1:1080 agy ...
ALL_PROXY=socks5://127.0.0.1:1080 agy ...

# Решения:
# 1) proxychains-ng
brew install proxychains-ng
proxychains4 agy --model "gemini-2.5-flash" -p "prompt"

# 2) HTTP proxy bridge (tinyproxy) на localhost
# tinyproxy должен быть настроен отдельно
HTTPS_PROXY=http://127.0.0.1:8888 HTTP_PROXY=http://127.0.0.1:8888 agy ...

# 3) TUN mode (sing-box) — перехватывает весь трафик на уровне ядра
# Go-приложения идут через TUN автоматически
```

**Проверка:** если `curl -s --max-time 5 https://ifconfig.me` работает, но `agy` зависает — скорее всего проблема в том, что Go не использует SOCKS5.

## Дополнительные проверки

```javascript
// Язык браузера
navigator.languages  // должен быть ['en-US', 'en']

// Платформа
navigator.platform  // MacIntel — нормально для macOS

// WebRTC утечки
const pc = new RTCPeerConnection({iceServers: [{urls: 'stun:stun.l.google.com:19302'}]});
pc.createDataChannel('test');
// Если onicecandidate не возвращает локальный IP — WebRTC заблокирован
```

## Типичные проблемы

| Симптом | Причина | Решение |
|---------|---------|---------|
| IP: US, timezone: Asia/Shanghai | macOS timezone не сменена | `sudo systemsetup -settimezone "America/Chicago"` (error -99 игнорировать) |
| DNS показывает китайские DNS | Системный DNS не через прокси | Проверить `networksetup -getdnsservers Wi-Fi` |
| ipleak.net показывает NL а не US | Прокси идёт через NL ноду | Сменить прокси-сервер на US-ноду |
| WebRTC показывает реальный IP | WebRTC не заблокирован | Brave: настройки → WebRTC = disable non-proxied UDP |
| Browser tools не работают (404 WS) | CDP URL изменился после рестарта | Использовать page-level WebSocket напрямую |
| Go CLI (agy/antigravity) зависает | Go не поддерживает SOCKS5 | proxychains или HTTP_PROXY |
| Google API выдаёт 400 location error | Не сеть — аккаунт/billing | См. google-service-region-unblock.md → API-Level Error |
