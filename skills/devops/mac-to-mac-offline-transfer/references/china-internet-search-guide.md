# Search Strategies for Headless Macs Behind Chinese Firewall

## Context
When running a local LLM (LM Studio, Ollama) with no internet access or restricted Chinese internet, the model can't search the web natively. Use `terminal` tool with `curl` for HTTP-based search.

## Prerequisites
- `curl` available (built-in on macOS)
- For Python parsing: portable Python at `/tmp/hermes_bundle/python/bin/python3` (system python may need Xcode CLT)

## Search Priority Order
1. **Bing China** — most reliable in CN
2. **Baidu** — primary Chinese engine
3. **Gitee API** — GitHub mirror
4. **ModelScope API** — HuggingFace mirror
5. **Wikipedia via wikiless** — knowledge base
6. **GitHub API** — last resort, slow

## Commands

### Bing China
```bash
curl -s -A "Mozilla/5.0" --max-time 15 "https://cn.bing.com/search?q=QUERY&ensearch=1" | sed 's/<[^>]*>//g' | grep -i "match" | head -10
```

### Baidu
```bash
curl -s -A "Mozilla/5.0" --max-time 15 "https://www.baidu.com/s?wd=QUERY" | grep -oP '(?<=<a[^>]*href=")[^"]*' | head -10
```

### Gitee (GitHub mirror)
```bash
curl -s --max-time 15 "https://gitee.com/api/v5/search/repositories?q=QUERY&sort=stars" | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin)[:5]:
    print(r.get('full_name', '?'))
"
```

### ModelScope (HF mirror)
```bash
curl -s --max-time 15 "https://modelscope.cn/api/v1/models?query=QUERY" | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for m in json.load(sys.stdin).get('models', [])[:5]:
    print(m.get('name', '?'))
"
```

### Wikipedia mirror
```bash
curl -s --max-time 15 "https://wikiless.org/api/v1/search?q=QUERY&limit=3" | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin):
    print(r.get('title', '?'))
"
```

### GitHub API (slow, 60 req/hr limit)
```bash
curl -s --max-time 30 "https://api.github.com/search/repositories?q=QUERY&sort=stars&per_page=3" | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin).get('items', [])[:3]:
    print(r['full_name'])
"
```

## Key Rules for Local LLM Search
- Use portable Python (`/tmp/hermes_bundle/python/bin/python3`) — system python may trigger Xcode CLT errors
- Always `--max-time 15` — never wait longer for a single request
- Errors → pause 10s → retry up to 3x
- 3 failures → switch to next source
- If ALL sources fail → tell user to search from the Mac with good internet

## Pip Mirrors (for offline Python package installs)
```bash
# Tsinghua (primary)
/tmp/hermes_bundle/python/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>

# AliYun (backup)
/tmp/hermes_bundle/python/bin/pip install -i https://mirrors.aliyun.com/pypi/simple <package>
```

## No Xcode CLT? Use Portable Python
System `python3` on macOS requires Xcode Command Line Tools. If not installed:
- `/tmp/hermes_bundle/python/bin/python3` — portable from uv, works without Xcode
- Or transferred CLT: `xcode-select -s /Library/Developer/CommandLineTools` after offline transfer
