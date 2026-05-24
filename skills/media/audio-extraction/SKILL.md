---
name: audio-extraction
description: Extract audio from video files (MP4, MOV, etc.) for transcription (Whisper), analysis, or archival. Covers ffmpeg usage, bulk conversion, and macOS-specific pitfalls with non-ASCII filenames.
domains: media, mlops
triggers:
  - "extract audio"
  - "convert video to audio"
  - "get audio for transcription"
  - "wav from mp4"
  - "ffmpeg audio batch"
---

# Audio Extraction

## Quick Start

Extract a single video to 16kHz mono WAV (optimal for Whisper/faster-whisper):

```bash
ffmpeg -i input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav -y
```

**Flag breakdown:**
- `-vn` — drop video stream
- `-acodec pcm_s16le` — 16-bit signed little-endian PCM (WAV)
- `-ar 16000` — 16kHz sample rate (Whisper standard)
- `-ac 1` — mono
- `-y` — overwrite output without prompt
- `-loglevel error` — suppress progress output (for batch scripts)

## CRITICAL: Always Run Bulk Tasks in Background

**USER MANDATE:** Long conversions and large model downloads MUST run in the background (`background=true`) or be delegated to a subagent. Never block the user's chat with a foreground process — the agent must remain responsive.

```python
# RIGHT — stays responsive:
terminal(command="python3 convert_all.py ...", background=true, notify_on_complete=true)

# WRONG — blocks the conversation:
terminal(command="python3 convert_all.py ...")  # DON'T
```

When the user says "ну" or "давай" after an interruption, just re-run the same command — `-c` / resume logic handles the rest.

### Checking Background Progress

After starting a background task, check progress without blocking:

```python
# Poll the process for current progress
process(action="poll", session_id="proc_xxx")
# Returns: status=running, uptime_seconds, output_preview

# Or check file growth directly
terminal("du -h /path/to/output/file")
```

Don't ask the user to check progress — just poll and report back. The `output_preview` from aria2c shows percentage, MiB downloaded, speed, and ETA. For scripts, check file count or size increase.

## Bulk Conversion

### Recommended: Python (robust with non-ASCII names)

```python
from pathlib import Path
import subprocess

SRC = Path("/path/to/videos")
DST = Path("/path/to/audio_output")

for mp4 in sorted(SRC.rglob("*.mp4")):
    rel = mp4.relative_to(SRC)
    wav = DST / rel.with_suffix(".wav")
    if wav.exists():
        continue
    wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-i", str(mp4), "-vn",
         "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
         str(wav), "-y", "-loglevel", "error"],
        check=True
    )
```

### Alternative: bash (works for ASCII-only paths)

```bash
#!/bin/bash
SRC="/path/to/videos"
DST="/path/to/audio_output"

find "$SRC" -name '*.mp4' -print0 | while IFS= read -r -d '' f; do
    base=$(basename "$f")
    dirpart=$(dirname "$f" | sed "s|$SRC/||")
    wav="$DST/$dirpart/${base%.mp4}.wav"
    mkdir -p "$DST/$dirpart"
    ffmpeg -i "$f" -vn -acodec pcm_s16le -ar 16000 -ac 1 "$wav" -y -loglevel error
done
```

## Format Guide

| Format | Size/hr | Use case |
|--------|---------|----------|
| WAV 16kHz mono 16-bit | ~60 MB | Best for STT (Whisper, faster-whisper) |
| MP3 128k | ~25-30 MB | Compact, decent quality |
| WAV 44.1kHz stereo | ~300 MB | Full quality for music/analysis |

## Pitfalls

- **macOS + bash `find` + Russian/Cyrillic filenames:** `find` can return paths with the leading `/` truncated (e.g., `Users/...` instead of `/Users/...`). Use Python's `Path.rglob()` instead — it handles Unicode paths correctly.
- **AAC decode errors:** Some MP4 files have corrupted AAC streams. ffmpeg will still produce a WAV (with silence during bad sections) but log "channel element 0.0 duplicate" errors. This is usually safe to ignore.
- **xargs with long paths:** `xargs -I` can fail with "command line cannot be assembled, too long" when paths contain spaces and special characters. Use `while read` loops or Python instead.
- **`export -f` in bash:** Exporting functions with `export -f` can cause variable scope issues in subshells. Avoid it; use inline processing or Python.
- **Always test on one file first** before running bulk conversion.

## Complete Pipeline: Video → Audio → Transcription → Obsidian Vault → Compiled Reference

For a fully automated workflow from video lectures to an Obsidian knowledge base:

1. **Extract audio** — `python3 bulk_convert_to_wav.py /path/to/videos /path/to/audio`
2. **Transcribe** — `python3 transcribe_to_obsidian.py /path/to/audio --source "course-name" --tags "lecture"` 
3. **Load into Obsidian** — point your vault at the audio directory (or copy .md files in)
4. **Compile into one reference doc** — see `references/compile-transcripts.md` to combine all .md files into one structured document with section headers

Both scripts skip existing files — re-run anytime to catch new additions.

Run each step in background:
```python
terminal(command="python3 bulk_convert_to_wav.py /input /output", background=true, notify_on_complete=true)
```

### Compiling Transcripts into One Reference Document

