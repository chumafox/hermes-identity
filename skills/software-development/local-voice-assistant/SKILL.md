---
name: local-voice-assistant
description: "Build local voice assistants (Siri-like) on macOS using MLX Whisper, Ollama/LM Studio, and TTS. Fully offline, Apple Silicon optimized."
version: 2.0.1
author: Hermes Agent
tags: [voice, assistant, siri, stt, tts, llm, mlx, ollama, local, russian]
---

# Local Voice Assistant (macOS)

Build a fully local voice assistant on macOS — like Siri, but open-source and private.
Supports Russian language as primary, multilingual as fallback.

## Before Building: Check Existing Solutions First

For common voice tasks (dictation, transcription, voice notes), **search GitHub first** before writing custom code. Multiple open-source alternatives already exist:

| App | Stars | Best for | Saves to file? |
|-----|-------|----------|----------------|
| **TypeNo** (marswaveai/TypeNo) | ★873 | Quick voice typing (Ctrl toggle) | ❌ Outputs to active window — needs fork |
| **Pindrop** (watzon/pindrop) | ★527 | Pure native, no deps, Apple Silicon | ✅ Fork exists with file-save (see `references/pindrop-fork-changes.md`) — needs Xcode to build |
| **MacParakeet** (moona3k/macparakeet) | ★299 | All-in-one: dictation + file/YouTube transcription | ⚠️ Internal history only, no auto-export to .md |

See `references/ready-made-voice-apps.md` for full comparison. If an existing app fits ≥80% of the need, use it. Build custom only when the gap is fundamental (e.g. must save to specific file format, unusual hotkey combos, need to integrate with other pipeline components).

## Russian Voice Assistant — Quick Deploy (M1 8GB)

```bash
cd ~/Documents/local-siri/
./run.sh --setup  # install deps, warm Whisper cache
./run.sh          # full mode: voice + Web UI
```

### Architecture (Russian-optimized)

```
Mic → Silero VAD (CPU, ~15MB) → mlx-whisper base (GPU) → Ollama qwen2.5:3b → Silero v4 + ffmpeg pitch → Speakers
                                         ↑
                              триггер "прием" в конце фразы
```

### LLM Backend Options

| Backend | Command | GUI? | Notes |
|---------|---------|------|-------|
| **Ollama** (recommended for terminal) | `ollama run qwen2.5:3b` | ❌ | Auto-starts on login, models persist. Already installed with qwen2.5:3b and qwen2.5-coder:3b. API: `http://localhost:11434/v1/chat/completions` |
| **LM Studio** | Open app → Developer → Start Server | ✅ | GUI, more model options. Already installed with Qwen + Vikhrmodels. API: `http://localhost:1234/v1/chat/completions` |
| **llama.cpp** | `llama-server -m <gguf_path> --port 1234` | ❌ | Via brew. Terminal-only, light. Needs GGUF path explicitly. |

**Ollama is the lightest option** — it's already running as a daemon and shares Metal GPU with mlx-whisper gracefully on 8GB. LM Studio reserves GPU until quit.

### Memory Budget (M1 8GB, confirmed by testing)

| Component | Disk | Actual RAM | Notes |
|-----------|------|-----------|-------|
| macOS 15.7.5 | — | ~2500 MB | Base system |
| Silero VAD ONNX | **~1.2 MB** | **~15 MB** | Bundled in pip package |
| mlx-whisper base | **137 MB** | **~140 MB** | GPU via MLX+Metal |
| Qwen 3B Q4_K_M (Ollama) | **2.0 GB** | ~2000 MB | Already downloaded |
| Silero v4 TTS + ffmpeg | **38 MB** | **~150 MB** | CPU, lazy-loaded |
| Python middleware | — | ~100 MB | FastAPI + audio buffers |
| **Total RAM** | | **~4.9 GB** | ~3 GB headroom |

### TTS Options Tested

