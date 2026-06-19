#!/usr/bin/env python3
"""
Doubao Chat Bridge — Web UI backend.
Aiohttp server: HTTP + WebSocket + CDP + TTS/BlackHole + Translation.

Key patterns captured here:
- Voice chat: dialog ("结束并开始新通话") may appear BEFORE or AFTER clicking the phone button.
  Check both times.
- Transcript parsing: voice chat adds ASR text first, then AI response.
  Wait for 2+ new lines before extracting the response (double-message bug).
- Never navigate voice pages to about:blank — that kills the floating window.
  Use UI button clicks instead.
- Translation: auto-detect ZH/EN when translating to Russian. AI responds in
  either language depending on context.
"""

import asyncio, json, os, urllib.request, subprocess, time
from pathlib import Path
import aiohttp
from aiohttp import web

HOST = "127.0.0.1"
PORT = 8765
CDP_PORT = 9223
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
TTS_DIR = Path("/tmp/doubao_chat")
TTS_DIR.mkdir(exist_ok=True)

voice_active = False
voice_page_id = None

NOISE_LINES = {"正在听...", "打断豆包", "复制", "请开始说话", "回答字幕将显示在这里", "挂断通话"}
LOG = True

def log(*args, **kwargs):
    if LOG:
        print(f"[{time.strftime('%H:%M:%S')}]", *args, **kwargs, flush=True)


# ── CDP ──────────────────────────────────────────────────────────────────

async def cdp_list_pages():
    req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

async def cdp_send(target_id, method, params=None):
    import websockets
    pages = await cdp_list_pages()
    ws_url = next(p["webSocketDebuggerUrl"] for p in pages if p["id"] == target_id)
    async with websockets.connect(ws_url, max_size=10_000_000) as ws:
        await ws.send(json.dumps({"id": 1, "method": method, "params": params or {}}))
        return json.loads(await asyncio.wait_for(ws.recv(), 30))

async def cdp_read_body(target_id):
    r = await cdp_send(target_id, "Runtime.evaluate", {
        "expression": "document.body.innerText", "returnByValue": True
    })
    return r.get("result", {}).get("result", {}).get("value", "")

async def cdp_eval(target_id, js):
    r = await cdp_send(target_id, "Runtime.evaluate", {
        "expression": js, "returnByValue": True
    })
    return r.get("result", {}).get("result", {}).get("value", "")

async def find_page(substr):
    for p in await cdp_list_pages():
        if substr in p.get("url", ""):
            return p["id"]
    return None

def get_new_lines(body, prev):
    lines = [l.strip() for l in body.split("\n")
             if l.strip() and l.strip() not in NOISE_LINES]
    old = set(l.strip() for l in prev.split("\n")
              if l.strip() and l.strip() not in NOISE_LINES)
    return [l for l in lines if l not in old]

async def click_button_text(target_id, text_fragment):
    """Click a button by its text content using JS .click()."""
    await cdp_eval(target_id, f"""
        (() => {{
            let els = document.querySelectorAll('div, button, span');
            for (let e of els) {{
                if (e.textContent.includes('{text_fragment}')) {{ e.click(); return; }}
            }}
        }})()
    """)

async def click_phone_launcher():
    """Click the phone/hang-up button on the launcher page via CDP mouse event."""
    lid = await find_page("launcher")
    if not lid:
        return False
    for ev in ["mousePressed", "mouseReleased"]:
        await cdp_send(lid, "Input.dispatchMouseEvent", {
            "type": ev, "x": 328, "y": 25, "button": "left", "clickCount": 1
        })
        await asyncio.sleep(0.1)
    return True

async def handle_end_call_dialog(vid):
    """Check if the '结束并开始新通话' dialog is showing on a page and click it.
    Returns True if dialog was found and clicked (new call started)."""
    body = await cdp_read_body(vid)
    if "结束并开始新通话" in body:
        log("END_CALL: dialog found, clicking")
        await click_button_text(vid, "结束并开始新通话")
        await asyncio.sleep(3)
        return True
    return False


# ── Translation ──────────────────────────────────────────────────────────

