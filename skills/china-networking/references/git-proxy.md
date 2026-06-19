# Git Proxy for China (hermes update fix)

## Problem

`hermes update` fails with:
```
→ Fetching updates...
✗ Failed to fetch updates from origin.
  error: RPC failed; curl 56 Recv failure: Operation timed out
```

**Root cause:** GitHub is inaccessible without proxy from China. `hermes update` runs `git fetch origin` via `subprocess.run()` — it does NOT inherit `$ALL_PROXY`, `$HTTP_PROXY`, or any shell environment variable.

## Fix

```bash
# Set git's global proxy (persists across all subprocess git calls)
git config --global http.proxy socks5h://127.0.0.1:1080
git config --global https.proxy socks5h://127.0.0.1:1080

# Run update — works now
hermes update
```

**Why `socks5h` (not `socks5`):** The `h` variant makes DNS resolution go through the proxy too. Without it, git resolves GitHub's IP directly (which may be blocked), then tunnels the TCP connection — still fails if DNS is poisoned or blocked.

## Verification

```bash
# Check current proxy setting
git config --global --get http.proxy

# Test that git can reach GitHub
ALL_PROXY=socks5h://127.0.0.1:1080 git ls-remote https://github.com/NousResearch/hermes-agent.git HEAD
```

## Remove (when on direct internet)

```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

## What doesn't work

- `$ALL_PROXY` in shell — `hermes update` spawns `subprocess.run(["git", ...])` without passing env
- `$HTTP_PROXY` / `$HTTPS_PROXY` — same reason
- Setting proxy in `~/.ssh/config` — only works for SSH git remotes, not HTTPS
