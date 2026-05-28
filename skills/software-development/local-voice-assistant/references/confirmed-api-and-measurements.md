# Confirmed API Signatures, Sizes & Measurements

Tested on M1 MacBook Air, macOS 15.7.5, Python 3.12.

## Audio Devices

```python
import sounddevice as sd
devs = sd.query_devices()
# [0] MacBook Air Microphone (input)
# [1] MacBook Air Speakers (output)
# [2] Jenya Microphone (input)
# [3] Multi-Output Device (output)
```

## Silero VAD (pip package)

```python
from silero_vad import load_silero_vad
model = load_silero_vad(onnx=True)       # ONNX for CPU inference
iterator = model.get_iterator(
    threshold=0.5,
    min_silence_duration_ms=700          # ms silence to trigger end
)
result = iterator(audio_chunk)            # 512 samples @16kHz float32
# Returns: "start" | "end" | None
```

- Disk: **1.2 MB** (`silero_vad_v6.onnx`)
- RAM: **~5 MB** (ONNX Runtime)
- Bundled in pip package `silero-vad`, no torch.hub needed

## mlx-whisper

```python
import mlx_whisper

# Preload model (warmup)
mlx_whisper.load_models("mlx-community/whisper-small-mlx")

# Transcribe
result = mlx_whisper.transcribe(
    audio_np,                              # numpy array, 16kHz float32
    path_or_hf_repo="mlx-community/whisper-small-mlx",
    language="ru",
    verbose=False,
    fp16=True,                             # GPU via Metal
)
text = result.get("text", "").strip()
```

Available models in HF cache:
| Model | Path | Format |
|-------|------|--------|
| whisper-tiny-mlx | cached | .npz |
| whisper-base-mlx | cached | .npz |
| whisper-small-mlx | cached | .npz |
| whisper-medium-mlx | cached | .npz |
| whisper-large-v3-turbo | cached | .safetensors |

API: `mlx_whisper.load_models(name)` — note plural `load_models`, not `load_model`.

## Silero TTS v5

**Download URL:** `https://models.silero.ai/models/tts/ru/v5_ru.pt`
- Expected size: **145 MB** (confirmed via Content-Length header)
- Expected RAM: ~150-200 MB when loaded in PyTorch CPU

**Download URL (v4, smaller):** `https://models.silero.ai/models/tts/ru/v4_ru.pt`
- Expected size: **38 MB**
- Response code: 200 OK (both v4 and v5)

**NOTE:** `models.silero.ai` does NOT support Range/Resume. Speed from China: highly variable (1KB/s - 300KB/s). May timeout.

## macOS Built-in TTS

```bash
say -v Milena "Привет"  # Russian voice, preinstalled
say -v '?' | grep ru    # List Russian voices
```

Available Russian voice: **Milena** (ru_RU)
Zero RAM, zero disk beyond macOS system files.

## LM Studio

- Qwen2.5-3B-Instruct GGUF Q4_K_M: **2.0 GB** (completely downloaded)
- QVikhr-3-4B-Instruction GGUF Q4_K_S: **~1.8 GB downloaded of ~2.4 GB** (not complete)
- Vikhr-Qwen-1.5B-Instruct MLX 8bit: **~1.1 GB downloaded** (not complete)
- Gemma-4-E2B-it Q4_K_M: fully downloaded
- API: `http://localhost:1234/v1/chat/completions`

## LLM Benchmark Results (M1 Air 8GB, macOS 15.7.5)

All benchmarks via Ollama API's built-in `eval_duration`/`eval_count`. Temperature=0, 50 tok max.

### Ollama (llama.cpp Metal)

| Model | tok/s | GPU alloc | System RAM | Notes |
|-------|-------|-----------|------------|-------|
| qwen2.5:3b (Q4_K_M) | **27.0** | ~1.8 GB | ~1.1 GB | Best speed/RAM ratio |
| qwen2.5-coder:3b (Q4_K_M) | **27.0** | ~1.8 GB | ~0.6 GB | Same as plain 3B |
| qvikhr-3-4b (Q4_K_S) | **20.1** | **~3.4 GB** | ~2.5 GB | Heavy for 8GB! |

### mlx-lm (MLX native)

| Model | tok/s | GPU alloc | Notes |
|-------|-------|-----------|-------|
| Vikhr-Qwen-1.5B 8bit | **11.0** | ~1.6 GB | Chat template required |
| Phi-4-mini MLX 4bit | **10.8** | ~2.0 GB | Broken Russian |

### Key finding

llama.cpp/Ollama is **2.4x faster** than mlx-lm on M1 Air for the same memory bandwidth (both ~1.5GB data per token). Reason: llama.cpp's Metal kernels are more mature.

### Prompt processing (qwen2.5:3b)

| Prompt tokens | Time |
|-------------|------|
| 14 tok | 414 ms |
| 42-43 tok | 164-271 ms |


| Component | Actual RAM | Notes |
|-----------|-----------|-------|
| macOS 15.7.5 | ~2.5-3 GB | varies |
| Silero VAD ONNX | ~5 MB | confirmed |
| mlx-whisper small | ~460 MB | confirmed |
| Qwen3B Q4 GGUF | ~2.0 GB | confirmed |
| macOS say (Milena) | ~0 MB | NSSpeechSynthesizer, no model load |
| Python middleware | ~100 MB | FastAPI + audio buffers |
| **Total** | **~5.1-5.6 GB** | ~2.5-3 GB headroom on 8GB |
