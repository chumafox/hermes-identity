# SSH config for GitHub via Port 443 (China / Firewall / VPN)

## The problem

GitHub's SSH port 22 is blocked or intercepted by:
- VPNs that hijack outbound SSH (e.g. Shadowrocket, Surge, Clash on macOS — you see `Connection closed by 198.18.x.x`)
- Corporate firewalls
- National-level filtering (China, UAE, etc.)

## The fix: ssh.github.com on port 443

GitHub provides an SSH endpoint on HTTPS port 443 that bypasses most interceptors.

### ~/.ssh/config entry

```
Host github.com
  HostName ssh.github.com
  Port 443
  User git
  IdentityFile ~/.ssh/id_ed25519_hermes
  StrictHostKeyChecking no
```

This transparently routes all `git@github.com:owner/repo.git` URLs through port 443 — no URL rewriting needed.

### Verify

```bash
ssh -T git@github.com
# Expected: "Hi username! You've successfully authenticated..."
# Exit code 1 is SUCCESS — GitHub doesn't grant shell access
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection closed by 198.18.x.x` | VPN proxy on 198.18.0.0/15 intercepting port 22 | Use port 443 config above |
| `Host key verification failed` | First connection, host key unknown | Add `StrictHostKeyChecking no` or `ssh -o` flag |
| `Permission denied (publickey)` | Wrong key or key not registered | Explicitly test with `ssh -T -i ~/.ssh/<key> git@github.com` |
| Connection hangs / timeout | Port 443 also blocked | Fall back to HTTPS token auth |

### GitHub key naming convention

For agent-managed machines, name keys clearly:

- `id_ed25519_hermes` — main key for identity sync
- `id_ed25519_github` — general GitHub access key
- Title on GitHub: `hermes-agent-<machine-name>` for easy identification

### Multiple machines, same key

Copy the same private key to all machines for unified auth:

```bash
scp ~/.ssh/id_ed25519_hermes admin@other-mac:~/.ssh/
scp ~/.ssh/id_ed25519_hermes.pub admin@other-mac:~/.ssh/
# Set permissions
ssh admin@other-mac "chmod 600 ~/.ssh/id_ed25519_hermes ~/.ssh/config"
```

One key, one GitHub registration, works everywhere.
