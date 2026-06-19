# internet_pro.py — SSH Tunnel Internet Sharing

**Tool:** `~/projects/tools/internet-pro/internet_pro.py`

TUI для шаринга интернета pro→dispo через SSH dynamic tunnel.

## Ports

| Service | Port |
|---------|------|
| SOCKS5 | 1080 |
| HTTP bridge | 8888 |

## Quick Start

```bash
inpro  # alias → python3 ~/projects/tools/internet-pro/internet_pro.py
```

## Controls

| Key | Action |
|-----|--------|
| `P` | Toggle tunnel |
| `Y` | Toggle macOS system proxy |
| `K` | KeepAlive — auto-reconnect |
| `N` | Cycle interface |
| `S` | Proxy shell |
| `C` | Configure gateway |
| `Q` | Quit |

## KeepAlive

Press `K` to enable. Adds `ServerAliveInterval=15` to SSH. Auto-reconnects on drop. Survives sleep/wake.

## SSH Config

Uses `admin-remote` alias from `~/.ssh/config`:

```
Host admin-remote
  HostName 192.168.103.70
  User admin
  IdentityFile ~/.ssh/id_ed25519_headless
```

## Env for other CLI tools

```bash
export http_proxy=http://127.0.0.1:8888
export https_proxy=http://127.0.0.1:8888
export all_proxy=socks5://127.0.0.1:1080
```
