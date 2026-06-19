# brew tap Workaround for China

## Problem

`brew tap <org>/<repo>` clones a git repo — and git through brew **does not respect** `http.proxy` or `ALL_PROXY`. From China, `brew tap` will hang or fail with:

```
fetch-pack: unexpected disconnect while reading sideband packet
Error: SIGTERM
```

## Fix: download DMG/app bundle directly from GitHub Releases via SOCKS5

```bash
# 1. Find the latest release assets
curl -s --socks5 127.0.0.1:1080 --max-time 15 \
  https://api.github.com/repos/<org>/<repo>/releases/latest \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tag_name']); [print(a['name']) for a in d['assets']]"

# 2. Download the aarch64 DMG (Apple Silicon) or x64 DMG (Intel)
curl -L --socks5 127.0.0.1:1080 --max-time 300 \
  -o /tmp/app.dmg \
  "https://github.com/<org>/<repo>/releases/download/<tag>/<filename>.dmg"

# 3. Mount, install, clean
hdiutil attach /tmp/app.dmg -nobrowse
cp -R /Volumes/AppName/AppName.app /Applications/
hdiutil detach /Volumes/AppName
rm /tmp/app.dmg

# 4. Remove quarantine if needed
xattr -d com.apple.quarantine /Applications/AppName.app 2>/dev/null || true

# 5. Launch
open /Applications/AppName.app
```

## Key points

- `brew tap` fails in China because brew's git clone ignores proxy env vars
- Direct DMG download via `curl --socks5` works because curl respects the flag
- Pick `aarch64` DMG for Apple Silicon (M1/M2/M3/M4), `x64` for Intel
- For Homebrew formulas that don't have a DMG release — try `HOMEBREW_NO_AUTO_UPDATE=1 brew install` first, or download the `.tar.gz` source and build manually
- Cask-based installs (`brew install --cask`) may also fail — prefer direct DMG download
