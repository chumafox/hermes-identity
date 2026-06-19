# HuggingFace Download from China — Tested Methods

Tested on: **headless Mac (pro)**, China, June 2026
Network: **Shadowrocket TUN** (utun4, no working SOCKS5, direct access works)

## Quick Summary

| Method | Works? | Speed | Notes |
|--------|--------|-------|-------|
| **Direct HF (through TUN)** | ✅ Yes | ~1.8s/it (gpt2) | Most reliable for `huggingface_hub` Python lib |
| **hf-mirror.com** (curl/wget) | ✅ Yes | ~0.9s host | Good for single files, direct download |
| **hf-mirror.com + HF_ENDPOINT** (Python) | ❌ FAILS | — | SSL error: "Distant resource does not seem to be on huggingface.co" |
| **ModelScope** (modelscope.cn) | ✅ Yes | 0.3s host | Fastest for Chinese models (Qwen, DeepSeek, ChatGLM) |

## Working Methods

### Method 1: Direct HF through TUN (Python)

When Shadowrocket/V2rayU TUN is active, `huggingface_hub` works without proxy:

```bash
unset HF_ENDPOINT
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('bert-base-uncased', local_dir='./model')
"
```

TUN captures all system traffic — no `HF_ENDPOINT` or proxy config needed.

### Method 2: hf-mirror.com (curl/wget)

For downloading individual files directly:

```bash
curl -LO "https://hf-mirror.com/bert-base-uncased/resolve/main/config.json"
wget -c "https://hf-mirror.com/bert-base-uncased/resolve/main/pytorch_model.bin"
```

### Method 3: ModelScope (recommended for Chinese models)

```bash
pip install modelscope
python3 -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen2.5-7B', local_dir='./model')
"
```

Fastest option — servers inside China. Best for Qwen, DeepSeek, ChatGLM, Baichuan.

## Known Pitfall: huggingface_hub + hf-mirror SSL Error

`HF_ENDPOINT=https://hf-mirror.com` combined with TUN/utun4 causes:
```
FileMetadataError: Distant resource does not seem to be on huggingface.co.
```

**Root cause:** The Python `huggingface_hub` library's SSL verification conflicts with the route through TUN. DNS resolves hf-mirror.com to TUN's virtual IP (198.18.0.x), but the SSL certificate check expects huggingface.co and fails.

**Fix:** Use direct HF through TUN OR use curl/wget to hf-mirror for individual files. Don't rely on `HF_ENDPOINT` when TUN is active.

## Also Covered In

- HF.md (full guide in ~/Downloads, 1162 lines) — covers mirrors, aria2c, gated models, Docker, Kubernetes
- hf-mirror.com documentation (Chinese) — https://hf-mirror.com