| Engine | Model | Disk | RAM | Quality verdict | Status |
|--------|-------|------|-----|----------------|--------|
| **macOS say** (preinstalled) | Milena (Enhanced, ru_RU) | 0 MB | 0 MB | Натуральный, русский | ✅ Primary (финал) |
| **Piper** (pypi piper-tts) | ru_RU-irina-medium | 60 MB | ~20 MB CPU | "грустный" | ❌ Rejected |
| **Silero v4** (torch.hub) | v4_ru (xenia/baya/kseniya) | 38 MB | ~150 MB CPU | "приемлемо с pitch down" | ❌ Replaced by macOS say |
| **Fish Speech** (pip fish-speech) | N/A | — | Heavy deps | Not tested (too big) | ❌ Skipped |
| **Qwen3-TTS** (qwen-tts) | 0.6B Base / 1.7B Base | ~2.4 GB | ~1.5-2 GB GPU (0.6B) / ~2.5-3 GB (1.7B) | Russian supported. 1.7B 4-bit: WER 3.47%, RTF 0.79 (fast). 0.6B 4-bit: WER 15.58% (poor). See `references/qwen3-tts-benchmarks-apple-silicon.md` | ✅ Benchmarked |

**Current active setup:** Silero v4 TTS + ffmpeg post-processing → robot voice effects (see below). User rejected natural voices (Piper, Silero) but accepted robot/monster voice as preferred style.

See `references/tts-comparison.md` for detailed setup, parameters, and voice samples — including tested speakers, synthesis speed, and user verdict per engine.

### Piper TTS (alternative TTS)

**Install:** `pip3 install piper-tts` (provides `piper` CLI)

**Models:** Download from HuggingFace `rhasspy/piper-voices`. Russian available:
- `ru/ru_RU/irina/medium/ru_RU-irina-medium.onnx` (female) — tested, rejected
- `ru/ru_RU/denis/medium/ru_RU-denis-medium.onnx` (male) — downloaded but not tested
- `ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx` (male)
- `ru/ru_RU/ruslan/medium/ru_RU-ruslan-medium.onnx` (male)

**URL pitfall:** The path on HF is `ru/ru_RU/voice/medium/`, NOT `ru_RU-voice-medium.onnx`. Downloading the wrong path returns an HTML error page. Verify with `file model.onnx` — should say "data", not "HTML document".

**Integration (assistant.py):**
```python
import subprocess, tempfile
proc = subprocess.run(["piper", "-m", PIPER_MODEL, "-c", PIPER_CONFIG,
    "-f", tmp_path,
    "--length-scale", "0.9",    # faster = less sad
    "--noise-scale", "0.8",     # more expressive
    "--noise-w-scale", "0.6"],
    input=text.encode("utf-8"), capture_output=True, timeout=30)
subprocess.run(["afplay", tmp_path])  # playback
```

**Slow network:** HuggingFace from HK eSIM can be 1-200 KB/s. Use `curl -C - -L` (resume) for multi-segment downloads. Expect ~5 min per 60MB.

### Silero TTS v4 (alternative TTS)

**Setup:**
```bash
pip3 install omegaconf soundfile
```

**Load model (torch.hub):**
```python
import torch
torch.hub._validate_not_a_forked_repo = lambda a,b,c: True  # bypass trust check
torch.hub._check_repo_is_trusted = lambda *args, **kwargs: True
model, example_text = torch.hub.load(
    'snakers4/silero-models', 'silero_tts',
    language='ru', speaker='v4_ru', trust_repo=True)
```

**Russian speakers:** `aidar` (male), `baya` (female), `kseniya` (female), `xenia` (female), `eugene` (male), `random`

**Synthesis:**
```python
audio = model.apply_tts(text=text, speaker='xenia', sample_rate=48000)
# audio: torch.Tensor, ~0.9s for 5s utterance
import soundfile as sf
sf.write("/tmp/out.wav", audio.numpy(), 48000)
```