async def translate_to_russian(text):
    """Detect source language (ZH/EN) and translate to Russian."""
    prompt = f"""Translate the following text to Russian.
The text may be in Chinese, English, or another language.
Detect the language automatically and translate to Russian.
Return ONLY the translation, no explanations, no quotes, no notes.

Text: {text}"""
    return await _call_api(prompt)

async def translate_ru_to_en(text):
    """Translate Russian to English."""
    prompt = f"""Translate the following text from Russian to English.
Return ONLY the translation, no explanations, no quotes, no notes.

Text: {text}"""
    return await _call_api(prompt)

async def _call_api(prompt):
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.1, "max_tokens": 500}
    async with aiohttp.ClientSession() as s:
        async with s.post(DEEPSEEK_URL, json=payload, headers=headers) as r:
            data = await r.json()
            return data["choices"][0]["message"]["content"].strip()


# ── Audio / Voice ────────────────────────────────────────────────────────

def switch_audio(dev):
    subprocess.run(["SwitchAudioSource", "-s", dev, "-t", "input"],
                   capture_output=True, timeout=10)

def tts_gen(text):
    f = TTS_DIR / f"tts_{int(time.time())}.aiff"
    subprocess.run(["say", "-v", "Samantha", "-o", str(f), text],
                   capture_output=True, timeout=30)
    return f

def inject_audio(path):
    subprocess.run(["ffmpeg", "-i", str(path), "-f", "audiotoolbox",
                    "-audio_device_index", "0", ""], capture_output=True, timeout=60)

async def voice_open():
    """Open voice chat: BlackHole → handle any active call → click phone → verify."""
    global voice_active, voice_page_id
    log("VOICE: opening...")
    switch_audio("BlackHole 2ch")

    # Phase 1: check existing voice page for dialog BEFORE clicking phone
    already_started = False
    vid = await find_page("voice")
    if vid:
        if await handle_end_call_dialog(vid):
            already_started = True

    # Phase 2: click phone button (may show the dialog on voice page)
    if not already_started:
        await click_phone_launcher()
        await asyncio.sleep(2)

        # Phase 3: check again AFTER clicking — dialog may have just appeared
        vid2 = await find_page("voice")
        if vid2:
            await handle_end_call_dialog(vid2)

    voice_page_id = await find_page("voice")
    if voice_page_id:
        voice_active = True
        log("VOICE: active")
        return True
    log("VOICE: failed — no voice page")
    return False

async def voice_close():
    """Close voice chat: handle dialog → click phone → restore mic."""
    global voice_active, voice_page_id
    log("VOICE: closing...")
    vid = voice_page_id or await find_page("voice")
    if vid:
        await handle_end_call_dialog(vid)
        await click_phone_launcher()
        await asyncio.sleep(2)
    switch_audio("MacBook Air Microphone")
    voice_active = False
    voice_page_id = None
    log("VOICE: closed, mic restored")

async def voice_send(text_en):
    """Inject English TTS and wait for AI response.
    KEY: voice chat adds ASR text FIRST, then AI response.
    Poll waits for 2+ new lines to avoid double-message bug."""
    log(f"VOICE_SEND: '{text_en[:60]}...'")
    aiff = tts_gen(text_en)
    log(f"VOICE_SEND: TTS ready ({aiff.name})")
    inject_audio(aiff)
    log("VOICE_SEND: audio injected, waiting for response...")

    vid = voice_page_id or await find_page("voice")
    if not vid:
        return ""
    prev = await cdp_read_body(vid)
    stable = 0
    last = ""
    for i in range(30):
        await asyncio.sleep(1)
        body = await cdp_read_body(vid)
        if body == prev:
            stable += 1
            if stable >= 2 and last:
                log(f"VOICE_SEND: stable 2s, response: '{last[:60]}'")
                return last
            continue
        stable = 0
        new = get_new_lines(body, prev)
        if new:
            log(f"VOICE_SEND: +{len(new)} at {i+1}s: {[l[:40] for l in new]}")
            last = new[-1]
            prev = body
            continue
        prev = body
    return ""


# ── Text chat ────────────────────────────────────────────────────────────

