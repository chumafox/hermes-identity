# GitHub SSH Access Behind GFW (Port 443)

## The Problem

When running a VPN/proxy on macOS (Shadowrocket, Surge, Clash, etc.), direct SSH to `github.com:22` is intercepted by the VPN's network extension:

```
$ ssh -T git@github.com
Connection closed by 198.18.0.37 port 22
```

The `198.18.x.x` IP range is the synthetic VPN range (Apple NEVPN framework) — the connection never reaches GitHub's real server.

## The Fix: SSH via `ssh.github.com:443`

GitHub provides an alt-SSH endpoint on port 443 specifically for restrictive networks:

```bash
ssh -T -p 443 git@ssh.github.com
# Hi username! You've successfully authenticated...
# (exit code 1 is normal — no shell access)
```

### One-time: accept host key

```bash
ssh -T -p 443 -o StrictHostKeyChecking=no git@ssh.github.com
```

## Permanent SSH Config

Add to `~/.ssh/config` so `git@github.com` transparently routes through the port-443 endpoint:

```
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519_hermes
```

Now `ssh git@github.com` and `git push` both work without port flags.

## Multiple Keys for Multiple Accounts (Optional)

If you have both a personal and a bot/hermes key:

```
Host github.com
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519_hermes

Host github.com-personal
    HostName ssh.github.com
    Port 443
    User git
    IdentityFile ~/.ssh/id_ed25519
```

Use `git@github.com-personal:owner/repo.git` as remote for personal repos.

## Detection

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection closed by 198.18.x.x` | VPN NE intercepts port 22 | Use port 443 |
| `Host key verification failed` | First time connecting to `ssh.github.com` | Accept the key once |
| `Permission denied (publickey)` | Wrong key or key not on GitHub | Verify key at `https://github.com/settings/keys` |
| `Connection refused` | Port 443 also blocked | Try SSH over HTTPS via `https://github.com` (clone via `https://` instead) |

## Why This Works

The VPN network extension intercepts SSH port 22 by default (standard SSH protocol), but does NOT intercept port 443 (reserved for HTTPS/WebSocket traffic). Since `ssh.github.com:443` speaks SSH-over-HTTPS (wrapped in TLS), the VPN sees HTTPS traffic and passes it through.

## Pitfalls

- **Only works for `github.com`** — not for self-hosted GHES or other git servers
- **Host key differs from `github.com:22`** — GitHub publishes a separate ED25519 key for `ssh.github.com`. First connect will prompt to accept it.
- **Some corporate VPNs block all outbound SSH** even on port 443 — in that case use HTTPS with personal access token as fallback
- **Dual GitHub accounts** — without separate Host entries, all repos use the same key. Configure per-account Host blocks in `~/.ssh/config`.