**Model sizes:** v4_ru = 38 MB (fast download even from China), v5_ru = 145 MB (may time out)

**Pitfall:** The `models.silero.ai` CDN has no Range/Resume support. v5_ru may fail from China. Use v4_ru (38MB) — significantly smaller, faster, same speaker set.

### Qwen3-TTS (benchmarked — recommendations available)

**Type:** Discrete codec LM (token-based TTS)
**Installed via:** `pip3 install qwen-tts` (requires `transformers`, `accelerate`, `gradio`, `librosa`)
**Model sizes:** 0.6B Base (~2.4 GB) or 1.7B Base (~3+ GB)
**RAM estimate:** ~1.5-2 GB (0.6B), ~2.5-3 GB (1.7B) via MLX on Apple Silicon
**Languages:** zh, en, ja, ko, de, fr, **ru**, pt, es, it — 10 languages including Russian
**Features:** Voice cloning (3s reference), streaming (~97ms latency), instruction-based voice control

**Benchmark summary (via mlx-audio on Apple Silicon):**
- 1.7B 4-bit MLX: RTF ~0.79, WER 3.47% — **recommended for M1 Pro 32GB+**
- 0.6B 4-bit MLX: RTF ~0.4-0.6, WER 15.58% — poor quality, use 8-bit (9.74%) if needed on 8GB
- CPU GGUF: RTF 1.6+ — avoid (slower than real-time)

See `references/qwen3-tts-benchmarks-apple-silicon.md` for full RTF/latency/WER breakdown.

**Download from ModelScope (China-friendly):**
```python
from modelscope import snapshot_download
model_dir = snapshot_download('Qwen/Qwen3-TTS-12Hz-0.6B-Base')
# Saves to ~/.cache/modelscope/hub/models/Qwen/Qwen3-TTS-12Hz-0.6B-Base/
# Download speed from ModelScope: ~500 KB/s (vs ~1.2 KB/s from HuggingFace)
```

**Usage:**
```python
from qwen_tts import Qwen3TTSModel
import torch

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    device_map="mps",
    dtype=torch.float16,
    attn_implementation="eager",
)
```

**Status:** Package installed, model downloading. Not yet tested for Russian voice quality.
**Pitfall:** Original HF download from China is extremely slow. Always use ModelScope mirror.

### Robot/Monster Voice via ffmpeg Post-processing

The user rejected all natural TTS voices. Active setup: **Silero v4 + ffmpeg pitch down = low female voice** (natural but lower timbre). Robot/monster effects are also available.

**Base voice:** Silero v4_ru, any speaker (xenia/baya/kseniya). Generate WAV first, then post-process via ffmpeg.

