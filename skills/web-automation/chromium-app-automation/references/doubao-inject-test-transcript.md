# Doubao Voice Chat — Audio Injection Test Transcript

Session: 2026-06-14. Verifies that BlackHole audio injection produces real ASR and correct AI responses.

## Setup
- Doubao launched with `--remote-debugging-port=9223`
- BlackHole 2ch as default input (`SwitchAudioSource -s "BlackHole 2ch" -t input`)
- Audio played via `ffmpeg -i <file> -f audiotoolbox -audio_device_index 0 ""`
- Voice transcript read via CDP: `document.body.innerText`

## Step 1: Confirm translator capability

**Injected TTS (English):**
> "Hello. I need a translator. Can you translate between English and Chinese?"

**AI response (English):**
> "Yes, I can translate between English and Chinese. Please tell me the content you need to translate."

## Step 2: English → Chinese translation

**Injected TTS (English):**
> "Please translate this sentence to Chinese. The weather is beautiful today and I would like to go for a walk in the park."

**AI response (Chinese ✅):**
> "今天天气很好，我想去公园散步。"

Translation is correct and natural.

## Step 3: Chinese → English translation

**Injected TTS (Chinese, macOS `say -v Tingting`):**
> "请把这句话翻译成英文：我昨天看了一部非常有趣的电影，推荐你也去看看。"

**AI response (English ✅):**
> "I watched a very interesting movie yesterday and recommend you to..."

Translation is correct (response truncated at ~50 chars in transcript view).

## Key Findings
1. ASR accurately transcribes both English and Chinese injected audio
2. AI correctly translates between EN↔ZH based on the spoken instruction
3. Language of response matches language of request
4. Full pipeline: TTS → AIFF → ffmpeg audiotoolbox → BlackHole → voice chat → ASR → AI response runs at real-time speed (1x)
5. Doubao does NOT respond in Russian — it follows the input language
