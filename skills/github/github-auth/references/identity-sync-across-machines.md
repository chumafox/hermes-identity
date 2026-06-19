# Identity sync across machines

## Concept

Keep identity files in sync across multiple Hermes agent machines via a shared GitHub repo.

**Key Hermes loading behavior:**
- `~/.hermes/SOUL.md` — loaded automatically as identity (system prompt slot #1)
- `AGENTS.md` from cwd — loaded as project context, NOT from `~/.hermes/`
- `~/.hermes/SOUL.md` must exist for Hermes to have the personality definition

## Architecture

```
┌─────────────────────┐     git push/pull     ┌─────────────────────┐
│  Machine A (screen) │ ◄──────────────────► │  Machine B (headless)│
│  ~/hermes-identity/ │      GitHub repo      │  ~/hermes-identity/ │
│  Cron: 4:00 daily   │   chumafox/hermes-    │  launchd: 4:05      │
└─────────────────────┘   identity.git        └─────────────────────┘
```

Each machine:
1. Copies SOUL.md from `~/.hermes/SOUL.md` → `~/hermes-identity/soul.md` (bidirectional — also copies back so Hermes picks it up on next session)
2. Copies skills from `~/.hermes/skills/` → `~/hermes-identity/skills/`
3. `git add -A && git commit -m "sync $(date)" && git pull --rebase && git push`
4. Before push: `git pull --rebase` to merge remote changes

## Setup steps

### 1. Create repo on GitHub
- `github.com/new`
- Name: `hermes-identity`
- Do NOT initialize with README/.gitignore

### 2. Clone on first machine
```bash
cd ~/ && git clone git@github.com:chumafox/hermes-identity.git
```

### 3. Copy identity files and push
```bash
cd ~/hermes-identity
cp ~/.hermes/SOUL.md soul.md 2>/dev/null || touch soul.md
mkdir -p skills
cp -r ~/.hermes/skills/* skills/ 2>/dev/null || true
git add -A && git commit -m "init" && git push
```

Note: `SOUL.md` (upper case) is what Hermes reads. `soul.md` (lower case) in the repo is the git-tracked copy. The sync script does bidirectional copy: `SOUL.md` → `soul.md` on export, `soul.md` → `SOUL.md` on import.

### 4. Set up auto-sync

**Machine A (Hermes cron):**
```
hermes cron create "0 4 * * *" --name identity-sync --prompt "..." --deliver local
```

**Machine B (launchd — when crontab is blocked):**
Create `~/Library/LaunchAgents/com.hermes.identity-sync.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hermes.identity-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/USER/hermes-identity/sync.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>4</integer>
        <key>Minute</key>
        <integer>5</integer>
    </dict>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/hermes-identity-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/hermes-identity-sync.log</string>
</dict>
</plist>
```
Load: `launchctl load ~/Library/LaunchAgents/com.hermes.identity-sync.plist`

### 5. sync.sh script

```bash
#!/bin/bash
IDENTITY_DIR="$HOME/hermes-identity"

# Copy Hermes identity files → repo
cp "$HOME/.hermes/SOUL.md" "$IDENTITY_DIR/soul.md" 2>/dev/null || true
cp -r "$HOME/.hermes/skills/" "$IDENTITY_DIR/skills/" 2>/dev/null || true

# Copy back from repo → Hermes home (bidirectional)
cp "$IDENTITY_DIR/soul.md" "$HOME/.hermes/SOUL.md" 2>/dev/null || true

# Git operations
cd "$IDENTITY_DIR"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "identity sync $(date +%Y-%m-%d_%H:%M)"
  git pull --rebase origin main
  git push
fi
```

### 6. macOS crontab workaround

macOS SIP may block `crontab` with "Operation not permitted". Use launchd instead (step 4).

## What syncs / what doesn't

| Item | Syncs? | Loaded by Hermes? | Notes |
|------|--------|-------------------|-------|
| soul.md / SOUL.md | ✅ bidirectional | ✅ `~/.hermes/SOUL.md` loaded automatically | Identity slot #1 in system prompt |
| AGENTS.md | ✅ | ❌ only from cwd, not auto-loaded | Project context, not identity |
| memory-backup.md | ✅ one-way | ❌ text dump only | Memory DB is separate per machine |
| Skills | ✅ one-way | ❌ must be in `~/.hermes/skills/` | Copied each sync |
| Memory DB | ❌ | — | Separate SQLite DB per machine |
| Config (providers, models) | ❌ | — | Machine-specific hardware/networking |
| Sessions | ❌ | — | Local SQLite DB only |
