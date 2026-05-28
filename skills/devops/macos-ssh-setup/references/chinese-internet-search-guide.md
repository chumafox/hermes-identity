# China Internet Search Guide for Hermes Agent

## When the Agent Is Behind the Chinese Firewall

DuckDuckGo, Google, Wikipedia, and raw GitHub are BLOCKED.
Use these alternatives in priority order.

## Priority Order

1. **Bing China** — most reliable in mainland China
2. **Baidu** — backup Chinese search engine
3. **Gitee API** — GitHub mirror
4. **ModelScope** — HuggingFace mirror for ML models
5. **GitHub API via token** — last resort (slow)

## No Xcode CLT? Use portable Python

If the machine has no Xcode Command Line Tools (common on headless Macs without internet), the system `python3` will fail with `xcode-select` errors. Use the portable Python shipped with the Hermes Agent bundle instead:

```bash
# Instead of:
curl ... | python3 -c "..."

# Use:
curl ... | /tmp/hermes_bundle/python/bin/python3 -c "..."
```

The portable Python at `/tmp/hermes_bundle/python/bin/python3` is a full CPython that needs no Xcode.

## Bing China (cn.bing.com)

```bash
# Search and extract results
curl -s -A "Mozilla/5.0" --max-time 15 \
  "https://cn.bing.com/search?q=QUERY&ensearch=1" \
  | sed 's/<[^>]*>//g' | grep -i "github\|description" | head -10
```

## Baidu (baidu.com)

```bash
curl -s -A "Mozilla/5.0" --max-time 15 \
  "https://www.baidu.com/s?wd=QUERY" \
  | grep -oP '(?<=<a[^>]*href=")[^"]*(?=")' | head -10
```

## Gitee API (Chinese GitHub mirror)

```bash
# Search repositories
curl -s --max-time 15 \
  "https://gitee.com/api/v5/search/repositories?q=QUERY&sort=stars" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin)[:5]:
    print(r.get('full_name', '?'))
"

# Clone via Gitee
git clone --depth 1 https://gitee.com/mirrors/REPO-NAME.git
```

## ModelScope (Chinese HuggingFace mirror)

```bash
curl -s --max-time 15 \
  "https://modelscope.cn/api/v1/models?query=QUERY" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for m in json.load(sys.stdin).get('models', [])[:5]:
    print(m.get('name', '?'))
"
```

## Wikipedia via Wikiless mirror

```bash
curl -s --max-time 15 \
  "https://wikiless.org/api/v1/search?q=QUERY&limit=3" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin):
    print(r.get('title', '?'))
"
```

## GitHub API (last resort — slow in China)

```bash
curl -s --max-time 30 \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/search/repositories?q=QUERY&sort=stars&per_page=3" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin).get('items', [])[:3]:
    print(r['full_name'], '-', r.get('description', '')[:80])
"
```

## Pip Mirrors for China

```bash
# Tsinghua (primary)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package

# AliYun (backup)
pip install -i https://mirrors.aliyun.com/pypi/simple package
```

## Rules for Unstable WiFi

- `--max-time 15` on every curl
- On error: wait 10s, retry twice more
- 3 failures → move to next source
- If NOTHING works → ask the screen Mac for help

## aria2c for Resumable Downloads

For large model files (GGUF, safetensors — 2-10 GB) over unstable connections, `aria2c` supports resume (`-c`), unlike `curl` or `wget`. This is critical when the connection drops mid-download:

```bash
# Install via brew (may fail in China — use pip from tsinghua mirror instead)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple aria2p
# Or get the binary directly
curl -L -o /tmp/aria2c https://github.com/aria2/aria2/releases/latest/download/aria2-1.37.0-macos-arm64.tar.gz

# Download with resume (+ 4 parallel connections)
aria2c -c -x 4 -s 4 "https://huggingface.co/USER/REPO/resolve/main/model.gguf"
```

Key flags: `-c` (continue/resume), `-x 4` (max connections per server), `-s 4` (split file into chunks).

## HuggingFace Direct Download Links

Get a direct download URL for any file in a HuggingFace repo:

```bash
curl -s "https://huggingface.co/api/models/USER/REPO" | python3 -c "
import json, sys
for f in json.load(sys.stdin).get('siblings', []):
    if f['rfilename'].endswith('.gguf'):
        print(f'https://huggingface.co/USER/REPO/resolve/main/{f[\"rfilename\"]}')
"
```

Use with `aria2c -c` for resumable downloads of large model files.
