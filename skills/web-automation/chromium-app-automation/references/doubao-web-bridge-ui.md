# Web UI Bridge for CDP-Controlled Apps

**Pattern:** Build a local web server with WebSocket + HTML frontend to wrap a CDP-controlled Chromium app into a user-friendly web interface.

When you need a GUI to interact with a CDP-automated app (Doubao, etc.), don't build a native app — use a local web server. It's faster to build, requires no compilation, and works in any browser.

## Architecture

```
[Browser] ←WS→ [Python aiohttp backend] ─CDP→ [Doubao/Chromium app]
                         │
                         ├─ TTS (say) → ffmpeg → BlackHole (voice mode)
                         └─ Translation API (DeepSeek etc.)
```

## Skeleton structure

```
project/
├── server.py    — Aiohttp backend (HTTP + WebSocket + CDP + pipeline)
└── index.html   — Single-page HTML frontend (WS client)
```

## Backend (server.py)

### Key components

1. **Aiohttp server** on localhost (e.g. 8765)
2. **WebSocket endpoint** (`/ws`) for real-time bidirectional communication
3. **CDP helpers**: `cdp_send()`, `cdp_read_body()`, `cdp_eval()` — generic async wrappers
4. **Pipeline functions**: pass user input through the full chain

### WebSocket message protocol

**Client → Server:**
```json
{"type": "chat", "text": "Russian message"}
{"type": "voice_start"}
{"type": "voice_stop"}
```

**Server → Client (async, real-time):**
```json
{"type": "status", "text": "Перевожу на английский..."}
{"type": "message", "role": "user", "text": "Привет"}
{"type": "message", "role": "bot", "text": "Здравствуйте"}
{"type": "voice_status", "active": true}
{"type": "error", "text": "Описание ошибки"}
```

### CDP wrapper pattern

```python
import asyncio, json, websockets, urllib.request

async def cdp_list_pages():
    req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

async def cdp_send(target_id, method, params=None):
    import websockets
    pages = await cdp_list_pages()
    ws_url = next(p["webSocketDebuggerUrl"] for p in pages if p["id"] == target_id)
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        msg_id = 1
        await ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        return json.loads(await asyncio.wait_for(ws.recv(), 30))

async def cdp_read_body(target_id):
    r = await cdp_send(target_id, "Runtime.evaluate", {
        "expression": "document.body.innerText", "returnByValue": True
    })
    return r.get("result", {}).get("result", {}).get("value", "")
```

### Translation via API

```python
async def translate_to_russian(text):
    prompt = f"Translate to Russian. Detect language automatically.\\n\\nText: {text}"
    # POST to DeepSeek/OpenAI-compatible API

async def translate_ru_to_en(text):
    prompt = f"Translate from Russian to English.\\n\\nText: {text}"
    # POST to DeepSeek/OpenAI-compatible API
```

## Frontend (index.html)

### Single-page requirements

1. **WebSocket connection** — auto-reconnect on disconnect
2. **Chat window** — message bubbles, scroll-to-bottom
3. **Input field** — submit on Enter
4. **Voice toggle button** — switch between text/voice modes
5. **Status bar** — shows current pipeline step with spinner
6. **Dark theme** — GitHub-style (`#0d1117` background)

### WS client pattern

```javascript
const ws = new WebSocket(`ws://${location.host}/ws`);
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    switch(data.type) {
        case 'status': updateStatus(data.text); break;
        case 'message': addMessage(data.role, data.text); break;
        case 'voice_status': toggleVoiceBtn(data.active); break;
        case 'error': addSystemMsg('⚠ ' + data.text); break;
    }
};
```

### Template: status update pattern (auto-detect language)

```python
async def send_status(ws, text):
    await ws.send_json({"type": "status", "text": text})

async def chat_pipeline(ws, ru_text):
    await send_message(ws, "user", ru_text)

    await send_status(ws, "Перевожу на английский...")
    en_text = await translate_ru_to_en(ru_text)

    if voice_active:
        await send_status(ws, "Генерирую голос...")
        response = await voice_chat_send(en_text)
    else:
        await send_status(ws, "Отправляю в текстовый чат...")
        response = await text_chat_send(en_text)

    await send_status(ws, "Перевожу ответ на русский...")
    ru_response = await translate_to_russian(response)

    await send_message(ws, "bot", ru_response)
    await send_status(ws, "Готов.")
```

## When to use this pattern

- Any CDP-controlled app needs a human-friendly interface
- You need real-time status feedback during multi-step pipelines
- You want to offer both fast (text) and rich (voice) interaction modes
- Translation or TTS steps need to be orchestrated between the user and the app

## When NOT to use (use direct CDP instead)

- One-shot automation (no need for a persistent UI)
- The user is already comfortable with terminal output
- The pipeline has only 2-3 steps with no user interaction needed

## Pitfalls

### Dictation tool compatibility (Handy, macOS built-in dictation)

Inline `onkeydown` handlers on `<input>` elements **block macOS dictation tools**. When Handy (Option+Space dictation) finishes and tries to insert text, the browser's key event interception may consume or break the insertion.

**Fix:** Use a native `<form>` with a `submit` event listener instead of inline `onkeydown`:

```html
<!-- ❌ Breaks dictation tools -->
<input onkeydown="if(event.key==='Enter'){sendMessage();event.preventDefault()}">

<!-- ✅ Works with dictation tools -->
<form id="msgForm" style="display:contents">
  <input type="text" id="input" autofocus>
  <button type="submit">→</button>
</form>
<script>
document.getElementById('msgForm').addEventListener('submit', (e) => {
  e.preventDefault();
  sendMessage();
});
</script>
```

The form's native submit event is triggered by Enter keypress and is compatible with system-level text insertion from dictation tools. The inline `onkeydown` approach intercepts key events before the browser can process them properly for accessibility/dictation.

**Verify:** After the fix, the input field should accept text from Handy (Option+Space → speak → release → text appears), and Enter should send it.

## Reference project

Full working skeleton at: `~/projects/active/doubao-chat-bridge/`
- `server.py` — complete backend
- `index.html` — complete frontend
- `run.sh` — launcher with correct Python path

Or use templates from this skill:
- `templates/doubao-web-bridge-server.py` — complete backend
- `templates/doubao-web-bridge-ui.html` — matching frontend (dark theme, WS client, form-submit input for dictation compatibility)
- `templates/doubao-web-bridge-ui.html`

### Dependency installation

The user may have multiple Python installs. Test before running:

```bash
python3 -c "import aiohttp, websockets"   # check from user's shell
pip3 install aiohttp websockets --break-system-packages   # if missing
```

Use explicit Python path if needed: `/opt/homebrew/bin/python3 server.py`

Start it with: `python3 ~/projects/active/doubao-chat-bridge/server.py`
Open: `http://127.0.0.1:8765`
