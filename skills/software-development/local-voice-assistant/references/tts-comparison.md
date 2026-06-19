# TTS Comparison for local-siri (M1 Air 8GB)

Tested May 2026 on M1 MacBook Air 8GB, macOS 15.7.5.
User: Jenya (Евгений), Chongqing, HK eSIM + Shadowrocket.

## 1. macOS say (Milena)

**Type:** Built-in NSSpeechSynthesizer
**Disk:** 0 MB
**RAM:** 0 MB
**Speed:** Instant
**Setup:** None — preinstalled
**Voice quality:** Robot-like, synthetic
**User verdict:** "роботик" (robotic) — basic but functional
**Status:** ✅ Default fallback

```python
import subprocess
subprocess.run(["say", "-v", "Milena", "текст"])
```

## 2. Piper TTS (ru_RU-irina-medium)

**Type:** ONNX CPU inference
**Disk:** 60 MB (model) + 5 KB (config JSON)
**RAM:** ~20 MB during inference
**Speed:** Fast (~real-time on CPU)
**Setup:**
```bash
pip3 install piper-tts
```

**Download URL (correct):**
```
https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx
```
Note: `ru/ru_RU/irina/medium/` — double `ru/` prefix is required.

**Parameters tested:**
- Default: length-scale=1.2, noise-scale=0.667 → slow, sad
- Brisk: length-scale=0.9, noise-scale=0.8 → faster, more expressive
- User still rejected: "голос грустный" (voice sounds sad)

**Other voices downloaded (not tested):**
- ru_RU-denis-medium.onnx (male, 60 MB)

**Pitfalls:**
- Wrong URL returns HTML page, not ONNX file — verify with `file model.onnx`
- HuggingFace from HK eSIM: 1-200 KB/s, use `curl -C - -L` resume
- Text-to-WAV + afplay adds 2 subprocesses per utterance (latency)

## 3. Silero TTS v4 (v4_ru)

**Type:** PyTorch CPU inference
**Disk:** 38 MB (model cached in ~/.cache/torch/hub/)
**RAM:** ~150 MB during inference
**Speed:** ~0.9s for 5s utterance (CPU)
**Setup:**
```bash
pip3 install omegaconf soundfile
```

**Model load (Python):**
```python
import torch
# Bypass trust check for torch.hub in non-interactive mode
torch.hub._validate_not_a_forked_repo = lambda a,b,c: True
torch.hub._check_repo_is_trusted = lambda *args, **kwargs: True
model, _ = torch.hub.load(
    'snakers4/silero-models', 'silero_tts',
    language='ru', speaker='v4_ru', trust_repo=True)
```

**Available Russian speakers:** `aidar` (male), `baya` (female), `kseniya` (female), `xenia` (female), `eugene` (male), `random`

**Tested (all rejected as natural voices):**
- xenia: feminine, clear diction, slightly robotic
- baya: deeper female voice
- kseniya: similar to xenia

**But: Accepted as base voice for ffmpeg post-processing** — two distinct modes used:

**Mode 1 — Low Female Voice (active setup, user's choice):**
Clean pitch down, no robot effects.
```bash
ffmpeg -i input.wav -af "asetrate=48000*0.85,aresample=48000,atempo=1.176" output_low_female.wav
```
Integration: `TextToSpeech(speaker="xenia", pitch=0.85)` in assistant.py.

**Mode 2 — Robot/Monster variants (available but not active):**
- Light robot: `vibrato=f=8:d=0.2,asetrate=44100*1.2,aresample=44100,volume=1.5`
- Chill robot: `vibrato=f=5:d=0.3,volume=1.3`
- Deep robot: `asetrate=44100*0.85,aresample=44100,vibrato=f=7:d=0.15,volume=1.5`
- Deepest robot: `asetrate=44100*0.6,aresample=44100,vibrato=f=4:d=0.3,volume=2.0`
- Classic robot: `vibrato=f=10:d=0.1,aphaser=in_gain=0.7:out_gain=0.8:delay=5:decay=0.7:speed=0.5`

**Synthesis speed:** ~0.9s for 3s audio, ~1.5s for 5s audio (CPU). +0.1s for ffmpeg effect.
**Status:** ✅ Active base TTS (with robot post-processing)

## 4. Fish Speech (attempted)

**Type:** Transformer-based TTS, PyTorch
**Disk:** Unknown (model not downloaded)
**Dependencies:** Massive (lightning, wandb, tensorboard, gradio, modelscope, etc.)
**Network:** HF download would take 30+ min at 150 KB/s
**Status:** ❌ Not installed — too heavy for 8GB + slow network

## 5. Qwen3-TTS (in progress)

**Type:** Discrete codec LM (token-based TTS)
**Package:** `pip3 install qwen-tts` (pulled in: transformers, accelerate, gradio, librosa)
**Model:** Qwen3-TTS-12Hz-0.6B-Base
**Disk:** ~2.4 GB (1.7 GB model + 651 MB speech_tokenizer)
**RAM:** ~1.5-2 GB estimate (bf16 via MPS on M1)
**Languages:** zh, en, ja, ko, de, fr, ru, pt, es, it
**Russian support:** Confirmed in model card (`language: [zh, en, ..., ru, ...]`)
**Download source:** ModelScope (China-friendly), ~500 KB/s
```python
from modelscope import snapshot_download
model_dir = snapshot_download('Qwen/Qwen3-TTS-12Hz-0.6B-Base')
```
**Features:** Voice cloning (3s reference), 97ms streaming, instruction-based voice control
**Status:** ⏳ Package installed, model downloading in progress. Not yet tested.

## Summary

| # | Engine | Voice quality | RAM | Disk | Setup effort | User says |
|---|--------|--------------|-----|------|-------------|-----------|
| 1 | macOS say Milena | Robotic | 0 MB | 0 MB | None | "роботик" |
| 2 | Piper irina-medium | Sad/synthetic | ~20 MB | 60 MB | Medium | "грустный" |
| 3 | Silero v4 xenia + ffmpeg **pitch 0.85** | Low female, clean | ~150 MB | 38 MB | Easy | ✅ Active |
| 4 | Silero v4 + ffmpeg robot fx | Robot/monster | ~150 MB | 38 MB | Easy | ⏸ Available |
| 5 | Fish Speech | Unknown | Heavy | Heavy | Hard | N/A |
| 6 | Qwen3-TTS 0.6B | Unknown (ru supported) | ~1.5-2 GB | ~2.4 GB | Medium | ⏳ Incomplete |

**Current active config:** Silero v4 (xenia, female) → ffmpeg pitch down 0.85 (low female voice) → afplay.
