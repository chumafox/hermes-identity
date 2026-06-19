# Doubao Voice Chat — Transcript Parsing Pitfalls

## Problem: Double-message bug

When polling `document.body.innerText` on a Doubao voice chat page after injecting audio, the transcript changes INCREMENTALLY:

1. **First change (1-3s after injection):** User's English text appears — ASR has transcribed it
2. **Second change (3-7s after injection):** AI's Chinese/English response appears

If your poll loop returns on the FIRST change and treats the new text as the AI response, the user's own translated text gets displayed back to them as a "bot response" — the double-message bug.

## Problem: Single-line English responses

The AI may respond in **English** (1 new line) instead of Chinese (also 1 new line). A `len(new) >= 2` check would fail for English responses. The dialog "结束并开始新通话" text, "挂断通话", "⌥+Q" hotkey hints also appear as new lines later, corrupting the result.

## Fixed polling pattern: stability-based

Do NOT rely on a fixed "wait for 2+ new lines" count. Instead, wait until the transcript stabilizes (no changes for 2 consecutive seconds), then return the last new line captured.

```python
noise = {"正在听...", "打断豆包", "复制", "请开始说话",
         "回答字幕将显示在这里", "挂断通话"}

prev = await cdp_read_body(vid)
stable_count = 0
last_new_line = ""

for i in range(30):  # max 30 seconds
    await asyncio.sleep(1)
    body = await cdp_read_body(vid)

    if body == prev:
        stable_count += 1
        if stable_count >= 2 and last_new_line:
            return last_new_line  # stable for 2s, AI done speaking
        continue

    stable_count = 0

    lines = [l.strip() for l in body.split("\n") if l.strip()
             and l.strip() not in noise]
    old_lines = set(l.strip() for l in prev.split("\n") if l.strip()
                    and l.strip() not in noise)
    new = [l for l in lines if l not in old_lines]

    if new:
        last_new_line = new[-1]
        prev = body
        continue

    prev = body

return ""  # timeout
```

Key points:
- **Stability check:** 2 consecutive seconds with no changes → AI finished speaking
- **No fixed line count:** Handles both 1-line (EN) and multi-line responses
- **Noise filter:** "挂断通话" and "⌥+Q" are common late noise — they trigger re-check but stability gate prevents them being picked up
- **Max 30s timeout:** generous ceiling for slow ASR + AI processing

## Same issue in text chat

The text chat also shows the user's message first, then the AI response. Apply the same stability-based polling approach there too.

## Background

Doubao voice chat uses WebRTC for real-time audio. The voice page transcript reflects:
- ASR results appear as they're recognized
- AI responses appear as text overlay (even though audio is also spoken)
- Status indicators like "正在听..." (listening) and "请开始说话" (please start speaking) cycle in and out
- Late noise: "挂断通话" (end call) and "⌥+Q" hotkey hint appear minutes later if the call times out

## Translation auto-detect

The AI may respond in Chinese OR English:
- Questions about itself (name, capabilities, duration): often English
- Translation commands: Chinese
- Conversational follow-ups: mixed

Always auto-detect the source language. Use separate functions:
```python
async def translate_ru_to_en(text):
    # Explicit RU → EN for TTS/CDP forward direction

async def translate_to_russian(text):
    # Auto-detect ZH/EN → RU for reverse direction
    # Prompt: "Translate the following text to Russian.
    # The text may be in Chinese, English, or another language.
    # Detect the language automatically..."
```
