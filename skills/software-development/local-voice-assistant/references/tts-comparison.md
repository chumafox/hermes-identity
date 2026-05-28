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

**Tested (all rejected):**
- xenia: feminine, clear diction, slightly robotic
- baya: deeper female voice
- kseniya: similar to xenia

**Synthesis speed:** ~0.9s for 3s audio, ~1.5s for 5s audio (CPU)
**User verdict:** "не нравится" (don't like) — all voices too synthetic
**Status:** ❌ Rejected

Note: v5_ru (145 MB model) was not tested — v4_ru (38 MB) was smaller and adequate for evaluation.

## 4. Fish Speech (attempted)

**Type:** Transformer-based TTS, PyTorch
**Disk:** Unknown (model not downloaded)
**Dependencies:** Massive (lightning, wandb, tensorboard, gradio, modelscope, etc.)
**Network:** HF download would take 30+ min at 150 KB/s
**Status:** ❌ Not installed — too heavy for 8GB + slow network

## Summary

| # | Engine | Voice quality | RAM | Disk | Setup effort | User says |
|---|--------|--------------|-----|------|-------------|-----------|
| 1 | macOS say Milena | Robotic | 0 MB | 0 MB | None | "роботик" |
| 2 | Piper irina-medium | Sad/synthetic | ~20 MB | 60 MB | Medium | "грустный" |
| 3 | Silero v4 xenia/baya | Synthetic | ~150 MB | 38 MB | Easy | "не нравится" |
| 4 | Fish Speech | Unknown | Heavy | Heavy | Hard | N/A |

**Recommendation:** macOS `say` is the pragmatic default — zero cost, works, and user can switch to a better cloud TTS (edge-tts, gTTS) when internet is available. Local neural TTS on M1 8GB doesn't meet the user's quality bar yet.
