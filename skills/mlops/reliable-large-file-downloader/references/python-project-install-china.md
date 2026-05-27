# Python Project Installation from Source — China Network

Example: Open WebUI (open-webui/open-webui v0.9.5)

## The Challenge

A modern Python project pulls in 200+ dependencies including very large packages:
- torch (~83MB)
- opencv-python-headless (~44MB)
- pyarrow (~29MB)
- onnxruntime (~16MB)
- transformers (~10MB)
- chromadb (~19MB)

Running `uv pip install -e .` from China often times out after 3-5 minutes, having downloaded only ~50 of 260 packages. Retrying from scratch loses partial progress.

## Network Setup

- **Location:** China (mainland)
- **GitHub:** Requires `--depth 1` (full history >1GB times out)
- **npm:** Use `--registry=https://registry.npmmirror.com`
- **Python:** Use `UV_INDEX_URL` or mirror via env
- **HuggingFace:** Use `HF_ENDPOINT=https://hf-mirror.com` for `snapshot_download()`
- **Local proxy:** Shadowrocket at 127.0.0.1:1082 (socks5 — npm/pip ignore it unless HTTP proxy is set)

## Step-by-Step: Open WebUI

### 1. Clone (shallow)

```bash
git clone --depth 1 --single-branch https://github.com/open-webui/open-webui.git
```

Full clone times out (repo ~1GB+). Shallow clone gives latest commit only.

### 2. Python venv + deps

```bash
cd open-webui
uv venv --python 3.12
source .venv/bin/activate

# Install dependencies from requirements.txt (smaller downloads per call)
UV_HTTP_TIMEOUT=300 uv pip install -r backend/requirements.txt
```

This may take 3-8 minutes depending on network. If it times out, retry — `uv` caches completed packages.

### 3. Install the package itself

```bash
# Avoid re-downloading all deps
uv pip install -e . --no-deps
```

If `--no-deps` fails (e.g., hatchling build hangs in China):

```bash
# Symlink instead of pip install
cd .venv/lib/python3.12/site-packages/
ln -sf /Users/admin/open-webui/backend/open_webui open_webui

# Verify
python -c "import open_webui; print(open_webui.__file__)"
```

### 4. Frontend build

```bash
# npm from China
npm install --registry=https://registry.npmmirror.com

# Build (skip pyodide:fetch if it hangs — it downloads Python runtime for browser)
npx vite build
```

If `npm install` hangs:

```bash
# Clean and retry with mirror only (no proxy)
rm -rf node_modules package-lock.json
npm cache clean --force
npm config set registry https://registry.npmmirror.com
npm config set fetch-retries 5
npm install
```

**Check for Shadowrocket/Clash proxy interference first:**
```bash
scutil --proxy | grep -E "HTTP(S)?(Proxy|Port)"
```
If proxy is active but npmmirror direct fails, use two-phase proxy warmup (see `package-managers-china.md`).

### 5. Run server

```bash
# Set HF endpoint for embedding model downloads
export HF_ENDPOINT=https://hf-mirror.com

# Generate a secret key
echo "test-key-$(head -c 12 /dev/random | base64)" > backend/.webui_secret_key

# Start
cd backend
source ../.venv/bin/activate
WEBUI_SECRET_KEY="$(cat .webui_secret_key)" python -m uvicorn open_webui.main:app \
  --host 0.0.0.0 --port 8080 --log-level info
```

### 6. Verify

```bash
curl -s http://localhost:8080/health
# Should return HTTP 200
# Browser: http://<mac-ip>:8080
```

## Known Issues

### HuggingFace model download blocks startup

On first start, Open WebUI downloads sentence-transformers/all-MiniLM-L6-v2 for embeddings. From China with `HF_ENDPOINT=https://hf-mirror.com`:

- `Fetching 30 files` may succeed partially (6/30) then fail with `LocalEntryNotFoundError`
- Error message: `Cannot determine model snapshot path`
- The app still starts but embeddings/RAG doesn't work

**Quick fix — start immediately without model:** Set `OFFLINE_MODE=true` — the web UI starts without the embedding model (RAG won't work, but chat does). Download the model later:

```bash
OFFLINE_MODE=true python -m uvicorn open_webui.main:app --host 0.0.0.0 --port 8080
```

**Workaround — pre-download for full RAG support:** Download with aria2c:
```bash
aria2c -c -x 4 -s 4 --check-certificate=false \
  --dir=~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/blobs/ \
  "https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.safetensors"
```
Then run `snapshot_download` with `local_files_only=True`:
```python
from huggingface_hub import snapshot_download
snapshot_download("sentence-transformers/all-MiniLM-L6-v2", local_files_only=True)
```

### "Frontend build directory not found"

Error: `Frontend build directory not found at '/Users/admin/open-webui/build'. Serving API only.`

**Fix:** Either:
1. Build frontend: `cd ~/open-webui && npx vite build` (produces `build/`)
2. Or set `FRONTEND_BUILD_DIR` to point to the static dir:
```bash
export FRONTEND_BUILD_DIR=/Users/admin/open-webui/backend/open_webui/static
```
(Note: static/ may only have PDF/fonts, not the full Svelte UI — building is required)

### RAG embedding model missing

If `all-MiniLM-L6-v2` can't be downloaded, RAG features silently fail. Alternative: use Ollama embeddings if Ollama is running:
```bash
OLLAMA_BASE_URL=http://localhost:11434
```
Configure in Open WebUI settings → Models → Embedding Model → Ollama.

## Verdict

Open WebUI without Docker is feasible in China but requires:
- Shallow git clone
- Split Python install (requirements.txt first, then --no-deps)
- npmmirror for npm
- HF-Mirror for model downloads
- Patience with initial download time (~15 min total)
