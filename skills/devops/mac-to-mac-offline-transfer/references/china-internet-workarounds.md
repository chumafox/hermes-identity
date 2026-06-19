# Chinese Internet Workarounds

## Network conditions
- Google, DuckDuckGo, Wikipedia — BLOCKED
- GitHub — slow, may timeout
- HuggingFace — blocked or very slow
- PyPI — slow, use mirrors
- Apple services (Xcode CLT download) — may be slow or fail

## Search engines (in priority order)

### 1. Bing China (most reliable)
```bash
curl -s -A "Mozilla/5.0" --max-time 15 "https://cn.bing.com/search?q=QUERY&ensearch=1"
```

### 2. Baidu
```bash
curl -s -A "Mozilla/5.0" --max-time 15 "https://www.baidu.com/s?wd=QUERY"
```

## Code / Repos

### Gitee (GitHub mirror)
```bash
curl -s --max-time 15 "https://gitee.com/api/v5/search/repositories?q=QUERY&sort=stars"
git clone --depth 1 https://gitee.com/mirrors/REPO.git
```

### GitHub API (slow, 60 req/hr without token)
```bash
curl -s --max-time 30 "https://api.github.com/search/repositories?q=QUERY&sort=stars"
```

## ML Models

### ModelScope (HuggingFace mirror)
```bash
# API search
curl -s --max-time 15 "https://modelscope.cn/api/v1/models?query=QUERY"

# Download
python3 -c "from modelscope import snapshot_download; snapshot_download('REPO')"
```

## Python packages (pip mirrors)

```bash
# Tsinghua (primary)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PACKAGE

# AliYun (backup)
pip install -i https://mirrors.aliyun.com/pypi/simple PACKAGE

# uv with mirror
uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple PACKAGE
```

## Xcode CLT — offline install
Xcode Command Line Tools download often fails in China. Transfer from source Mac:
```bash
# On source Mac:
sudo tar czf /tmp/CLT_macOS14.tar.gz -C /Library/Developer CommandLineTools
scp /tmp/CLT_macOS14.tar.gz target:/tmp/

# On target Mac:
sudo tar xzf /tmp/CLT_macOS14.tar.gz -C /Library/Developer
sudo xcode-select -s /Library/Developer/CommandLineTools
```

Alternative: use portable Python (from uv) instead of system python3:
```bash
# Portable Python doesn't need Xcode CLT
/tmp/hermes_bundle/python/bin/python3 -c "..."
```

## Wikipedia

```bash
# Wikiless mirror
curl -s --max-time 15 "https://wikiless.org/api/v1/search?q=QUERY&limit=3"
```

## Ollama import from local GGUF

When a model is downloaded via LM Studio (or any other tool) as a GGUF file and you want it available in Ollama too — no need to re-download or copy:

```bash
# 1. Create a Modelfile with absolute path to the existing GGUF
cd ~/.lmstudio/models/NidAll/supergemma4-e4b-abliterated-Q4_K_M-GGUF
echo "FROM $(pwd)/supergemma4-e4b-abliterated-q4_k_m.gguf" > /tmp/Modelfile

# 2. Import into Ollama (uses the file in-place, no copy)
ollama create supergemma4 -f /tmp/Modelfile

# 3. Verify
ollama ls | grep supergemma4
ollama run supergemma4
```

**Critical:** Use the ABSOLUTE path in the Modelfile's `FROM` line — relative paths may be interpreted as model names in the Ollama registry. If you see `Error: pull model manifest: Get "https://registry.ollama.ai/..."`, the path was resolved as a remote reference instead of a local file.

**No file duplication:** Ollama creates a manifest + digest layer, but the GGUF blob gets a hardlink or reflink (copy-on-write on APFS), not a full copy.

## Retry strategy for unstable WiFi

```bash
for i in 1 2 3; do
    curl --max-time 15 <url> && break
    echo "Failed attempt $i, waiting 10s..."
    sleep 10
done
```

If 3 failures — switch to next source or request files from source Mac via Type-C.

## iPhone USB tethering

iPhone can provide internet via USB cable — useful when WiFi is unstable but cellular works.

### Enable and set as primary

```bash
# List services
networksetup -listnetworkserviceorder

# Move iPhone USB to priority 1
sudo networksetup -ordernetworkservices "iPhone USB" "Wi-Fi" "Thunderbolt Bridge"

# Verify
route -n get default | grep interface   # should show en7 (iPhone)
```

**Warning:** After switching priority, WiFi interface may disconnect. SSH sessions
through WiFi IP will drop. Keep Type-C cable as backup connection or reconnect
via new interface IP.

### iPhone USB subnet

iPhone tethering uses `172.20.10.0/28` subnet. The Mac gets `172.20.10.4`.
When other interfaces disconnect, SSH via mDNS hostname (`admin-admin.local`)
may still work over the Type-C link-local address.
