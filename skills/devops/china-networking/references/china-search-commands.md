# China Search Commands

Ready-to-use search commands for Chinese internet environment.
All work without Xcode CLT (use portable Python path).

## Bing China (most reliable in CN)

```bash
curl -s -A "Mozilla/5.0" --max-time 15 \
  "https://cn.bing.com/search?q=ACE-Step+music+generation&ensearch=1" \
  | sed 's/<[^>]*>//g' | grep -i "ace-step\|github" | head -10
```

## Baidu

```bash
curl -s -A "Mozilla/5.0" --max-time 15 \
  "https://www.baidu.com/s?wd=OpenVox+open+source" \
  | grep -oP '(?<=<a[^>]*href=")[^"]*(?=")' | head -10
```

## Gitee API

```bash
curl -s --max-time 15 \
  "https://gitee.com/api/v5/search/repositories?q=openvox&sort=stars" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin)[:5]:
    print(r.get('full_name', '?'), '—', r.get('description', '')[:80])
"
git clone --depth 1 https://gitee.com/mirrors/ACE-Step-1.5.git
```

## ModelScope API

```bash
curl -s --max-time 15 \
  "https://modelscope.cn/api/v1/models?query=ACE-Step" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for m in json.load(sys.stdin).get('models', [])[:5]:
    print(m.get('name', '?'))
"
```

## GitHub API (last resort)

```bash
curl -s --max-time 30 \
  "https://api.github.com/search/repositories?q=openvox&sort=stars&per_page=3" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
for r in json.load(sys.stdin).get('items', [])[:3]:
    print(r['full_name'], '-', r.get('description', '')[:80])
"
```

## Pip Mirrors

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>
pip install -i https://mirrors.aliyun.com/pypi/simple <package>
```

## HF Model Direct Link

```bash
# Find GGUF URL
curl -s "https://huggingface.co/api/models/USER/REPO" \
  | /tmp/hermes_bundle/python/bin/python3 -c "
import json, sys
d = json.load(sys.stdin)
for f in d.get('siblings', []):
    if f['rfilename'].endswith('.gguf'):
        print('URL:', f'https://huggingface.co/{d[\"id\"]}/resolve/main/{f[\"rfilename\"]}')
        break
"
# Download with resume
aria2c -c -x 4 -s 4 --timeout=30 --retry-wait=10 --max-tries=0 \
  --dir=/tmp "URL"
```
