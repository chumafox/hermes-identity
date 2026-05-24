# MLX Model Download in China (for Electron/MLX Apps)

When an Electron app (e.g., Gemma Chat) uses MLX-LM (`mlx_lm.server`) to serve models, the server downloads the model from HuggingFace during startup. From China, this fails or is extremely slow because `huggingface.co` is unreachable.

## Failure Signature

- MLX server starts on port 11434
- Small config files download (tokenizer, config.json, chat_template)
- The `.safetensors` weight file starts downloading but stalls — leaves a `.incomplete` file in the HF cache
- The app shows "Downloading model files…" but makes no progress

## Diagnosis

```bash
# Check MLX process
ps aux | grep mlx_lm.server

# Check HF cache for the model
ls -la ~/Library/Application\ Support/<app>/mlx/models/hub/models--mlx-community--<model-name>/
ls -la ~/Library/Application\ Support/<app>/mlx/models/hub/models--mlx-community--<model-name>/blobs/
# Look for .incomplete files — these indicate stalled partial downloads

# Check stderr of the MLX Python process
# The server logs to stdout/stderr of the process
```

## Fix: Download Via HF-Mirror, Then Restart

### Find the model cache path

For MLX apps, `HF_HOME` is often set to a custom path. Check:

```bash
# Common locations (check the app's source or process env):
# ~/.cache/huggingface/hub/  (default)
# ~/Library/Application Support/<app>/mlx/models/hub/  (custom — e.g. Gemma Chat)
ls -d ~/Library/Application\\ Support/*/mlx/models/hub 2>/dev/null
```

### Stop the MLX server

```bash
kill $(pgrep -f "mlx_lm.server") 2>/dev/null
# Verify
ps aux | grep mlx_lm.server | grep -v grep || echo "Server stopped"
```

### Plan A: Delete partial download and re-download via HF-Mirror (huggingface_hub)

```bash
# Find the model directory
MODEL_CACHE=~/Library/Application\\ Support/gemma-chat/mlx/models
# or: find ~/Library/Application\\ Support -path "*/mlx/models/hub" -type d

# Delete partial download
rm -rf "$MODEL_CACHE/hub/models--mlx-community--<model-name>/"

# Download with HF-Mirror
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME="$MODEL_CACHE"
export HF_HUB_DISABLE_TELEMETRY=1

python3 -c "
import ssl
# macOS cert issue: disable SSL verification before importing huggingface_hub
ssl._create_default_https_context = ssl._create_unverified_context
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id='mlx-community/<model-name>',
    resume_download=True,
    local_files_only=False,
    ignore_patterns=['*.md', '*.txt']
)
print(f'Done: {path}')
"
```

This uses the Python `huggingface_hub` library (which should be installed in the MLX venv or system Python). If the app has its own venv, use that Python (note: SSL fix is needed for both system and venv Python on this Mac):

```bash
~/Library/Application\\ Support/<app>/mlx/venv/bin/python3 -c "
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
from huggingface_hub import snapshot_download; ...
"
```

**⚠ Plan A may fail** — `huggingface_hub.snapshot_download` with `HF_ENDPOINT=https://hf-mirror.com` can throw `LocalEntryNotFoundError` even with SSL bypass. The HEAD requests through huggingface_hub's internal HTTP client may not reach the mirror. If Plan A fails, fall back to Plan B.

### Plan B: aria2c direct download + manual HF cache construction

When huggingface_hub fails, download files directly via aria2c and build the HF cache structure manually.

#### Step 1: Get the file list

```bash
# List model files (siblings) via HuggingFace API
curl -s -k "https://huggingface.co/api/models/mlx-community/<model-name>" | \
  python3 -c "
import json,sys
data = json.load(sys.stdin)
for f in data.get('siblings', []):
    rfn = f.get('rfilename','')
    size = f.get('size',0)
    if not rfn.endswith(('.md','.txt','.gitattributes')):
        print(f'{size}\t{rfn}')
" 2>&1 | sort -rn
```

#### Step 2: Download all files with aria2c to a temp directory

