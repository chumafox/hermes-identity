#!/bin/bash
IDENTITY_DIR="$HOME/hermes-identity"

# Copy identity files
cp "$HOME/.hermes/AGENTS.md" "$IDENTITY_DIR/" 2>/dev/null || true
cp "$HOME/.hermes/skills/"*/*/SKILL.md "$IDENTITY_DIR/skills/" 2>/dev/null || true

# Git operations
cd "$IDENTITY_DIR"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "identity sync $(date +%Y-%m-%d_%H:%M)"
  git push
fi
