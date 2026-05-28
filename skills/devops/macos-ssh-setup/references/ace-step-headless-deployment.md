# ACE-Step-1.5 — Headless Deployment Plan

ACE-Step-1.5 is a local music generation model (text2music, 10K+ stars on GitHub).

**Repo:** https://github.com/ace-step/ACE-Step-1.5
**Gitee mirror:** https://gitee.com/mirrors/ACE-Step-1.5

## Requirements for M1 Pro (32GB)
- Python 3.11-3.12
- PyTorch with MPS backend
- MLX for Apple Silicon acceleration
- Models: ~10-15 GB download

## Key Models
| Model | Purpose | Repo |
|---|---|---|
| acestep-v15-turbo | DiT (main generation) | ACE-Step/Ace-Step1.5 |
| acestep-5Hz-lm-1.7B | Language model (lyrics/thinking) | ACE-Step/Ace-Step1.5 |
| vae | Audio encoding/decoding | ACE-Step/Ace-Step1.5 |
| Qwen3-Embedding-0.6B | Text embeddings | ACE-Step/Ace-Step1.5 |

## Deployment Strategy (Chinese Internet)

### Plan A: Direct install (if internet works)
```bash
git clone --depth 1 https://gitee.com/mirrors/ACE-Step-1.5.git /tmp/ace-step
cd /tmp/ace-step
cp .env.example .env
echo "ACESTEP_DOWNLOAD_SOURCE=modelscope" >> .env
echo "ACESTEP_LM_BACKEND=mlx" >> .env
uv sync --timeout 120
uv run acestep-api --host 0.0.0.0 --port 8001 --download-source modelscope
```

### Plan B: Screen Mac bundle (if internet fails)
1. Screen Mac clones repo → `uv sync` → caches dependencies
2. Screen Mac downloads models via ModelScope/HuggingFace
3. Tar everything → SCP to headless Mac
4. Headless Mac extracts and runs

## Model Download Sources
- **ModelScope** (preferred in China): modelscope.cn
- **HuggingFace** (fallback): huggingface.co

Set via `ACESTEP_DOWNLOAD_SOURCE=modelscope` or `--download-source modelscope`.

## Runtime
- API server: `uv run acestep-api --host 0.0.0.0 --port 8001`
- Gradio UI: `bash start_gradio_ui_macos.sh`
- Models lazy-load on first request (fast startup)

## Instructions File
Full step-by-step: `/tmp/ACE_STEP_INSTRUCTIONS.md` (on both Macs)
