#!/bin/bash
# deploy-skills.sh — деплой всех Hermes скиллов во все CLI агенты
# Usage: cd ~/cli-common && bash deploy-skills.sh

set -euo pipefail

CLI_COMMON="$HOME/cli-common"

echo "=== Hermes Skills Deploy ==="
echo ""

STEP=1
echo "[$STEP/3] Hermes SKILL.md -> unified skill.yaml"
python3 "$CLI_COMMON/convert-hermes-to-unified.py" 2>&1 || exit 1
echo ""

STEP=$((STEP + 1))
echo "[$STEP/3] unified skill.yaml -> agents/*.md"
python3 "$CLI_COMMON/convert-skills.py" 2>&1 || exit 1
echo ""

STEP=$((STEP + 1))
echo "[$STEP/3] Symlink во все CLI"
cd "$CLI_COMMON" && bash deploy.sh 2>&1 || exit 1

echo ""
echo "=== Done ==="
echo "Agents:  $(ls "$CLI_COMMON/agents/"*.md 2>/dev/null | wc -l)"
echo "Claude:  $(ls "$HOME/.claude/agents/"*.md 2>/dev/null | wc -l)"
echo "Cursor:  $(ls "$HOME/.cursor/agents/"*.md 2>/dev/null | wc -l)"
echo "OpenCode:$(ls "$HOME/.config/opencode/agents/"*.md 2>/dev/null | wc -l)"
