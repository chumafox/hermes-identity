# Shadowrocket VPN Proxy in China — Tool Compatibility

Shadowrocket is a common VPN/proxy client on macOS in China. It installs as a network service and sets system-wide HTTP/HTTPS proxy on `127.0.0.1:1082`. This reference documents how each tool interacts with it.

## Detection

```bash
# Check if proxy is active
scutil --proxy | grep -E "HTTPEnable|HTTPProxy|HTTPPort"
# HTTPEnable : 1  → active (port 127.0.0.1:1082)
# HTTPEnable : 0  → Shadowrocket is OFF

# DNS is also proxied — resolves show 198.18.0.x (CGNAT range)
scutil --dns | grep "nameserver"
# Shows 198.18.0.2 (proxied DNS) alongside real DNS servers
```

## Tool Behavior Matrix

| Tool | Proxy active | Proxy inactive | Pattern |
|------|-------------|----------------|---------|
| **curl** | Works (auto-detects system proxy unless `--noproxy`) | Works direct | No special handling needed |
| **node https.get** | Works | Works | Respects system proxy settings |
| **npm** | ETIMEDOUT on registry (ironically) | ETIMEDOUT on registry | Needs explicit `npm config set proxy` + `https-proxy` |
| **npm (with proxy config)** | EIDLETIMEOUT on CDN tarballs | Works after metadata cached | Two-phase: proxy for metadata, then remove proxy for tarballs |
| **brew** | Works with `HTTP_PROXY`/`HTTPS_PROXY` env vars | Works direct (slower from China) | Set env vars for reliability |
| **pip** | Works with `--proxy` flag | May fail on pypi.org | Use `--proxy http://127.0.0.1:1082` or `HTTPS_PROXY` env |
| **aria2c** | Works with `--all-proxy` | Works direct | `--all-proxy=http://127.0.0.1:1082` if needed |
| **huggingface-hub (Python)** | Fails (SSL cert issues) | Works via hf-mirror redirect | Better to bypass proxy and use direct aria2c downloads |
| **xcode-select --install** | May fail | Works direct | Proxy breaks Apple CDN downloads |

## npm Two-Phase Workaround

When npm registry is unreachable from China and Shadowrocket proxy is active:

```bash
# Phase 1: Fetch metadata via proxy
npm config set proxy http://127.0.0.1:1082
npm config set https-proxy http://127.0.0.1:1082
npm config set registry https://registry.npmmirror.com
npm install     # This fetches all packument metadata through proxy

# Phase 2: Remove proxy for tarball downloads (IDLE TIMEOUT on CDN)
npm config delete proxy
npm config delete https-proxy
npm install     # This downloads cached tarballs directly from CDN
```

Alternative one-shot:
```bash
HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082 npm install
# If EIDLETIMEOUT on cdn.npmmirror.com, retry without proxy
npm install     # metadata is cached, tarballs download direct
```

## brew with Proxy

```bash
HTTP_PROXY=http://127.0.0.1:1082 HTTPS_PROXY=http://127.0.0.1:1082 brew install <formula>
```

Without proxy, brew may stall downloading Homebrew's portable Ruby from ghcr.io from China.

## Checking Proxy Health

```bash
# Test if proxy port is listening
curl -x http://127.0.0.1:1082 -sI --connect-timeout 5 https://google.com
# HTTP/1.1 200 Connection established → proxy is alive

# Test if proxy is system-enabled
scutil --proxy | grep HTTPEnable
# 1 → enabled, 0 → disabled
```

## Common Failure Modes

1. **npm EIDLETIMEOUT on cdn.npmmirror.com**: Proxy works for registry metadata but breaks CDN tarball downloads. Remove proxy after first successful metadata fetch.

2. **huggingface_hub LocalEntryNotFoundError**: The Python library's SSL handling conflicts with proxy-resolved DNS (198.18.0.x). Use aria2c directly instead:
   ```bash
   aria2c -c --check-certificate=false \
     "https://hf-mirror.com/org/repo/resolve/main/file.safetensors"
   ```

3. **brew fails to download portable-ruby**: Needs proxy env vars. Without them, ghcr.io is unreachable from China.

4. **xcode-select --install fails**: Proxy blocks Apple CDN. Disable Shadowrocket before installing CLT.

## Proactive Check Workflow

Before starting any download or installation, always check proxy status:
```bash
SCUTIL=$(scutil --proxy)
if echo "$SCUTIL" | grep -q "HTTPEnable : 1"; then
  echo "Proxy active on $(echo "$SCUTIL" | grep HTTPPort | awk '{print $3}')"
else
  echo "No system proxy"
fi
```
