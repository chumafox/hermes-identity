# Hermes Venv Recovery on Headless Mac (admin@admin-admin)

## Context

The headless Mac (admin, M1 Pro 32GB, China, no physical display) had Hermes v0.13.0 installed via `~/.hermes/hermes-agent/` with a venv at `venv/bin/python3` symlinked to `/tmp/hermes_bundle/python/bin/python3`.

After a system cleanup/reboot, `/tmp/hermes_bundle/` was deleted, breaking the venv.

## Symptom

```
admin@admin-admin ~ % hermes
/Users/admin/bin/hermes: /Users/admin/.hermes/hermes-agent/venv/bin/hermes: /Users/admin/.hermes/hermes-agent/venv/bin/python: bad interpreter: No such file or directory
```

## System State

- macOS (Apple Silicon, M1 Pro)
- Python 3.9.6 at `/usr/bin/python3` (system)
- Python 3.12.13 at `/opt/homebrew/bin/python3.12` (via brew)
- No brew CLI on PATH (must use full path `/opt/homebrew/bin/brew`)
- `uv` 0.11.13 at `/Users/admin/.local/bin/uv`
- Original venv was Python 3.11 (indicated by `pip3.11` in venv/bin/)

## Fix Steps

```bash
# 1. SSH into headless Mac from jenyanovak's Mac
sshpass -p '0000' ssh -o StrictHostKeyChecking=no admin@192.168.0.174

# 2. Check the broken symlink
ls -la /Users/admin/.hermes/hermes-agent/venv/bin/python3
# lrwxr-xr-x python3 -> /tmp/hermes_bundle/python/bin/python3  (BROKEN)

# 3. Remove broken venv
rm -rf /Users/admin/.hermes/hermes-agent/venv

# 4. Recreate with Python 3.12 via uv
cd /Users/admin/.hermes/hermes-agent
/Users/admin/.local/bin/uv venv --python 3.12 venv

# 5. Install deps
source venv/bin/activate
/Users/admin/.local/bin/uv pip install -e ".[dev]"

# 6. Verify
/Users/admin/.hermes/hermes-agent/venv/bin/hermes --version
# Hermes Agent v0.13.0 — should work
```

## PATH Fix

The wrapper script at `/Users/admin/bin/hermes` calls `venv/bin/hermes` directly,
so after the venv fix it should work. But the PATH to `~/bin/` was only in `.zshrc`,
which macOS zsh does NOT source for non-interactive login shells (`zsh -l -c "cmd"`).

Fix: add PATH to `~/.zshenv` (always sourced):

```bash
echo 'export PATH="/Users/admin/bin:/Users/admin/.local/bin:/usr/local/bin:$PATH"' > ~/.zshenv
```

Verification:
```bash
zsh -l -c "hermes --version"
# Hermes Agent v0.13.0
```

## Access Details

| Parameter | Value |
|-----------|-------|
| Host | admin@admin-admin |
| IP (WiFi) | 192.168.0.174 |
| IP (Thunderbolt) | 192.168.2.2 |
| IP (Type-C) | 192.168.3.2 |
| Password | 0000 |
| sshpass cmd | `sshpass -p '0000' ssh -o StrictHostKeyChecking=no admin@192.168.0.174 'cmd'` |