```bash
mkdir -p /tmp/<model-temp>
cd /tmp/<model-temp>

# Small config files — download sequentially (fast, each <30MB)
for f in config.json tokenizer.json tokenizer_config.json generation_config.json \
         model.safetensors.index.json processor_config.json chat_template.jinja; do
  aria2c -c --check-certificate=false --max-tries=3 --retry-wait=5 \
    --dir=/tmp/<model-temp> --out="$f" \
    "https://hf-mirror.com/mlx-community/<model-name>/resolve/main/$f"
done

# Big weight file — download in background with multi-connection
# hf-mirror redirects to huggingface.co CDN (Xet Hub / cas-bridge), which delivers ~30MB/s
aria2c -c --check-certificate=false --file-allocation=none \
  --max-connection-per-server=4 --split=4 \
  --max-tries=10 --retry-wait=15 \
  --dir=/tmp/<model-temp> --out=model.safetensors \
  "https://hf-mirror.com/mlx-community/<model-name>/resolve/main/model.safetensors"
```

#### Step 3: Build the HF cache structure

The HF cache is content-addressed: blobs are named by their SHA256 hash, and symlinks in `snapshots/<commit>/` point to them.

```bash
cd /tmp/<model-temp>

# Compute SHA256 for model.safetensors
WEIGHTS_HASH=$(shasum -a 256 model.safetensors | cut -d' ' -f1)
echo "weights hash: $WEIGHTS_HASH"

# Determine commit hash (from etags in aria2c output or HF API)
# Common commit hashes for mlx-community models:
# gemma-4-e2b-it-4bit: 2c3e507453b4f218d05fe3cc97bea5c5a654257e
COMMIT_HASH="<commit-hash-from-api-or-log>"

# Create cache directories
MODEL_CACHE="$HOME/Library/Application Support/gemma-chat/mlx/models/hub/models--mlx-community--<model-name>"
BLOB_DIR="$MODEL_CACHE/blobs"
SNAP_DIR="$MODEL_CACHE/snapshots/$COMMIT_HASH"
mkdir -p "$BLOB_DIR" "$SNAP_DIR" "$MODEL_CACHE/refs"

# Write refs/main
echo "$COMMIT_HASH" > "$MODEL_CACHE/refs/main"

# File -> SHA256 mappings (extract etag from aria2c logs for each file)
# config.json etag is typically the SHA256 of the file
declare -A FILE_HASHES
FILE_HASHES[config.json]=e4f9de994fcdf7a8c104e4f5aafa0d137474837c
FILE_HASHES[chat_template.jinja]=c19999a347da729cf62806a8ddb7eb8e315223b5
FILE_HASHES[generation_config.json]=e605bb4523b1462ea9d9a3810b9e3ecf7ab7b1f6
FILE_HASHES[model.safetensors.index.json]=cbba8cce606b3549efd993cdc055372bcc9cb42d
FILE_HASHES[processor_config.json]=13e92a44d19566f334d7450e7898935e16e16f3d
FILE_HASHES[tokenizer_config.json]=375b25dc8be85705251e41be1c25310d24932051
FILE_HASHES[tokenizer.json]=cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f
FILE_HASHES[model.safetensors]=$WEIGHTS_HASH

# Copy files to blobs/ and symlink in snapshots/
for fname in "${!FILE_HASHES[@]}"; do
  fhash="${FILE_HASHES[$fname]}"
  cp "$fname" "$BLOB_DIR/$fhash"
  ln -sf "../../blobs/$fhash" "$SNAP_DIR/$fname"
done

# Verify
ls -la "$SNAP_DIR/"
echo "Total cache size: $(du -sh "$MODEL_CACHE" | cut -f1)"
```

**Getting the commit hash:** The commit hash can be found from the HF API or from the redirect URL in aria2c logs:
```
Redirecting to https://huggingface.co/api/resolve-cache/models/.../<COMMIT_HASH>/config.json
```
Or list available snapshots after partial download. Common mlx-community commit hashes are stable per model version.

#### Step 4: Alternative — use Python to build cache programmatically

