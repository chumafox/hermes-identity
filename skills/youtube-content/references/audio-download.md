# Audio Download via yt-dlp

Download audio from YouTube videos when transcripts aren't enough.

## Workflow

```bash
# Update yt-dlp first (old versions break — YouTube changes signatures)
pip install --proxy socks5://127.0.0.1:1080 --upgrade yt-dlp

# Download best audio, convert to mp3
yt-dlp --proxy socks5://127.0.0.1:1080 \
  -f bestaudio \
  --extract-audio --audio-format mp3 \
  -o "~/Downloads/%(title)s.%(ext)s" \
  "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Pitfalls

### SSL: UNEXPECTED_EOF_WHILE_READING
Some videos fail over SOCKS5 proxy with SSL errors. Try:
1. Different extractor: `--extractor-args "youtube:player_client=android"` (may still fail)
2. Direct connection (if not in China): `env -u ALL_PROXY yt-dlp ...`
3. If both fail, the video may be region-locked or the proxy unstable

### "Signature extraction failed"
yt-dlp is too old. Update: `pip install --proxy socks5://127.0.0.1:1080 --upgrade yt-dlp`

### "Content not available on this app"
Old yt-dlp + YouTube changed player. Update yt-dlp first, then retry.

### "No supported JavaScript runtime"
YouTube extraction without a JS runtime is deprecated but still works for basic downloads. Install deno for full support: `brew install deno`

### SOCKS5 proxy via ALL_PROXY breaks pip
When `ALL_PROXY=socks5://127.0.0.1:1080` is set in the environment, `pip install` fails with "Missing dependencies for SOCKS support". Fix:
```bash
env -u ALL_PROXY pip install pysocks   # one-time fix
# OR
env -u ALL_PROXY pip install --upgrade yt-dlp
# OR use --proxy flag
pip install --proxy socks5://127.0.0.1:1080 --upgrade yt-dlp
```

## Output
- Default: opus 251 (best quality) → auto-converted to mp3
- Output path: `~/Downloads/%(title)s.%(ext)s`
- File size varies: ~3.5MB for a 3-minute song at 128kbps mp3
