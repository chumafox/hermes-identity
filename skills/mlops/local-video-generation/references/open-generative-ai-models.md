# Open Generative AI Model Download Sources

## App Info
- Name: Open Generative AI v1.0.9
- Bundle ID: `ai.generative.open`
- Location: `/Applications/Open Generative AI.app`
- Electron app (Next.js-based UI, bundled as app.asar)

## Data Directory Structure

```
~/Library/Application Support/open-generative-ai/local-ai/
├── bin/
│   ├── sd-clli                          # 26 MB, compiled for macOS 26.0
│   └── sd-cli-metal-macos-arm64/
│       └── libstable-diffusion.dylib    # Metal shader lib for Apple Silicon
├── models/                             # Target dir for sd.cpp models
│                                       # (empty = no models installed yet)
├── tmp/
└── wan2gp.json                         # {"url": "http://localhost:7860"}
```

Other Electron data in the same parent directory:
- `~/Library/Application Support/open-generative-ai/Preferences` — Electron JSON prefs
- Cache, GPUCache, Local Storage, Session Storage, etc.

## Models Listed in UI

Models are specific to sd.cpp backend. The UI shows them with "Download" buttons. Actual download URLs depend on what the app fetches from its model registry. Standard HuggingFace equivalents:

| UI Name | Likely HF Source | Size | Format |
|---------|------------------|------|--------|
| Z-Image Turbo | WaveSpeed/tongyi — check HuggingFace | 2.5 GB | safetensors |
| Z-Image Base | tongyi-mai/z-image-base — check HuggingFace | 3.5 GB | safetensors |
| Dreamshaper 8 | lykon/dreamshaper-8 | 2.1 GB | safetensors (SD1.5) |
| Realistic Vision v5.1 | SG161222/Realistic_Vision_V5.1_noVAE | 2.1 GB | safetensors (SD1.5) |
| Anything v5 | stablediffusionapi/anything-v5 | 2.1 GB | safetensors (SD1.5) |
| SDXL Base 1.0 | stabilityai/stable-diffusion-xl-base-1.0 | 6.9 GB | safetensors (SDXL) |

Components for Z-Image:
- Qwen3-4B Text Encoder (2.4 GB) — likely from Qwen/Qwen3-4B or similar
- FLUX VAE (335 MB) — black-forest-labs/FLUX.1-dev VAE component

## How to Download

1. **Via app UI (easiest):** Open Open Generative AI → navigate to Local Models → click "Download" on any model. The app should handle progress and placement.
2. **Manually (if UI buttons fail):** Download the safetensors files from HuggingFace (use HF-Mirror in China) and place in `local-ai/models/`. The app may not auto-detect them — may need app restart or scanning.
3. **Wan2GP models:** These auto-download on first use when the Wan2GP server is running. No manual download needed.

## macOS Compatibility Issue

The `sd-cli` binary bundled with v1.0.9 was compiled for macOS 26.0 (Sequoia+). On macOS 14.x (Sonoma) it crashes immediately:

```
dyld[NNNNN]: Symbol not found: _OBJC_CLASS_$_MTLResidencySetDescriptor
  Referenced from: .../sd-cli (built for macOS 26.0 which is newer than running OS)
  Expected in: /System/Library/Frameworks/Metal.framework/Versions/A/Metal
```

This is a Metal API version mismatch — `MTLResidencySetDescriptor` was added in
macOS 25+/Sequoia. No workaround exists; the app developer must recompile
sd-cli with a lower deployment target.

## Wan2GP Server Connection

The app connects to Wan2GP at localhost:7860 by default, configured via `wan2gp.json`. Click "Test" in Settings → Wan2GP server to verify. Shows "Connected to Gradio X.Y.Z" when working.
