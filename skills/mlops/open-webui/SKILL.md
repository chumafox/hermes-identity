---
name: open-webui
category: mlops
description: Deploy and run Open WebUI from source on macOS — Python backend, Svelte frontend, China-network workarounds, and provider configuration.
trigger: User asks to set up, install, configure, or run Open WebUI; or mentions OWUI, openwebui, or a "web interface for local LLMs".
tags: [open-webui, web-ui, llm-frontend, svelte, fastapi, deployment]
---

# Open WebUI on macOS

Deploy [Open WebUI](https://github.com/open-webui/open-webui) from source on macOS, with China-network workarounds and Ollama/LM Studio integration.

## 1. Clone (China-safe)

Use shallow clone — full history is 1GB+:

```bash
cd ~
git clone --depth 1 --single-branch https://github.com/open-webui/open-webui.git
```

If GitHub is slow/blocked, use a mirror or proxy:
```bash
git -c http.proxy=socks5://127.0.0.1:1082 clone --depth 1 https://github.com/open-webui/open-webui.git
```

## 2. Python Backend

### 2.1 Create venv + install deps

```bash
cd ~/open-webui
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r backend/requirements.txt
```

### 2.2 Install the package itself

Symlink instead of `uv pip install -e .` (avoids hatchling build hang):

```bash
cd ~/open-webui/.venv/lib/python3.12/site-packages/
ln -sf /Users/admin/open-webui/backend/open_webui .
```

Verify: `python -c "import open_webui; print(open_webui.__file__)"` should print the symlinked path.

## 3. Frontend Build

### 3.1 Install Node deps (China-safe)

npm from China hangs on postinstall scripts (cypress, onnxruntime-node). Use npmmirror + `--ignore-scripts`:

```bash
cd ~/open-webui
npm install --ignore-scripts --registry=https://registry.npmmirror.com
```

### 3.2 Run essential postinstall scripts

Only esbuild is needed for vite to work:

```bash
node node_modules/esbuild/install.js
node node_modules/vite/node_modules/esbuild/install.js
```

### 3.3 Build

```bash
./node_modules/.bin/vite build
```

Output: `~/open-webui/build/` (~223MB).

## 4. Run Server

### 4.1 Minimal start (no auth, offline mode to skip HF downloads)

Create `~/open-webui/.env` for persistent config:
```
OFFLINE_MODE=true
WEBUI_SECRET_KEY=some-key
WEBUI_AUTH=false
RAG_EMBEDDING_MODEL_AUTO_UPDATE=false
RAG_RERANKING_MODEL_AUTO_UPDATE=false
WHISPER_MODEL_AUTO_UPDATE=false
REQUESTS_CA_BUNDLE=""
CURL_CA_BUNDLE=""
HF_ENDPOINT=https://hf-mirror.com
```

env.py auto-loads `.env` from the project root via `load_dotenv(find_dotenv(str(BASE_DIR / '.env')))`.

Then start:
```bash
cd ~/open-webui
source .venv/bin/activate
python -u -m uvicorn open_webui.main:app \
    --host 0.0.0.0 --port 8080
```

Background: use `terminal(background=true)`.

### 4.2 Verify

```bash
curl -s http://localhost:8080/health       # → 200
curl -s http://localhost:8080 | head -5    # → HTML
```

## 5. Provider Integration

### Ollama

```bash
ollama serve
```

OWUI auto-discovers Ollama at `http://localhost:11434`.

### LM Studio / OpenAI-compatible API

Set env var at start:
```bash
OPENAI_API_BASE_URL=http://localhost:1234/v1
```

Or configure in the Web UI: Settings → Connections → OpenAI API.

## Pitfalls

### HF model download blocks startup
OWUI downloads `sentence-transformers/all-MiniLM-L6-v2` on first start. From China this hangs for minutes.

**Fix:** Start with `OFFLINE_MODE=true`. RAG won't work until the model is cached, but the web UI starts immediately.

To cache the model later:
```bash
aria2c -c --check-certificate=false \
  "https://hf-mirror.com/sentence-transformers/all-MiniLM-L6-v2/resolve/main/model.safetensors" \
  -d ~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/<hash>/
```

Or download via proxy: `ALL_PROXY=socks5://127.0.0.1:1082 python -c "from huggingface_hub import snapshot_download; snapshot_download('sentence-transformers/all-MiniLM-L6-v2')"`

### SSL certificate errors on this Mac
The HF client (`requests`/`urllib3`) fails with SSL verification on this Mac. Workarounds:
- Use `aria2c --check-certificate=false` for manual downloads
- Or set `REQUESTS_CA_BUNDLE="" CURL_CA_BUNDLE=""`
- Or use `OFELINE_MODE=true` to skip all HF network calls

### npm postinstall scripts hang
cypress (13MB binary download) and onnxruntime-node hang from China. Always use `--ignore-scripts` and manually run only esbuild postinstall.

### The .venv doesn't find open_webui package
The package is at `backend/open_webui/`. If `uv pip install -e .` doesn't work (hangs on hatchling build), use the symlink approach above.

## Verification Checklist

- [ ] `curl localhost:8080/health` returns 200
- [ ] Browser shows OWUI login/signup page
- [ ] Ollama models visible in model selector (if ollama serve is running)
- [ ] Chat completes without errors

## See Also

- `huggingface-hub` skill — HF model download workflows
- `reliable-large-file-downloader` skill — China-network download strategies
- `llama-cpp` skill — local GGUF inference backend
