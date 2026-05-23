# German Language: Fastest Local STT & TTS

## Speech-to-Text (Whisper)

### Fastest option on Apple Silicon

**`mlx-community/whisper-large-v3-turbo`** — already the fastest local Whisper for German on Apple Silicon.
- Runs at ~x19 realtime on M-series Macs via MLX
- German language detection is automatic (MLX Whisper detects language per file)
- ~1.5 GB model, loaded once and reused across multiple files
- Usage: `mlx_whisper.transcribe("file.wav", path_or_hf_repo="mlx-community/whisper-large-v3-turbo")`

### Smaller / faster alternatives (if needed)

| Model | Size | Speed | German quality |
|-------|------|-------|----------------|
| `mlx-community/whisper-turbo` | ~1 GB | slightly faster | good |
| `mlx-community/whisper-small` | ~500 MB | ~2× faster | acceptable |
| `mlx-community/whisper-base` | ~250 MB | ~3× faster | mediocre |

For German transcription quality, `large-v3-turbo` is the recommended minimum — smaller models struggle with compound words and proper nouns common in German.

## Text-to-Speech

### Option 1: macOS `say` (fastest, zero setup)

```bash
# Available German voices (built into macOS):
say -v '?' | grep de_DE

# Anna     de_DE  (basic)
# Eddy     de_DE  (German voice)
# Flo      de_DE  (German voice)
# Grandma  de_DE
# Grandpa  de_DE
# Reed     de_DE
# Rocko    de_DE
# Sandy    de_DE
# Shelley  de_DE

# Usage:
say -v Anna "Hallo, das ist ein Test."
say -v Anna -o output.m4a "Hallo, das ist ein Test."
```

**Speed**: <100ms latency, x500+ realtime. Zero model download needed.
**Quality**: Classic concatenative TTS. Understandable but robotic.
**Note**: Some voices may need first-time download (takes ~30 seconds on first use).

### Option 2: Piper TTS (installed via pip, ONNX-based)

```bash
pip3 install piper-tts
```

**Available German voices** (from HF, multiple quality levels):

| Voice ID | Quality | Size | Speed |
|----------|---------|------|-------|
| `speaches-ai/piper-de_DE-thorsten-low` | low | ~5 MB | x50-100 realtime |
| `speaches-ai/piper-de_DE-thorsten-medium` | medium | ~30 MB | x20-30 realtime |
| `speaches-ai/piper-de_DE-thorsten-high` | high | ~100 MB | x5-10 realtime |
| `speaches-ai/piper-de_DE-kerstin-low` | low | ~5 MB | fast |
| `speaches-ai/piper-de_DE-eva_k-x_low` | extra low | ~2 MB | fastest piper |
| `speaches-ai/piper-de_DE-ramona-low` | low | ~5 MB | fast |
| `ufozone/piper-de_DE-jarvis-low` | low | ~5 MB | fast |
| `speaches-ai/piper-de_DE-mls-medium` | medium | ~30 MB | good quality |

**Usage:**
```python
import piper
voice = piper.PiperVoice("speaches-ai/piper-de_DE-thorsten-low")
audio = voice.synthesize("Hallo, ich bin eine deutsche Sprachsynthese.")
# Audio is 16-bit PCM at 22050 Hz (mono)
```

## Recommendation Summary

| Use case | STT | TTS |
|----------|-----|-----|
| Max speed | mlx-whisper large-v3-turbo | macOS `say` (Anna/Eddy) |
| Good quality | mlx-whisper large-v3-turbo | Piper thorsten-medium |
| Best quality | same | Piper thorsten-high |
