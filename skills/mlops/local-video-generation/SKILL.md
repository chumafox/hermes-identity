---
name: local-video-generation
description: Set up and manage local video generation infrastructure on Apple Silicon (WanGP/Wan2GP) for use with UI apps like Open Generative AI. Covers installation, Gradio patching for macOS, MPS compatibility, and server lifecycle.
version: 1.0.0
tags: [video-generation, wangp, wan2gp, mps, apple-silicon, gradio]
platforms: [macos]
triggers:
  - "set up video generation"
  - "install wan2gp"
  - "run wangp server"
  - "connect open generative ai to video models"
  - "download models in open generative ai"
  - "open generative ai models"
  - "gradio startup failure"
  - "localhost not accessible gradio"
  - "sd.cpp integration"
  - "local image generation"
  - "z-image model"
---

# Local Video Generation on Apple Silicon (WanGP)

## Overview

WanGP (also referred to as Wan2GP in some UIs) is an open-source video generation server that supports multiple models (Wan 2.2, LTX Video, Hunyuan Video, Flux.1 Dev, Qwen Image) and runs on Apple Silicon via MPS (Metal Performance Shaders).

**Architecture:** WanGP is the backend server. Frontend UIs like Open Generative AI connect to it via HTTP API. The server provides a Gradio web UI and a REST API that the UI uses for model inference.

**GitHub:** https://github.com/deepbeepmeep/Wan2GP

## Prerequisites

- macOS 14+ with Apple Silicon (M1/M2/M3/M4)
- Python 3.11+ (WanGP explicitly requires this)
- Git
- ~4 GB free disk space for models

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/deepbeepmeep/Wan2GP.git
cd Wan2GP
```

### 2. Install Python 3.11

```bash
brew install python@3.11
```

### 3. Create venv and install dependencies

```bash
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

# Install PyTorch with CPU index (no CUDA on macOS)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install all WanGP dependencies
pip install -r requirements.txt
```

The `requirements.txt` includes: diffusers, transformers, mmgp, gradio, opencv, torchvision, and many media/audio libraries.

**Note:** `pip install -r requirements.txt` may take 5-15 minutes depending on network speed. Run it in background.

### 4. Patch Gradio for macOS startup issues

Gradio 5.x on macOS with outdated LibreSSL fails during startup with:

```
Exception: Couldn't start the app because 'http://localhost:7860/gradio_api/startup-events'
failed (code 503). Check your network or proxy settings to ensure localhost is accessible.
```

**Root cause:** Gradio tries to make an HTTPS GET to `localhost:PORT/startup-events` during `launch()`. On macOS with LibreSSL 2.8.3 (no modern CA bundle), TLS verification fails even for localhost. Then a subsequent `url_ok()` health check also fails, throwing `ValueError: When localhost is not accessible`.

**Fix:** Patch `gradio/blocks.py` in the venv to bypass both checks:

```python
# In <venv>/lib/python3.11/site-packages/gradio/blocks.py

# 1. Replace the startup-events HTTP call with direct call (around line 2711):
# BEFORE:
resp = httpx.get(
    f"{self.local_api_url}startup-events",
    verify=ssl_verify,
    timeout=None,
)

# AFTER:
self.run_startup_events()


# 2. Replace the url_ok() check (around line 2748):
# BEFORE:
if (
    _frontend
    and not wasm_utils.IS_WASM
    and not networking.url_ok(self.local_url)
    and not self.share
):
    raise ValueError(...)

# AFTER:
if (
    _frontend
    and not wasm_utils.IS_WASM
    and not self.share
):
    pass
```

This fix is safe for local-only usage. The startup events still run — they're just called directly instead of via HTTP.

## Usage

### Start the server

```bash
cd /path/to/Wan2GP
source venv/bin/activate
python wgp.py --listen --server-name 0.0.0.0 --server-port 7860
```

Flags:
- `--listen` — bind to 0.0.0.0 (accessible from other devices on network)
- `--server-name` — host to bind to (0.0.0.0 for external access, localhost for local-only)
- `--server-port` — port (default 7860)

Server output when successful:
```
* Running on local URL:  http://0.0.0.0:7860
Autosave: Queue is empty, nothing to save.
```

### Connect from Open Generative AI

1. Open Open Generative AI app
2. Go to Wan2GP settings / server configuration
3. Enter the server URL: `http://localhost:7860` (or the Mac's IP if connecting from another device)
4. Models will appear as available (previously showed "Server offline")

### First load behavior

On first access, Gradio may take 30-60 seconds to generate the UI (it compiles templates). Subsequent loads are faster. Models themselves are downloaded on first use — the WanGP server auto-downloads the required model files.

## Available Models via WanGP

| Model | Type | Notes on MPS |
|-------|------|-------------|
| Wan 2.2 (Text-to-Video) | video | Works on MPS, slower on consumer GPUs |
| Wan 2.2 (Image-to-Video) | video | Provide a start frame |
| LTX Video | video | **Fastest video option in WanGP** |
| Hunyuan Video | video | Works on MPS |
| Flux.1 Dev | image | MPS compatible |
| Qwen Image | image | MPS compatible |