```bash
cd /tmp/<model-temp> && python3 -c "
import hashlib, os, shutil

# Get SHA256 of each file (or use known etags from aria2c output)
# Build the cache structure
commit_hash = '<commit>'
model_cache = os.path.expanduser('~/Library/Application Support/gemma-chat/mlx/models/hub/models--mlx-community--<model-name>')
blob_dir = os.path.join(model_cache, 'blobs')
snap_dir = os.path.join(model_cache, 'snapshots', commit_hash)
os.makedirs(blob_dir, exist_ok=True)
os.makedirs(snap_dir, exist_ok=True)
os.makedirs(os.path.join(model_cache, 'refs'), exist_ok=True)

with open(os.path.join(model_cache, 'refs', 'main'), 'w') as f:
    f.write(commit_hash + '\n')

# File -> SHA256 (from hf etags or computed)
files = {
    'config.json':                'e4f9de994fcdf7a8c104e4f5aafa0d137474837c',
    'tokenizer.json':             'cc8d3a0ce36466ccc1278bf987df5f71db1719b9ca6b4118264f45cb627bfe0f',
    'model.safetensors':          hashlib.sha256(open('model.safetensors','rb').read()).hexdigest(),
    # ... add all other files
}
for fname, fhash in files.items():
    shutil.copy2(fname, os.path.join(blob_dir, fhash))
    if os.path.exists(os.path.join(snap_dir, fname)):
        os.remove(os.path.join(snap_dir, fname))
    os.symlink(f'../../blobs/{fhash}', os.path.join(snap_dir, fname))

print(f'Done. Cache: {model_cache}')
print(f'Size: {sum(os.path.getsize(os.path.join(blob_dir,f)) for f in os.listdir(blob_dir)) / 1024**3:.1f} GB')
"
```

### Port conflict between manual MLX server and Electron app

If you started the MLX server manually (e.g., during testing or download verification), the Electron app will fail to start its own MLX server when it tries to run `mlx_lm.server --model ... --port 11434` because port 11434 is already occupied:

```bash
# Check if a manual MLX server is running
lsof -i :11434
# If found, kill it before restarting the app
kill <PID>
# Verify port is free
lsof -i :11434 || echo "Port free"
```

**Symptom:** The app's Setup screen shows "Downloading model files…" or "Starting model runtime…" at 100% but never transitions to the Chat screen. No visible error in the app UI. The Electron app's `mlx.ts` calls `startServer()` which spawns a new Python process — it fails silently because the port is already bound.

**Fix:** Kill the manual MLX server, then close and reopen the Electron app. The app will spawn its own MLX server and find the cached model.

### Restart the MLX / Electron app

After the download completes by either plan, restart the app. The MLX server will find the cached model and start immediately without downloading.

## MLX Model Repos

Models for MLX have prefixes like `mlx-community/` or `mlx/` and contain MLX-optimized `.safetensors` files (not the original PyTorch weights). Common models:

| Repo | Size (actual) | Note |
|------|--------------|------|
| `mlx-community/gemma-4-e2b-it-4bit` | ~3.3 GB | Labeled "1.5 GB" in some apps (Gemma Chat UI), actual MLX weights |
| `mlx-community/gemma-4-e4b-it-4bit` | ~5.3 GB | Recommended all-rounder |
| `mlx-community/gemma-4-26b-a4b-it-4bit` | ~16 GB | Mixture-of-Experts |
| `mlx-community/gemma-4-31b-it-4bit` | ~18 GB | Best quality |

**Actual size may differ from app UI labels.** Always check the .safetensors file size on disk.

## Key details from real-world session (May 2026)

- hf-mirror.com URLs redirect to huggingface.co's **Xet Hub CDN** (cas-bridge.xethub.hf.co), not a Chinese CDN. Downloads still reach ~30MB/s from China.
- HuggingFace cache directory for Gemma Chat: `~/Library/Application Support/gemma-chat/mlx/models/hub/`
- MLX venv Python: `~/Library/Application Support/gemma-chat/mlx/venv/bin/python3`
- MLX server command: `python -m mlx_lm.server --model <hf-repo-id> --port 11434`
- Server listens on `127.0.0.1:11434`, uses OpenAI-compatible API (`/v1/chat/completions` with SSE streaming)

## HF Cache Structure

```
models--mlx-community--<model>/
├── blobs/           # Content-addressed files (named by SHA256)
│   ├── <sha256>                     # Small metadata files (few KB each)
│   └── <sha256>.incomplete          # Partial download (stalled)
├── refs/
│   └── main                         # Pointer to current commit
├── snapshots/
│   └── <commit_hash>/               # Symlinks to blobs/
│       ├── config.json -> ../../blobs/<sha256>
│       ├── model.safetensors -> ../../blobs/<sha256>
│       └── ...
└── .locks/
```

The `.incomplete` extension signals a partial download — `huggingface_hub` will resume from it on the next attempt. But from China, the resume to `huggingface.co` will also stall. Better to delete the entire model dir and re-download via `HF_ENDPOINT=https://hf-mirror.com`.
