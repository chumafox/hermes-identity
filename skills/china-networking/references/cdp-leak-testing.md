# Automated Leak Testing via CDP

Полная автоматическая проверка утечек через браузерный CDP (Chrome DevTools Protocol).
Используется, когда `browser_navigate` в Hermes TUI не работает (404 WebSocket).

## Prerequisites

- Python с библиотекой `websockets`
- Brave/Chrome запущен с `--remote-debugging-port=9222`
- Зависимости: `pip install websockets httpx` (обычно уже есть)

## Quick Test (IP + Timezone)

```python
python3 << 'PYEOF'
import json, asyncio, websockets, httpx

async def main():
    tab = httpx.put("http://localhost:9222/json/new?url=https://ipleak.net").json()
    async with websockets.connect(tab["webSocketDebuggerUrl"]) as ws:
        mid = 1
        async def s(m, p=None):
            global mid
            i = mid; mid += 1
            await ws.send(json.dumps({"id": i, "method": m, "params": p or {}}))
            return json.loads(await ws.recv())
        
        await s("Page.enable")
        # Wait for load
        for _ in range(20):
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), 1.0))
                if m.get("method") == "Page.frameStoppedLoading": break
            except: pass
        
        await asyncio.sleep(2)
        
        # IP
        r = await s("Runtime.evaluate", {"expression": 
            "document.body.innerText.match(/Your IP addresses[\\s\\S]{1,300}/)?.[0] || 'N/A'", "returnByValue": True})
        print("IP:", r["result"]["result"]["value"][:200])
        
        # Timezone
        r = await s("Runtime.evaluate", {"expression": "Intl.DateTimeFormat().resolvedOptions().timeZone", "returnByValue": True})
        print("TZ:", r["result"]["result"]["value"])
        
        # Languages
        r = await s("Runtime.evaluate", {"expression": "navigator.languages.join(',')", "returnByValue": True})
        print("Lang:", r["result"]["result"]["value"])
        
        # WebRTC
        r = await s("Runtime.evaluate", {"expression": """
(async()=>{let ips=[];try{let pc=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});
pc.createDataChannel('');let o=await pc.createOffer();await pc.setLocalDescription(o);
await new Promise(r=>{pc.onicecandidate=e=>{if(e.candidate){let m=e.candidate.candidate.match(/(\\d+\\.\\d+\\.\\d+\\.\\d+)/);if(m)ips.push(m[1])}else r()};setTimeout(r,3000)});
pc.close()}catch(e){}return JSON.stringify(ips)})()""", "returnByValue": True, "awaitPromise": True, "timeout": 5000})
        print("WebRTC:", r["result"]["result"]["value"])

asyncio.run(main())
PYEOF
```

## Full Leak Report

```python
# Запустить в execute_code (hermes_tools)
import json, asyncio, websockets, httpx

async def main():
    tab = httpx.put("http://localhost:9222/json/new?url=https://ipleak.net").json()
    async with websockets.connect(tab["webSocketDebuggerUrl"]) as ws:
        mid = 1
        async def s(m, p=None):
            global mid; i = mid; mid += 1
            await ws.send(json.dumps({"id": i, "method": m, "params": p or {}}))
            return json.loads(await ws.recv())
        await s("Page.enable")
        
        # wait for load
        for _ in range(30):
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), 1.0))
                if m.get("method") == "Page.frameStoppedLoading": break
            except: pass
        await asyncio.sleep(3)
        
        text = (await s("Runtime.evaluate", {"expression": "document.body.innerText", "returnByValue": True})
                )["result"]["result"]["value"]
        
        sections = {"IP": "Your IP addresses", "WebRTC": "WebRTC detection", 
                     "DNS": "DNS Addresses", "Geo": "IP Address details"}
        for name, query in sections.items():
            idx = text.find(query)
            if idx >= 0: print(f"\n=== {name} ===\n{text[idx:idx+400]}")

asyncio.run(main())
```

## CDP Reconnection (when tools fail)

Если `browser_navigate` не работает (404 WebSocket):

```bash
# 1. Проверить, жив ли CDP
curl -s http://localhost:9222/json/version

# 2. Узнать новый WebSocket URL
curl -s http://localhost:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['webSocketDebuggerUrl'])"

# 3. Обновить конфиг Hermes (но TUI не перечитает на ходу)
hermes config set browser.cdp_url "ws://127.0.0.1:9222/devtools/browser/<NEW_UUID>"

# 4. Использовать page-level WebSocket напрямую (см. выше)
```

## Cookie Clearing

После смены прокси/региона Google cookies содержат старую сессию:

```python
import json, asyncio, websockets, httpx
async def main():
    tab = httpx.get("http://localhost:9222/json").json()
    page = next(t for t in tab if t["type"] == "page")
    async with websockets.connect(page["webSocketDebuggerUrl"]) as ws:
        await ws.send(json.dumps({"id":1,"method":"Network.enable","params":{}})); await ws.recv()
        await ws.send(json.dumps({"id":2,"method":"Network.clearBrowserCookies","params":{}}))
        r = json.loads(await ws.recv())
        print(f"Cleared: {r}")
asyncio.run(main())
```