After transcription, combine all .md files into one structured document using the script pattern in `references/compile-transcripts.md`:

```bash
python3 << 'EOF'
# See references/compile-transcripts.md for the full script
EOF
```

The bundled `scripts/transcribe_to_obsidian.py` generates basic frontmatter.

For German-language content, see `references/german-local-stt-tts.md` for fastest local STT (whisper) and TTS (piper/macOS say) options. To add custom fields (e.g., `source`, `tags`, `category`), edit the template in the script:

```python
# Inside transcribe_to_obsidian.py — customize this block:
md_content = f"""---
title: "{wav.stem}"
source: "my-course-name"       # ← customize per project
tags: [lecture, anti-age]      # ← add relevant tags
duration_min: {duration_sec/60:.1f}
transcribed_at: "{datetime.now():%Y-%m-%d %H:%M}"
model: "{args.model}"
---

{text}
"""
```

## Related: Video Generation Pipeline

After transcribing lecture/educational videos, you may want to generate AI video content. See the `local-video-generation` skill for WanGP/Wan2GP setup on Apple Silicon — covers installation, Gradio patching for macOS SSL issues, MPS compatibility, and connecting from Open Generative AI or other UIs.

## Next Step: Transcription with MLX Whisper

After extracting WAV files, transcribe them locally with `mlx-whisper` (Apple Silicon)

> **Note:** `mlx_whisper.transcribe(verbose=False)` still shows an audible-only progress bar (frames/sec) in stderr. This is normal — the bar indicates decoding progress and doesn't corrupt the transcript text output.

### Install

```bash
pip3 install mlx-whisper
```

### Model Download

The model is large-v3-turbo (~1.5 GB). Download via aria2c (resumable):

```bash
# Create download directory
mkdir -p ~/Downloads/whisper_model

# Download model files (small ones via Python)
python3 -c "
import requests, os
files = {'config.json', 'README.md', '.gitattributes'}
for name in files:
    r = requests.get(f'https://hf-mirror.com/mlx-community/whisper-large-v3-turbo/resolve/main/{name}')
    with open(f'~/Downloads/whisper_model/{name}', 'wb') as f:
        f.write(r.content)
"

# Download weights.safetensors (1.5 GB) with aria2c
# On macos with old LibreSSL, use --check-certificate=false
aria2c -c -x 4 -s 4 --check-certificate=false \
  --out=weights.safetensors \
  --dir=~/Downloads/whisper_model \
  "https://hf-mirror.com/mlx-community/whisper-large-v3-turbo/resolve/main/weights.safetensors"
```

### Manual HF Cache Population

When `snapshot_download()` times out on the large file, populate the HF hub cache manually:

```bash
# 1. Compute SHA256
SHASUM=$(shasum -a 256 weights.safetensors | cut -d' ' -f1)

# 2. Find existing cache structure (snapshot_download may have created partial layout)
CACHE_DIR="$HOME/.cache/huggingface/hub"
MODEL_CACHE="$CACHE_DIR/models--mlx-community--whisper-large-v3-turbo"

# 3. Copy blob and symlink
cp weights.safetensors "$MODEL_CACHE/blobs/$SHASUM"
SNAPSHOT_HASH=$(ls "$MODEL_CACHE/snapshots/")
ln -sf "../../blobs/$SHASUM" "$MODEL_CACHE/snapshots/$SNAPSHOT_HASH/weights.safetensors"

# 4. Verify
ls -la "$MODEL_CACHE/snapshots/$SNAPSHOT_HASH/"
```

### Bulk Transcription

```python
import mlx_whisper
from pathlib import Path

SRC = Path("/path/to/wav/files")
MODEL = "mlx-community/whisper-large-v3-turbo"

for wav in sorted(SRC.rglob("*.wav")):
    md = wav.with_suffix(".md")
    if md.exists():
        continue  # skip already transcribed
    
    result = mlx_whisper.transcribe(str(wav), path_or_hf_repo=MODEL, verbose=False)
    text = result["text"].strip()
    
    md.write_text(f"""---
title: "{wav.stem}"
transcribed_at: "{datetime.now():%Y-%m-%d %H:%M}"
model: "whisper-large-v3-turbo"
---

{text}
""")
```

### Obsidian Template

A reusable Obsidian-compatible transcription script is available at `scripts/transcribe_to_obsidian.py` — run it with:

```bash
python3 ~/.hermes/skills/media/audio-extraction/scripts/transcribe_to_obsidian.py \
  /path/to/wav_dir \
  --model mlx-community/whisper-large-v3-turbo
```

The script skips already-transcribed files and adds Obsidian frontmatter.

## Verification

After bulk conversion or transcription, verify count matches:

```bash
echo "WAV: $(find $DST -name '*.wav' | wc -l)"
echo "MP4: $(find $SRC -name '*.mp4' | wc -l)"
```

Pro tip: save the conversion script as `convert_audio.py` next to your source videos so you can re-run it — it'll skip existing files.

A reusable script is also bundled with this skill at `scripts/bulk_convert_to_wav.py` — copy it anywhere with:
```bash
cp ~/.hermes/skills/media/audio-extraction/scripts/bulk_convert_to_wav.py .
python3 bulk_convert_to_wav.py /path/to/videos /path/to/output
```
