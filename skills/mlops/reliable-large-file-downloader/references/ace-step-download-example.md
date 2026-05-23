# ACE-Step Model Download — Session Notes

## Context
- Machine: M1 Pro Mac (21.3GB unified), headless, China network (iPhone tethering en7)
- Project: ACE-Step-1.5 (AI music generation)
- Repo: https://github.com/ace-step/ACE-Step-1.5 cloned to /tmp/ace-step
- Models needed from `ACE-Step/Ace-Step1.5`:
  - acestep-v15-turbo/model.safetensors (~2.3GB expected, HF-Mirror version 4.4GB)
  - acestep-5Hz-lm-1.7B/model.safetensors (~2.6GB expected, HF-Mirror version 4.4GB)
  - vae/diffusion_pytorch_model.safetensors (322MB)
  - Qwen3-Embedding-0.6B/model.safetensors (1.1GB)

## Speed Test Results (May 12, 2026, iPhone tethering)
| Source | Single-stream | 4-stream (aria2c) |
|--------|--------------|-------------------|
| HF-Mirror (hf-mirror.com) | 900 KB/s | 3-4 MB/s |
| ModelScope | ~200 KB/s | ~600 KB/s |
| HuggingFace direct | blocked | blocked |

=> Always prefer HF-Mirror URLs directly for large downloads in China.

## Download Commands Used

### 1. Small files via curl
```bash
cd /tmp/ace-step/checkpoints/acestep-v15-turbo/
curl -sLO "https://hf-mirror.com/Ace-Step/Ace-Step1.5/resolve/main/acestep-v15-turbo/config.json"
```

### 2. Large safetensors via aria2c (resumable)
```bash
aria2c -c -x 4 -s 4 --check-certificate=false \
  --dir=/tmp/ace-step/checkpoints/acestep-v15-turbo \
  --out=model.safetensors \
  "https://hf-mirror.com/Ace-Step/Ace-Step1.5/resolve/main/acestep-v15-turbo/model.safetensors"
```

### 3. Integrity check after download
```bash
python3 -c "
import safetensors
for f in ['checkpoints/acestep-v15-turbo/model.safetensors', 'checkpoints/acestep-5Hz-lm-1.7B/model.safetensors']:
    t = safetensors.safe_open(f, framework='pt')
    print(f'OK: {f} ({len(t.keys())} keys)')
"
```
Valid check: `safetensors.safe_open(path, framework='pt')` — both ACE-Step models had 677 keys when valid.

### 4. ACE-Step model_downloader quirks
- `--prefer-source` is NOT a valid CLI flag — use env var `ACESTEP_DOWNLOAD_SOURCE=modelscope`
- `--force` works for re-download but uses `snapshot_download` (entire repo, slow)
- Better: download individual `.safetensors` files via aria2c from HF-Mirror
- `_contains_model_weights()` only checks file existence, not integrity
- Model code sync happens at startup (auto-copies .py files from acestep/models/ to checkpoints)

### 5. HF-Mirror direct URLs
Pattern: `https://hf-mirror.com/{org}/{repo}/resolve/main/{path}`

## Whisper Model Download (mlx-whisper large-v3-turbo, 1.5 GB)

```bash
aria2c -c -x 4 -s 4 --check-certificate=false --file-allocation=none \
  --out=weights.safetensors \
  "https://hf-mirror.com/mlx-community/whisper-large-v3-turbo/resolve/main/weights.safetensors"
```

**Key details:**
- `--file-allocation=none` → shows real download progress immediately (not pre-allocated size)
- `--check-certificate=false` → needed on macOS with old LibreSSL 2.8.3
- After download, copy to HF cache manually (see main SKILL.md section "Manual HF Cache Population")
- Speed on China network: ~2-5 MB/s from hf-mirror.com

**Also download metadata files (small):**
```bash
for f in config.json README.md .gitattributes; do
  curl -sLo "$f" "https://hf-mirror.com/mlx-community/whisper-large-v3-turbo/resolve/main/$f"
done
```
