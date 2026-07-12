# Leak Testing — Verify Proxy/VPN Isolation

Проверка, что трафик полностью идёт через прокси, и ни один системный сервис не утекает наружу.

## Что проверять (наиболее критичные сигналы)

| Вектор | Инструмент | Что смотреть |
|--------|-----------|-------------|
| **IP** | `ipleak.net` / `ipinfo.io` | IP должен быть прокси, не твой реальный |
| **DNS** | `ipleak.net` | Все DNS-серверы должны быть через прокси (Cloudflare, Google), не ISP |
| **WebRTC** | `ipleak.net` → WebRTC detection / `browserleaks.com/webrtc` | Не должен показывать твой реальный IP |
| **IPv6** | `ipleak.net` | Должен быть недоступен (error) — иначе IPv6 может ходить в обход прокси |
| **Timezone** | `Intl.DateTimeFormat().resolvedOptions().timeZone` в консоли браузера | Должна быть US, не Asia/Shanghai ⚠️ |
| **Language** | `navigator.languages` | `en-US` |
| **Screen** | `screen.width` / `screen.height` | Реальные размеры монитора — не критично, но Google видит |
| **User-Agent** | `navigator.userAgent` | macOS — нормально для US |

## Быстрая проверка через CDP (Brave)

Когда `browser_navigate` не работает из-за stale WebSocket URL:

### 1. Получить актуальный WebSocket URL
```bash
curl -s http://localhost:9222/json/version | python3 -m json.tool
# → webSocketDebuggerUrl: ws://localhost:9222/devtools/browser/<NEW_ID>
```

### 2. Обновить конфиг Hermes
```bash
hermes config set browser.cdp_url "ws://127.0.0.1:9222/devtools/browser/<NEW_ID>"
```

### 3. Если tools всё ещё не работают — прямой CDP через Python websockets
```python
import asyncio, json, httpx, websockets

# Создать новую вкладку
r = httpx.put("http://localhost:9222/json/new?url=https://ipleak.net")
tab_id = r.json()["id"]

async with websockets.connect(f"ws://localhost:9222/devtools/page/{tab_id}") as ws:
    async def cdp(method, params=None):
        await ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        return json.loads(await ws.recv())

    await cdp("Page.enable")
    await asyncio.sleep(5)

    result = await cdp("Runtime.evaluate", {
        "expression": "document.body.innerText.substring(0, 5000)",
        "returnByValue": True
    })
    print(result["result"]["result"]["value"])
```

### 4. WebRTC-тест через CDP
```javascript
(async () => {
    let ips = [];
    const pc = new RTCPeerConnection({
        iceServers: [{urls: 'stun:stun.l.google.com:19302'}]
    });
    pc.createDataChannel('test');
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await new Promise(resolve => {
        pc.onicecandidate = e => {
            if (e.candidate) {
                const m = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
                if (m) ips.push(m[1]);
            } else resolve();
            setTimeout(resolve, 3000);
        };
    });
    pc.close();
    return JSON.stringify(ips);
})()
// → [] = нет утечки WebRTC
// → [твой реальный IP] = утечка!
```

### 5. Проверка timezone
```javascript
Intl.DateTimeFormat().resolvedOptions().timeZone
// Должно быть: America/New_York или America/Los_Angeles
// НЕ должно быть: Asia/Shanghai
```

## Критические находки из практики

### Timezone — отдельная утечка
Даже при идеальном IP/DNS/WebRTC через US-прокси, **Asia/Shanghai** timezone выдаёт Google, что ты в Китае. Исправить:
```bash
sudo systemsetup -settimezone "America/New_York"
```

### DNS-запросы могут идти мимо прокси
macOS может слать DNS напрямую, если DNS-серверы жёстко прописаны в сетевых настройках. Проверить:
```bash
networksetup -getdnsservers Wi-Fi
# Должны быть 8.8.8.8, 1.1.1.1 или через прокси, не пусто
networksetup -getdnsservers "USB 10/100/1000 LAN"  # en5
```

### IPv6 — полное отключение
```bash
networksetup -setv6off Wi-Fi
networksetup -setv6off "USB 10/100/1000 LAN"
```

### Proxy-сервер в правильной стране
IP прокси в Нидерландах → Google видит NL. Нужен сервер в США для US-видимости. Hysteria2-сервер должен быть настроен на US-ноду.

## Инструменты
- [ipleak.net](https://ipleak.net) — IP, DNS, WebRTC, IPv6
- [browserleaks.com](https://browserleaks.com) — WebRTC, Canvas, всё
- [ipinfo.io](https://ipinfo.io/json) — быстрый JSON с IP/локацией
- `ipleak.net/webrtc/` — отдельная страница WebRTC-теста
