#!/bin/bash
IDENTITY_DIR="$HOME/hermes-identity"

# Copy identity files from Hermes home → repo
cp "$HOME/.hermes/SOUL.md" "$IDENTITY_DIR/soul.md" 2>/dev/null || true
cp -r "$HOME/.hermes/skills/" "$IDENTITY_DIR/skills/" 2>/dev/null || true

# Copy back from repo → Hermes home (for files loaded by Hermes)
cp "$IDENTITY_DIR/soul.md" "$HOME/.hermes/SOUL.md" 2>/dev/null || true

# Git operations
cd "$IDENTITY_DIR"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "identity sync $(date +%Y-%m-%d_%H:%M)"
  git pull --rebase origin main 2>/dev/null
  git push
fi
