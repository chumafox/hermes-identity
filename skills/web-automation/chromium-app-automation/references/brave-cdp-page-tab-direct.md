# CDP Direct Connection & Browser Workarounds

When Hermes' built-in `browser_navigate` / `browser_cdp` tools cache stale WebSocket URLs, bypass with direct Python connections.

## Browser_navigate Fallback (Stale Browser ID)

`browser_navigate` fails with `CDP WebSocket connect failed: HTTP error: 404 Not Found` even when Brave has `--remote-debugging-port=9222`. Hermes caches the old `/devtools/browser/<id>` which changes on every Brave restart.

**Workaround — connect to a PAGE tab directly:**

```python
import asyncio, json, urllib.request, websockets

r = urllib.request.urlopen('http://localhost:9222/json/list')
tabs = json.loads(r.read())
ws_url = next(t['webSocketDebuggerUrl'] for t in tabs if t['type'] == 'page')

async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
    cmd = json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': url}})
    await ws.send(cmd)
    await asyncio.wait_for(ws.recv(), timeout=10)
    await asyncio.sleep(3)

    cmd = json.dumps({'id': 2, 'method': 'Runtime.evaluate',
                      'params': {'expression': 'document.body.innerText', 'returnByValue': True}})
    await ws.send(cmd)
    resp = await asyncio.wait_for(ws.recv(), timeout=10)
    result = json.loads(resp).get('result',{}).get('result',{}).get('value','')
```

Key: connect to the **page** WS URL (`/devtools/page/<id>`), not the browser-level WS. The page tab URLs are stable across browser restarts.

## Setting Cookies Before Navigation

Useful for geo cookies (SOCS region cookie), auth tokens, or bypassing region checks:

```python
async with websockets.connect(page_ws_url) as ws:
    await ws.send(json.dumps({'id': 1, 'method': 'Network.enable'}))
    await asyncio.wait_for(ws.recv(), timeout=5)

    await ws.send(json.dumps({'id': 2, 'method': 'Network.setCookie', 'params': {
        'url': 'https://target.com',
        'name': 'SOCS', 'value': 'BASE64VALUE',
        'domain': '.google.com', 'secure': True,
        'httpOnly': True, 'sameSite': 'None'
    }}))
    await asyncio.wait_for(ws.recv(), timeout=5)

    # Then navigate — cookie is already active
    await ws.send(json.dumps({'id': 3, 'method': 'Page.navigate',
                              'params': {'url': 'https://gemini.google.com/app'}}))
```

To inspect existing cookies: `method: 'Network.getAllCookies'`

## Safaridriver (W3C WebDriver HTTP)

When Brave CDP is unreliable, Safari automation uses standard HTTP protocol:

```bash
defaults write com.apple.Safari IncludeDevelopMenu -bool true
sudo safaridriver --enable
safaridriver -p 9223 &
```

**Python client:**
```python
import urllib.request, json, time

req = urllib.request.Request('http://localhost:9223/session',
    data=b'{"capabilities":{"alwaysMatch":{"browserName":"safari"}}}',
    headers={'Content-Type': 'application/json'})
session = json.loads(urllib.request.urlopen(req).read())['value']['sessionId']

req = urllib.request.Request(f'http://localhost:9223/session/{session}/url',
    data=b'{"url":"https://example.com"}',
    headers={'Content-Type': 'application/json'}, method='POST')
urllib.request.urlopen(req)

time.sleep(5)
req = urllib.request.Request(f'http://localhost:9223/session/{session}/execute/sync',
    data=b'{"script":"return document.body.innerText.substring(0,3000)","args":[]}',
    headers={'Content-Type': 'application/json'}, method='POST')
data = json.loads(urllib.request.urlopen(req).read())['value']
```

**Limitations:**
- Safari automation blocks Google OAuth login forms (can view, cannot auth)
- Uses separate profile from normal Safari — no extensions/user cookies
- `safaridriver --enable` requires sudo
- To open Safari normally: `osascript -e 'tell app "Safari" to open location "URL"'`

## Gemini Region Blocking

Gemini Web (`gemini.google.com/app`) "Gemini isn't currently supported in your country" — confirmed causes:

| Factor | Effect |
|--------|--------|
| Play Store country (US) | ❌ No effect |
| SOCS cookie | ❌ No effect |
| IP geo (US) | ❌ No effect |
| Timezone (America/Chicago) | ❌ No effect |
| Account home region (country-association-form) | ✅ Decisive |

Check: `https://policies.google.com/terms` — "Country version: United States" = proper association.
Submit change: `https://policies.google.com/country-association-form`.
API access: `aistudio.google.com` works even when web UI is blocked.