From the WanGP README: *"MPS / Apple Early Support: Mac users are about to discover the world of WanGP albeit for start it wont be fast nor very optimized and not all models will be supported."*

## Pitfalls

- **Always run the server in background** — long-running process must use `background=true` and `notify_on_complete=true`.
- **`venv/bin/python -u` is critical** — unbuffered output (`-u`) ensures log messages appear in real-time. Without it, all output may arrive at once on crash.
- **Run from Wan2GP directory** — `wgp.py` uses relative paths to `models/_settings.json` and other config files. Always `cd /path/to/Wan2GP` first.
- **Gradio first-load delay** — on the very first connection, Gradio may take 30-60 seconds to respond. Subsequent requests are fast (50-200ms).
- **No `--port` flag exists** — WanGP uses `--server-port`, not `--port`. Passing `--port` will cause `unrecognized arguments` error.
- **MPS BF16 unsupported** — Apple M1/M2/M3/M4 Pro chips do not support BF16 in hardware. WanGP detects this and falls back to FP16 automatically.
- **AV class conflicts** — You'll see warnings about `AVFFrameReceiver` and `AVFAudioReceiver` being implemented in multiple libraries. These are benign and can be ignored.

## Troubleshooting

### Server starts but models show "Server offline" in UI

1. Check the WanGP server is actually running: `curl http://localhost:7860/`
2. Verify the URL in Open Generative AI settings matches the server URL
3. Check that the server started without errors (review stderr logs)
4. On first launch, the server needs time to auto-download models — check server logs for download progress

### "Couldn't start the app because 'http://localhost:7860/gradio_api/startup-events' failed"

Apply the Gradio patch described above. It's the SSL verification failing on macOS with outdated CA certificates.

### "ValueError: When localhost is not accessible"

Apply the Gradio patch for the `url_ok()` check. On macOS the health check probes take too long or fail due to SSL issues.

### Server stops after Gradio error

Review stderr and stdout logs separately. The Gradio error print to stderr but the "Running on" message goes to stdout. Check both:

```bash
tail -20 /tmp/wgp_stderr.log
tail -20 /tmp/wgp_stdout.log
```

### ffmpeg warnings about conflicting libraries

```
Class AVFFrameReceiver is implemented in both ...libavdevice.61... and ...libavdevice.62...
```

This is harmless. Two Python packages (opencv and av) bundle different versions of FFmpeg libraries. Both work.

## Open Generative AI — Companion sd.cpp Integration

Open Generative AI (v1.0.9, bundle ID `ai.generative.open`) is an Electron desktop app that combines two local inference backends under one UI:

| Backend | Role | Status |
|---------|------|--------|
| **Wan2GP (WanGP) server** | Video/image generation (Wan, LTX, Hunyuan, Flux, Qwen) | Runs separately as a Gradio server on port 7860 |
| **sd.cpp (sd-cli binary)** | Image generation (SD1.5, SDXL, FLUX, Z-Image) | Bundled in the app's data directory |

### Data Directory

```
~/Library/Application Support/open-generative-ai/local-ai/
├── bin/
│   ├── sd-cli                          # sd.cpp binary (26 MB)
│   └── sd-cli-metal-macos-arm64/
│       └── libstable-diffusion.dylib   # Metal backend for Apple Silicon
├── models/                             # <-- sd.cpp model files go here (empty = no models)
├── tmp/
└── wan2gp.json                         # {"url": "http://localhost:7860"}
```

### Models Available in UI

| Model | Size | Type | Notes |
|-------|------|------|-------|
| Z-Image Turbo | 2.5 GB | Turbo | 8-step, fast. Needs Qwen3-4B TE (2.4 GB) + FLUX VAE (335 MB) |
| Z-Image Base | 3.5 GB | Quality | 50-step. Needs same components |
| Dreamshaper 8 | 2.1 GB | SD 1.5 | Versatile, photorealistic + artistic |
| Realistic Vision v5.1 | 2.1 GB | SD 1.5 | Photorealistic people |
| Anything v5 | 2.1 GB | SD 1.5 | Anime/illustration |
| SDXL Base 1.0 | 6.9 GB | SDXL | High-resolution |

Models download into `local-ai/models/` when clicking "Download" in the app UI. The app does not expose an external API for triggering downloads — use the app's UI buttons.

### sd-cli macOS Compatibility

The bundled `sd-cli` binary was compiled for **macOS 26.0** (Sequoia+) and references `MTLResidencySetDescriptor` from Metal.framework. On **macOS 14.x (Sonoma)** it crashes immediately:

```
dyld: Symbol not found: _OBJC_CLASS_$_MTLResidencySetDescriptor
```

This means Open Generative AI's sd.cpp backend will NOT run on macOS <26.0. The Wan2GP server integration still works fine — only the sd-cli side is affected.

### Wan2GP Connection

Configured via `wan2gp.json` in the app data dir. Standard setup points to `http://localhost:7860`. Click "Test" in the app to verify — shows "Connected to Gradio X.Y.Z" when the Wan2GP server is running.

## Related Files

- `references/wangp-setup-session.md` — Full session transcript reference
- `references/open-generative-ai-models.md` — Model download sources and paths for Open Generative AI
