# SSH Persistence Solutions — Comparison

Source: Antigravity CLI's brain on the headless Mac (archived here for reference).

## The Problem

Mosh and Tmux break native scroll in terminal emulators (Ghostty, iTerm2, etc.):
- **Mosh** syncs only the current frame — no scroll history on the client
- **Tmux/Zellij** capture the screen buffer — scroll only works inside the multiplexer

## Solutions That Preserve Native Scroll

### 1. Eternal Terminal (ET) — Рекомендуемый в общем случае

SSH replacement that preserves native scroll because it's a byte stream (like SSH).

| Feature | Details |
|---------|---------|
| Scroll | Native (Ghostty buffer) |
| Auto-reconnect | Automatic in background |
| Port | TCP 2022 |
| Install | `brew install et` (both Macs) |
| Connect | `et user@server_ip` |

**Pros:** Native scroll, auto-reconnect, transparent.
**Cons:** Extra port needed (TCP 2022), another daemon.

### 2. Shpool (Shell Pool) — Лёгкая альтернатива tmux

Rust-based, doesn't interfere with terminal rendering.

| Feature | Details |
|---------|---------|
| Scroll | Native (Ghostty buffer) |
| Reconnect | Manual (SSH reconnection) |
| Port | TCP 22 (standard SSH) |
| Install | `cargo install shpool` (headless only) |
| Connect | `ssh -t user@host "shpool attach main \|\| shpool daemon & shpool attach main"` |

**Pros:** Native scroll, no extra ports, lightweight.
**Cons:** Manual reconnect, session must be reattached.

### 3. Mosh + tmux — Для очень плохих сетей

Only option when the network is terrible (3G in a train, high packet loss). Mosh handles sync, tmux handles scroll.

**Pros:** Best network resilience, local echo.
**Cons:** No native scroll (tmux copy-mode only), two layers of complexity.

## User's Choice (This Instance) — Eternal Terminal (ET)

**Final decision: Eternal Terminal (ET).** After testing Mosh, Zellij, and ET in this dual-Mac setup (display Mac in HK, headless Mac behind Chinese firewall):

- Mosh: breaks native scroll, UDP ports need forwarding
- Zellij: scroll works but requires multiplexer mode (Ctrl+p), another layer of complexity
- **ET: native scroll, auto-reconnect, byte-stream transparent to Ghostty** ✅

### Setup (verified working)

**Install on both Macs:**
```bash
brew install et
# If brew hangs on auto-update, use:
HOMEBREW_NO_AUTO_UPDATE=1 brew install et
```

**Start server on headless Mac:**
```bash
sudo brew services start et
# Or manually:
/opt/homebrew/opt/et/bin/etserver --cfgfile /opt/homebrew/etc/et.cfg
```

**Config** (`/opt/homebrew/etc/et.cfg`):
```ini
[Networking]
port = 2022
```

**Verify server is listening:**
```bash
lsof -i :2022 | grep LISTEN
```

**Connect (display Mac):**
```bash
et admin-remote
```
Works with standard `~/.ssh/config` host aliases.

Current `pro` alias:
```zsh
pro() { et admin-remote; }
```

### Pitfalls

- **brew API may fail behind GFW:** use `HOMEBREW_NO_AUTO_UPDATE=1` to skip formula update
- **ET uses TCP port 2022** (not UDP like Mosh) — verify it's accessible between Macs
- **et server must be running** on the headless Mac before `pro` will work
- **Scroll is native** — Ghostty config should be clean (no mouse_reporting=false, no scroll keybind overrides). ET passes byte stream like regular SSH
- **No local echo** (unlike Mosh) — latency feels like regular SSH

## Zellij Reference (Documented for Future Reference)

Zellij was tested and documented in the main `macos-ssh-setup` skill. Key takeaways:

- `brew install zellij` on both Macs
- Minimal config (`~/.config/zellij/config.kdl`):
  ```
  theme: "default"
  scrollback_lines_to_search: 10000
  ```
- `Ctrl+p` for scroll/search mode, `Esc` to exit
- Mouse wheel scrolling works out of the box — NO custom mouse bindings needed
- **Pitfall:** KDL parser does NOT support `bind "Mouse { direction: Up }"` syntax
- **Pitfall:** Mosh/Zellij conflict — don't use together
- **Pitfall:** `ssh -t` is required for Zellij UI rendering