**Active setup — Low Female Voice (user's choice):**
```bash
# Pitch down 15% (0.85), normal speed (atempo compensation)
ffmpeg -i input.wav -af "asetrate=48000*0.85,aresample=48000,atempo=1.176" output.wav
```
Integration: `TextToSpeech(speaker="xenia", pitch=0.85)` — clean female voice, slightly lower timbre.

**Robot variants tested:**

**Robot variants tested:**

```bash
# Light robot — vibrato + pitch up
ffmpeg -i input.wav -af "vibrato=f=8:d=0.2,asetrate=44100*1.2,aresample=44100,volume=1.5" robot.wav

# Chill robot — light modulation only
ffmpeg -i input.wav -af "vibrato=f=5:d=0.3,volume=1.3" robot_chill.wav

# Deep robot — low pitch + vibrato
ffmpeg -i input.wav -af "asetrate=44100*0.85,aresample=44100,vibrato=f=7:d=0.15,volume=1.5" robot_deep.wav

# Deepest robot — extreme low pitch
ffmpeg -i input.wav -af "asetrate=44100*0.6,aresample=44100,vibrato=f=4:d=0.3,volume=2.0" robot_deepest.wav

# Classic robot — phaser + vibrato
ffmpeg -i input.wav -af "vibrato=f=10:d=0.1,aphaser=in_gain=0.7:out_gain=0.8:delay=5:decay=0.7:speed=0.5" robot_classic.wav
```

**Integration pattern (assistant.py):**
```python
import subprocess, tempfile, os, soundfile as sf

# 1. Generate base audio with Silero
audio = model.apply_tts(text=text, speaker='xenia', sample_rate=48000)

# 2. Save to temp WAV
tmp_in = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
sf.write(tmp_in, audio.numpy(), 48000)

# 3. Apply robot effect
tmp_out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
subprocess.run([
    "ffmpeg", "-y", "-i", tmp_in,
    "-af", "asetrate=44100*0.85,aresample=44100,vibrato=f=7:d=0.15,volume=1.5",
    tmp_out
], capture_output=True, timeout=10)

# 4. Play
subprocess.run(["afplay", tmp_out])

# 5. Cleanup
os.unlink(tmp_in); os.unlink(tmp_out)
```

**Performance:** Synthesis (~0.9s) + ffmpeg (~0.1s) + afplay (~time of utterance). Total ~1s overhead per sentence.

### End-of-Speech Trigger Word

Instead of relying solely on VAD silence detection, the user can say a trigger word at the end of their phrase to signal they're done speaking. Like a radio: say phrase + "прием" (over).

**Concept:** The trigger word is NOT a wake word (it doesn't start the assistant). It marks the END of the user's speech, so the assistant doesn't have to guess when silence means "done" vs "thinking."

**Implementation (assistant.py):**
```python
TRIGGER_WORDS = ["прием"]  # configurable

def _handle_speech(self, audio):
    text = self.asr.transcribe(audio)    # VAD already collected the buffer
    text_lower = text.lower().strip()
    for tw in TRIGGER_WORDS:
        if text_lower.endswith(tw):
            # Strip trigger word, process the rest
            text = text_lower[:-len(tw)].strip().rstrip(' ,.!?…')
            break
    if not text:
        return  # only trigger word, nothing to process
    # send to LLM...
```

**Flow:**
1. VAD detects speech start → buffers audio
2. VAD detects speech end (silence after trigger word) → stops buffering
3. Whisper transcribes full audio including trigger word
4. Assistant strips trigger word, processes the clean text

**Pitfalls:**
- Whisper might transcribe "приём" (with ё) — word comparison must handle this
- Punctuation after trigger word ("прием,", "прием.") can break `.endswith()` — rstrip the text first
- If whisper misspells the trigger word, it won't be detected (no fallback)

**Why "прием"?** Radio communication style — natural to say at end of utterance. Easy to remember, short, distinct.

### Files

`~/Documents/local-siri/`:
- `assistant.py` — main loop: VAD → ASR → LLM → `say`
- `web_server.py` — Web UI over WebSocket
- `web/index.html` — browser interface
- `setup.py` — dependency checker
- `run.sh` — launcher (`./run.sh --help`)

### LLM Options

| Model | Format | RAM | How to run | Status |
|-------|--------|-----|-----------|--------|
| Qwen2.5-3B Q4_K_M | GGUF | ~2.0 GB | Ollama `qwen2.5:3b` or `llama-server` | ✅ Imported to Ollama |
| **QVikhr-3-4B Q4_K_S** | GGUF | **~2.4 GB** | Ollama `qvikhr-3-4b` or LM Studio | ✅ **Best Russian** |
| Vikhr-Qwen-1.5B 8bit | MLX | ~1.5 GB | `mlx_lm.generate()` | ⚠️ **10 tok/s (slow)** |
| Phi-4-mini MLX 4bit | MLX | ~2.0 GB | `mlx_lm.generate()` | ❌ **Broken Russian** |
| Gemma-4-E2B Q4_K_M | GGUF | **3.2 GB** | LM Studio | ❌ **Too heavy for 8GB** |

**Ollama is 2.4x faster than MLX for the same memory bandwidth.** On M1 Air 8GB:
- `qwen2.5:3b` via Ollama: **27 tok/s** (GGUF Q4, ~1.8GB GPU alloc)
- `qvikhr-3-4b` via Ollama: **20 tok/s** (GGUF Q4_K_S, ~3.4GB GPU alloc — tight!)
- Vikhr-Qwen-1.5B 8bit via mlx-lm: **11 tok/s** (MLX 8bit, ~1.6GB GPU alloc)
- Phi-4-mini MLX via mlx-lm: **11 tok/s** (broken Russian output)

**Why:** llama.cpp has mature, optimized Metal GPU kernels. MLX is newer and its quantized inference kernels aren't as tuned. Also, GGUF Q4 is more efficient than MLX 8bit (half the bandwidth per token).

**Terminal-only LLM server (no GUI):**
```bash
# With llama.cpp (brew install llama.cpp)
llama-server \
  -m ~/.lmstudio/models/Qwen/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf \
  --port 1234 \
  --ctx-size 2048 \
  --n-gpu-layers 99
```

**With mlx-lm (pip install mlx-lm):**
```python
from mlx_lm import load, generate
model, tokenizer = load("mlx-community/Qwen2.5-3B-Instruct-4bit")
# IMPORTANT: instruct models need chat template formatting
chat_prompt = "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
response = generate(model, tokenizer, prompt=chat_prompt, max_tokens=128)
```

**Ollama GGUF import (for custom GGUF files):**
```bash
# Create a Modelfile with path to GGUF
cat > /tmp/Modelfile << 'EOF'
FROM /path/to/model-Q4_K_M.gguf
TEMPLATE "{{ .Prompt }}"
EOF

# Import to Ollama
ollama create model-name -f /tmp/Modelfile

# Now can use via API or ollama run
curl http://localhost:11434/api/generate \
  -d '{"model":"model-name","prompt":"hello","stream":false}'
```

### Whisper Options (mlx-whisper, GPU)

| Model | RAM | Accuracy | Status |
|-------|-----|----------|--------|
| whisper-base-mlx | ~150 MB | Good Russian | ✅ Cached |
| whisper-small-mlx | ~460 MB | Better (recommended) | ✅ Cached |
| whisper-medium-mlx | ~1.2 GB | Best | ✅ Cached (heavy for 8GB) |
| whisper-large-v3-turbo | ~2.5 GB | Best | ✅ Cached (too heavy for 8GB) |

### Key Commands

```bash
./run.sh                # full mode
./run.sh --no-tts       # text only
./run.sh --no-web       # terminal only
./run.sh --check        # diagnostics
```

### Dependencies

```bash
brew install ffmpeg portaudio llama.cpp
pip3 install sounddevice silero-vad mlx-whisper fastapi uvicorn websockets
```

### Permissions

System Settings → Privacy → Microphone → enable Terminal/python3

---

## Generic Architecture

```
Microphone → STT (Whisper) → LLM (Ollama/LM Studio) → TTS (macOS say / Silero) → Speaker
```

## Components — API Reference

All confirmed working signatures. See `references/confirmed-api-and-measurements.md` for exact sizes, device IDs, and tested calls.

### Silero VAD (pip package)

```python
from silero_vad import load_silero_vad
model = load_silero_vad(onnx=True)        # CPU inference
iterator = model.get_iterator(threshold=0.5, min_silence_duration_ms=700)
result = iterator(chunk)                  # chunk: 512 samples @ 16kHz float32
# Returns: "start" | "end" | None
```

Note: API returns **strings** ("start"/"end"), not dicts. No torch.hub needed — model bundled in pip package.

### mlx-whisper

```python
import mlx_whisper
mlx_whisper.load_models("mlx-community/whisper-small-mlx")  # Note: load_models (plural!)
result = mlx_whisper.transcribe(
    audio_np,                              # numpy array, 16kHz float32
    path_or_hf_repo="mlx-community/whisper-small-mlx",
    language="ru",
    verbose=False,
    fp16=True,                             # GPU via Metal
)
text = result.get("text", "").strip()
```

### macOS TTS

```bash
say -v Milena "Привет"                     # Russian, preinstalled
say -v '?' | grep ru                       # List Russian voices
```

Available voice: **Milena** (ru_RU). Zero RAM, zero disk.

### Silero TTS v5 (if downloadable)

```python
import torch
model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts', language='ru', speaker='v5_ru')
model.to('cpu')
audio = model.apply_tts(text="Привет", speaker='xenia', sample_rate=48000, put_accent=True, put_yo=True)
```

- Disk: **145 MB** (v5_ru.pt) or **38 MB** (v4_ru.pt)
- RAM: ~150-200 MB
- Download URL: `https://models.silero.ai/models/tts/ru/v5_ru.pt`
- **Pitfall:** Cannot be reliably downloaded from China. Server has no Range/Resume.

## Crash Recovery — After System Overload

If the Mac crashed/shut down during testing (e.g. RAM overload on 8GB):

1. **Don't assume state.** Check filesystem first: `ls -la ~/Documents/local-siri/`
2. **Check running processes** — Ollama may have auto-started, LM Studio probably didn't.
3. **Check memory pressure** before loading anything: `memory_pressure | head -5`
4. **Free pages below 15000 (~250MB)** = do NOT load another model. Wait or close apps.
5. **Use session_search()** to recall what was being done before the crash — the user will expect you to remember without being told.
6. **Never re-launch a heavy process automatically.** Ask the user before starting llama-server, LM Studio, or loading large models on a crashed system.

## Resource Safety (M1 Air 8GB)

**WARNING: Running model benchmarks or speed tests on M1 Air 8GB can crash the system.**

This Mac has 8GB unified memory. Loading even two models concurrently (e.g. Whisper + LLM while macOS is already using ~2.5GB for UI+services) can push free pages to zero, causing a kernel panic / hard shutdown.

Rules for safety:
- **Only ONE model loaded at a time** during testing/benchmarking
- **Never run benchmarks unattended** — watch memory_pressure output
- **`memory_pressure` free pages < 20000 → abort any new model load**
- **Whisper large models** (medium: ~1.2GB, large-v3-turbo: ~2.5GB) are too heavy for 8GB — use small or base only
- **Ollama** keeps models in memory after inference — `ollama stop <model>` to free RAM
- **After a crash**, let the system cool down 30s before doing anything
- **When in doubt, ask the user** before proceeding — better a question than a crash

### Safe Benchmark Methodology

Use Ollama's built-in metrics for accurate speed measurement (avoids curl/tool overhead):

```bash
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:3b","prompt":"Write one sentence.","stream":false,"options":{"num_predict":50,"temperature":0}}' \
  | python3 -c "
import json,sys; d=json.load(sys.stdin)
tok_s = d['eval_count']/(d['eval_duration']/1e9) if d['eval_duration'] > 0 else 0
print(f'tok/s: {tok_s:.1f}')
print(f'gen: {d[\"eval_duration\"]/1e6:.0f}ms ({d[\"eval_count\"]} tok)')
print(f'prompt: {d[\"prompt_eval_duration\"]/1e6:.0f}ms ({d[\"prompt_eval_count\"]} tok)')
"
```

Key fields from Ollama API response:
- `eval_duration` — generation time in nanoseconds
- `eval_count` — tokens generated
- `prompt_eval_duration` — prompt processing time in nanoseconds
- `prompt_eval_count` — prompt tokens processed

For MLX models, use the test_mlx.py helper (chat template formatted prompt).

## Pitfalls

- **Building .xcodeproj projects requires full Xcode** — `xcodebuild` from Command Line Tools only works for SwiftPM packages. For .xcodeproj, you need Xcode.app (10+ GB). Workaround: use `swiftc` directly for single-file projects, or build on a Mac with Xcode and copy the binary.
- **.shortcut files cannot be imported unsigned** — macOS 14+ blocks unsigned `.shortcut` file imports via Shortcuts.app. Use Automator workflows (.workflow) or build a native app instead.
- **Carbon RegisterEventHotKey: kEventHotKeyReleased is unreliable** — confirmed: the keyUp event NEVER fires. Always use toggle mode (press to start, press to stop) when using Carbon API. For push-to-talk (hold to record), use CGEventTap with keyDown+keyUp — requires Accessibility permission.
- **Carbon RegisterEventHotKey may silently fail in LSUIElement/accessory apps** — on macOS 15+, Carbon hotkeys don't register reliably when the app has no dock icon and only a menu-bar presence. Use `NSApplication.shared.setActivationPolicy(.accessory)` instead of `LSUIElement = true` in Info.plist, or accept that hotkeys may not work at all in menu-bar-only apps.
- **F5 key may be captured by system** — On MacBooks, F5 is used for Dictation or keyboard brightness by default. Hotkey may need to use Fn+F5, or disable system shortcuts, or use a modifier (Option+F5).

- **Silero TTS from China** — `models.silero.ai` is too slow for files >38 MB. Use v4_ru (38 MB) instead of v5_ru (145 MB) — faster download, same speaker set. Requires `trust_repo=True` in torch.hub.
- **llama.cpp vs LM Studio** — llama.cpp is terminal-only, installed via `brew install llama.cpp`. Serve GGUF models with `llama-server`. Fast, light, no GUI.
- **mlx-lm instruct models need chat template** — Raw prompt to `generate()` returns None. Always format: `<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n`
- **Ollama benchmarks** — Don't use curl+time for wall-clock. Use Ollama's built-in `eval_duration`/`eval_count` from the /api/generate response for accurate tok/s.
- **Ollama stop frees memory** — Model stays in GPU after inference. Always `ollama stop <model>` before loading another.
- **Silero VAD API** — returns `"start"`/`"end"` strings, not dicts with keys.
- **PyTorch MPS** — `torch.backends.mps.is_available()` should be True on M-series.
- **HuggingFace from China** — may need HF token or use ModelScope mirror.
- **Microphone permissions** — System Settings → Privacy → Microphone.
- **LM Studio +8GB models** — any LLM >4B params in FP16 won't fit M1 8GB. Q4 GGUF only.
- **Audio device IDs** on this Mac: [0]=MacBook Air Microphone, [1]=Speakers, [2]=Jenya Microphone, [3]=Multi-Output.

## References

- `references/confirmed-api-and-measurements.md` — Exact API signatures, model sizes, audio device IDs tested on M1 MacBook Air
- `references/gradio-voice-ui.md` — Gradio voice UI example
- `references/seamlessm4t-transformers.md` — SeamlessM4T via transformers
- `references/native-swift-voicenote-app.md` — Minimal SwiftUI menu-bar voice transcription app (SFSpeechRecognizer + CGEventTap/Carbon hotkey + swiftc compile, no Xcode). Push-to-talk or toggle, saves to markdown file.
- `references/pindrop-fork-changes.md` — Exact file-by-file changes to add "Save to file" toggle to Pindrop (SettingsStore, OutputManager, AppCoordinator, StatusBarController). Requires full Xcode.app to build (.xcodeproj).
- `references/ready-made-voice-apps.md` — Comparison of existing open-source macOS dictation apps: TypeNo (★873), Pindrop (★527), MacParakeet (★299). Pros/cons and when to choose which.
- `references/voice-to-file-routing.md` — How to route dictation output to a specific .md file. Covers Handy log monitor, Apple Dictation + Shortcuts, custom Swift app, forking existing apps, and clipboard monitor approaches.