async def text_send(text_en):
    """Send English text via CDP and wait for AI response."""
    log(f"TEXT_SEND: '{text_en[:60]}...'")
    cid = await find_page("doubao-chat/chat")
    if not cid:
        log("TEXT_SEND: no chat page found")
        return ""
    await cdp_eval(cid, "document.querySelector('textarea')?.focus()")
    await asyncio.sleep(0.2)
    await cdp_send(cid, "Input.insertText", {"text": text_en})
    await asyncio.sleep(0.2)
    for ev_type in ["rawKeyDown", "keyUp"]:
        await cdp_send(cid, "Input.dispatchKeyEvent", {
            "type": ev_type, "windowsVirtualKeyCode": 13, "key": "Enter"
        })
        await asyncio.sleep(0.1)
    prev = await cdp_read_body(cid)
    stable = 0
    last = ""
    for i in range(20):
        await asyncio.sleep(1)
        body = await cdp_read_body(cid)
        if body == prev:
            stable += 1
            if stable >= 2 and last:
                log(f"TEXT_SEND: stable 2s, response: '{last[:60]}'")
                return last
            continue
        stable = 0
        new = [l.strip() for l in body.split("\n") if l.strip()
               and l.strip() not in ("复制", "发消息...")]
        old = set(l.strip() for l in prev.split("\n") if l.strip()
                  and l.strip() not in ("复制", "发消息..."))
        new_lines = [l for l in new if l not in old]
        if new_lines:
            log(f"TEXT_SEND: +{len(new_lines)} at {i+1}s")
            last = new_lines[-1]
            prev = body
            continue
        prev = body
    return ""


# ── WebSocket handler ────────────────────────────────────────────────────

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    log(f"WS: connected from {request.remote}")

    async def send(t, **kw):
        await ws.send_json({"type": t, **kw})

    await send("status", text="Готов.")

    async def pipeline(ru_text):
        log(f"PIPELINE: start '{ru_text[:60]}...'")
        await send("message", role="user", text=ru_text)

        await send("status", text="Перевожу на английский...")
        try:
            en = await translate_ru_to_en(ru_text)
            log(f"PIPELINE: RU→EN: '{en[:80]}'")
        except Exception as e:
            log(f"PIPELINE: RU→EN error: {e}")
            return await send("error", text=f"Ошибка перевода: {str(e)[:100]}")

        if voice_active:
            await send("status", text="Голосовой канал...")
            zh = await voice_send(en)
        else:
            await send("status", text="Текстовый канал...")
            zh = await text_send(en)

        if not zh:
            log("PIPELINE: empty response from Doubao")
            return await send("error", text="Нет ответа от Doubao.")

        await send("status", text="Перевожу на русский...")
        try:
            ru = await translate_to_russian(zh)
            log(f"PIPELINE: ZH→RU: '{ru[:80]}'")
        except Exception as e:
            log(f"PIPELINE: ZH→RU error: {e}")
            ru = f"[{zh[:80]}...]"

        await send("message", role="bot", text=ru)
        await send("status", text="Готов.")
        log("PIPELINE: done")

    async for msg in ws:
        if msg.type != aiohttp.WSMsgType.TEXT:
            continue
        d = json.loads(msg.data)
        t = d.get("type")
        if t == "chat":
            await pipeline(d.get("text", "").strip())
        elif t == "voice_start":
            log("WS: VOICE_START")
            ok = await voice_open()
            await send("voice_status", active=ok)
            await send("status", text="Голос: " + ("вкл" if ok else "ошибка"))
        elif t == "voice_stop":
            log("WS: VOICE_STOP")
            await voice_close()
            await send("voice_status", active=False)
            await send("status", text="Голос: выкл")

    log("WS: disconnected")
    return ws


# ── Main ─────────────────────────────────────────────────────────────────

async def main():
    app = web.Application()
    app.router.add_get("/", lambda r: web.FileResponse(Path(__file__).parent / "index.html"))
    app.router.add_get("/ws", ws_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    print(f"Bridge ready: http://{HOST}:{PORT}", flush=True)
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        if voice_active:
            await voice_close()
    await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
