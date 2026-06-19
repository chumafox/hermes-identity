# Doubao Voice Chat — Russian Bridge Translation Pipeline

**Date:** 2026-06-14
**Pattern:** Russian text → English TTS → Doubao Voice Chat → Chinese response → Russian text

A 3-language orchestration pattern that lets a Russian-speaking user converse with Doubao (a Chinese AI assistant) through Doubao's EN+ZH voice chat, with the agent acting as the Russian↔EN↔ZH bridge.

## Why this exists

Doubao Voice Chat ASR supports **only English and Chinese** (verified across 19 languages). Russian speech is not recognized. But the agent can:
1. Accept Russian text from the user
2. Translate Russian → English (inline)
3. Speak English into Doubao via TTS + BlackHole injection
4. Read the Chinese AI response from the CDP transcript
5. Translate Chinese → Russian (inline)

This makes Doubao usable as a voice assistant for a Russian speaker despite the ASR limitation.

## Workflow

```
User (Russian text)
  ↓
Agent: translate RU → EN
  ↓
macOS `say` TTS (English voice)
  ↓
ffmpeg -f audiotoolbox → BlackHole 2ch
  ↓
Doubao Voice Chat ASR (recognizes English)
  ↓
AI responds in Chinese (via text + audio)
  ↓
Agent: read transcript via CDP (document.body.innerText)
  ↓
Agent: extract AI response (Chinese or English text)
  ↓
Agent: translate ZH/EN → RU (auto-detect language)
  ↓
User sees Russian text
```

## Prerequisites

Same as for standard audio injection:
- Doubao launched with `--remote-debugging-port=9223`
- BlackHole 2ch installed (`brew install blackhole-2ch`)
- SwitchAudioSource installed (`brew install switchaudio-osx`)
- ffmpeg installed (`brew install ffmpeg`)

## Step-by-step

### 0. Reset voice chat state
```python
# Fresh state — kills stale WebRTC call
await cdp('Page.navigate', {'url': 'about:blank'})
await asyncio.sleep(1)
await cdp('Page.navigate', {'url': 'doubao://doubao-voice-chat/?enter_from=global&viewId=NEWID'})
```

### 1. Set up translator role (first time only)
```bash
say -o /tmp/setup.aiff \
  "Hello. I need you to be a translator between English and Chinese. Can you help me with that?"
ffmpeg -i /tmp/setup.aiff -f audiotoolbox -audio_device_index 0 ""
sleep 4
```
Expected: AI confirms in English it can translate.

### 2. Translate user's Russian text to English
Inline — no external API needed. The agent translates directly.

### 3. Generate TTS on English text
```bash
say -o /tmp/msg_en.aiff "What is your name?"
```

### 4. Inject into Doubao voice chat
```bash
# Switch to BlackHole first (if not already)
SwitchAudioSource -s "BlackHole 2ch" -t input

# Play audio — it enters BlackHole → Doubao hears it
ffmpeg -i /tmp/msg_en.aiff -f audiotoolbox -audio_device_index 0 ""
```

### 5. Wait and read response
```python
import asyncio, json, websockets, urllib.request

async def read_transcript():
    pages = json.loads(urllib.request.urlopen('http://127.0.0.1:9223/json').read())
    voice_ws = next(p['webSocketDebuggerUrl'] for p in pages if 'voice' in p.get('url',''))
    async with websockets.connect(voice_ws, max_size=10_000_000) as ws:
        mid = [0]
        async def cdp(method, params=None):
            mid[0] += 1
            await ws.send(json.dumps({'id':mid[0],'method':method,'params':params or {}}))
            return json.loads(await asyncio.wait_for(ws.recv(),15))
        r = await cdp('Runtime.evaluate', {
            'expression': 'document.body.innerText',
            'returnByValue': True
        })
        return r['result']['result']['value']

# Wait ~5s for AI to respond
await asyncio.sleep(5)
transcript = await read_transcript()
```

### 6. Parse transcript for AI response

The transcript has this structure:
```
请开始说话
[user's recognized ASR text]
[AI response text]
复制
```

Extract the last non-empty, non-constant line that isn't:
- "请开始说话" / "正在听..." / "打断豆包" / "复制"
- The user's ASR-recognized text (English)
- Status indicators

The AI's response is typically in Chinese.

### 7. Translate Chinese → Russian
Inline translation by the agent.

## Example transcript (verified)

```
Step 0: User asks "Как тебя зовут?" (What's your name?)
Step 1: Agent translates → "What is your name?"
Step 2: TTS + inject
Step 3: Transcript shows:
  - "What is your name?" (ASR recognized)
  - "我的名字是豆包。" (AI response in Chinese)
Step 4: Agent translates → "Меня зовут Доубао (豆包)."
```

## Translation note

The AI may respond in **Chinese or English**, depending on the context:
- Questions about the AI itself (name, capabilities): often English
- Translation requests: Chinese
Always auto-detect the language before translating to Russian. Use `translate_to_russian()` (auto-detect) rather than hardcoding `zh → ru`.

## Web UI deployment

For repeated use, deploy the full Web UI bridge instead of typing CDP commands each time:

```bash
cd ~/projects/active/doubao-chat-bridge/
~/projects/active/doubao-chat-bridge/run.sh
# Open http://127.0.0.1:8765
```

The bridge auto-orchestrates translation → TTS → injection → reading → translation. It has two modes:
- **Text mode** (default): uses CDP on the text chat page (fast, ~5-8s per cycle)
- **Voice mode** (toggle 🎤): uses BlackHole + TTS (slow, ~10-15s, but sounds like real speech)

See `templates/doubao-web-bridge-server.py` and `references/doubao-web-bridge-ui.md` for implementation details.

## Pitfalls

- **App mute overrides injection:** If Doubao's mic is muted (e.g. user's Option+T shortcut), audio goes through BlackHole but Doubao ignores it. Verify microphone unmuted before injecting.
- **Old call state:** If a previous voice call wasn't properly ended, the AI might still be in "listening" mode from the old conversation. Always navigate to `about:blank` first, then to a fresh voice chat URL with a new viewId.
- **Timing:** Wait 4-6 seconds after injection for AI to respond. Short audio files (<2s) may not trigger ASR reliably.
- **Proxy:** All CDP WebSocket connections need `NO_PROXY="*"` to avoid routing through internet_pro.
- **ASR drift:** Doubao's ASR may occasionally mis-recognize English audio (especially with strong accents or background noise). Retry with clearer TTS or rephrase.
