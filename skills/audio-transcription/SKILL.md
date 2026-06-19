---
name: audio-transcription
description: "Transcribe audio files (mp3, m4a, wav, etc.) to text from the terminal using local MLX Whisper on Apple Silicon. No servers, no GUI."
tags: ["transcription", "whisper", "mlx", "audio", "speech-to-text"]
---

# Audio Transcription (MLX Whisper)

Transcribe audio files to text locally on Apple Silicon Macs using `mlx-whisper`. No internet required after model download.

## Prerequisites

```bash
pip install mlx mlx-whisper mlx-metal
```

Model is downloaded automatically on first run, OR you can point to a pre-downloaded model:

**Cache location:** `~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/`

Pre-downloaded MLX models on this Mac:
- `mlx-community/whisper-large-v3-turbo` (~1.5GB) — best quality/speed balance
  - Location: `~/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/`
- `openai/whisper-small` — smaller, faster, lower quality

**GGML models** (for whisper.cpp / Vibe app):
- `ggml-large-v3-turbo.bin` (~1.5GB) — Location: `~/Library/Application Support/github.com.thewh1teagle.vibe/`
- `ggml-model-whisper-small.bin` (~465MB) — Location: `~/Library/Application Support/MacWhisper/models/`

Other Whisper model variants available on HuggingFace (need separate download).

## Basic Usage

```bash
# Transcribe English audio, output txt file in CWD
mlx_whisper /path/to/file.mp3 --model mlx-community/whisper-large-v3-turbo --language en --output-format txt

# Transcribe Russian audio
mlx_whisper /path/to/file.mp3 --model mlx-community/whisper-large-v3-turbo --language ru --output-format txt
```

## Output Formats

mlx_whisper supports: `txt`, `vtt`, `srt`, `tsv`, `json`, `all`

**NOTE:** `--output-format md` is NOT supported. For .md output, transcribe to txt first then rename/convert:

```bash
mlx_whisper file.mp3 ... --output-format txt
mv "file.txt" "file.md"
```

## Output Location

mlx_whisper saves output in **the current working directory**, not next to the source file. Always check CWD or use `--output-dir`:

```bash
mlx_whisper file.mp3 ... --output-dir /path/to/output
```

## Batch Transcription

```bash
# Transcribe all mp3/m4a files in a directory
for f in ~/Downloads/*.mp3; do
  outname=$(basename "$f" .mp3)
  echo "Transcribing: $f"
  mlx_whisper "$f" --model mlx-community/whisper-large-v3-turbo --language en --output-format txt --output-dir ~/Downloads/transcripts
done
```

## Large File Handling (150MB+)

For long recordings (1+ hour), large-v3-turbo handles them fine on M-series Macs. Expect:
- 152MB mp3 file → ~1-2 minutes of processing
- Output ~60-130KB of text (depending on speaking speed)

## Pitfalls

- **CWD matters** — output goes to current working directory by default, not the source file directory. Use `--output-dir` or check CWD.
- **No .md output format** — only txt/vtt/srt/tsv/json/all. Rename after.
- **Model must be in cache** — first run downloads the model (~1.5GB). Pre-download if offline.
- **mlx_whisper binary location** — installed to the same venv/bin as pip. If `mlx_whisper: command not found`, use `python3 -m mlx_whisper` instead.
- **Multiple languages in one file** — mlx-whisper uses the specified language for the whole file. Code-switching (English + Russian mixed) may produce errors.
- **English-only models** — some models are en-only (whisper-tiny.en, whisper-base.en). Use large-v3-turbo for multilingual.

**Related skills:** china-networking

