#!/bin/bash
IDENTITY_DIR="$HOME/hermes-identity"

# Copy identity files
cp "$HOME/.hermes/AGENTS.md" "$IDENTITY_DIR/" 2>/dev/null || true
cp -r "$HOME/.hermes/skills/" "$IDENTITY_DIR/skills/" 2>/dev/null || true

# Also copy back from repo to .hermes (for the headless Mac)
cp "$IDENTITY_DIR/AGENTS.md" "$HOME/.hermes/AGENTS.md" 2>/dev/null || true

# Git operations
cd "$IDENTITY_DIR"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "identity sync $(date +%Y-%m-%d_%H:%M)"
  git pull --rebase origin main
  git push
fi
