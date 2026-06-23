# ALL_PROXY Trap & yt-dlp Through Proxy

## ALL_PROXY Environment Trap

macOS setups often export `ALL_PROXY=socks5://127.0.0.1:1080` in shell profile.
This **breaks pip** with:

```
ERROR: Could not install packages due to an OSError: Missing dependencies for SOCKS support.
```

### Fix — three options:

```bash
# Option A: unset ALL_PROXY for the command
env -u ALL_PROXY pip install <package>

# Option B: install pysocks once, then pip works with SOCKS
env -u ALL_PROXY pip install pysocks

# Option C: use --proxy flag explicitly
pip install --proxy socks5://127.0.0.1:1080 <package>
```

### Why

pip reads `ALL_PROXY`/`HTTPS_PROXY`/`HTTP_PROXY`. When `ALL_PROXY=socks5://...`
is set but `PySocks` is not installed, pip can't handle SOCKS5 and fails.

### Check current state

```bash
echo "ALL_PROXY=$ALL_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"
```

### NO_PROXY for localhost

`NO_PROXY="*"` must be set for localhost WebSocket/CDP connections
(Doubao bridge, Brave CDP) — otherwise they try to route through the proxy
and fail.

---

## yt-dlp Through Proxy

YouTube is blocked in China. Use yt-dlp with explicit proxy.

### Old versions fail

yt-dlp < 2026 gives:
- `Signature extraction failed` — YouTube broke the player signature
- `not available on this app` — stale client fingerprint

### Fix

```bash
# Update first
pip install --proxy socks5://127.0.0.1:1080 --upgrade yt-dlp

# Then download
yt-dlp --proxy socks5://127.0.0.1:1080 -f bestaudio --extract-audio \
  --audio-format mp3 -o "~/Downloads/%(title)s.%(ext)s" "URL"
```

### SSL errors on some videos

```
SSL: UNEXPECTED_EOF_WHILE_READING
```

Try:
- `--extractor-args "youtube:player_client=android"` — different client
- Some videos are region-locked or the proxy is unstable
- Accept the limitation: some work, some don't

### No JS runtime warning

```
No supported JavaScript runtime could be found. Only deno is enabled by default
```

YouTube extraction without a JS runtime is deprecated. Install deno:
```bash
brew install deno
```
Or ignore — most formats still work without it.
