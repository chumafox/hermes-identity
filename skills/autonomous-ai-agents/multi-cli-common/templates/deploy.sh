#!/bin/bash
# deploy.sh — развернуть общие агенты, MCP и контекст во все CLI-инструменты
# Usage: ./deploy.sh [--dry-run]
# Запускать из ~/cli-common/

set -euo pipefail

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

DRY() {
  if $DRY_RUN; then echo "  [DRY] $*"; else eval "$@"; fi
}

echo "=== Разворачиваем общие конфиги ==="

# ── 1. Агенты ──────────────────────────────────
echo ""
echo "[1/3] Агенты"

# Claude Code
DRY mkdir -p ~/.claude/agents
for f in agents/*.md; do
  name=$(basename "$f")
  DRY ln -sf "$PWD/$f" "$HOME/.claude/agents/$name"
  echo "  -> Claude: $name"
done

# OpenCode
DRY mkdir -p ~/.config/opencode/agents
for f in agents/*.md; do
  name=$(basename "$f")
  DRY ln -sf "$PWD/$f" "$HOME/.config/opencode/agents/$name"
  echo "  -> OpenCode: $name"
done

# Cursor
DRY mkdir -p ~/.cursor/agents
for f in agents/*.md; do
  name=$(basename "$f")
  DRY ln -sf "$PWD/$f" "$HOME/.cursor/agents/$name"
  echo "  -> Cursor: $name"
done

# ── 2. MCP (Cursor — как source of truth) ──────
echo ""
echo "[2/3] MCP"

# Cursor mcp.json — symlink напрямую
DRY ln -sf "$PWD/mcp/mcp-source.json" "$HOME/.cursor/mcp.json"
echo "  -> Cursor: mcp symlinked"

# OpenCode — добавлять вручную через opencode.json (формат отличается)
echo "  -> OpenCode: требуется ручное добавление MCP в opencode.json"

# Claude Code — mcp в ~/.claude.json (мерж через jq)
if command -v jq &>/dev/null; then
  if [ -f ~/cli-common/mcp/mcp-source.json ]; then
    echo "  -> Claude: мержим MCP в ~/.claude.json..."
    if ! $DRY_RUN; then
      NEW_MCP=$(cat ~/cli-common/mcp/mcp-source.json | jq '.mcpServers')
      EXISTING=$(cat ~/.claude.json 2>/dev/null || echo '{}')
      MERGED=$(echo "$EXISTING" | jq --argjson new "$NEW_MCP" '.mcpServers = (.mcpServers // {}) * $new')
      echo "$MERGED" > ~/.claude.json
      echo "  -> Claude: MCP обновлён"
    fi
  fi
else
  echo "  -> !!! jq не найден. Установи: brew install jq"
fi

# ── 3. AGENTS.md — symlink в каждый проект ──────
echo ""
echo "[3/3] AGENTS.md — shared контекст"

PROJECTS_DIR="$HOME/projects/active"
if [ -d "$PROJECTS_DIR" ]; then
  for project in "$PROJECTS_DIR"/*/; do
    name=$(basename "$project")
    target="$project/AGENTS.md"
    if [ ! -f "$target" ]; then
      DRY ln -sf "$PWD/AGENTS.md" "$target"
      echo "  -> $name: AGENTS.md linked"
    else
      echo "  -> $name: уже есть AGENTS.md — пропускаем"
    fi
  done
fi

echo ""
echo "=== Готово ==="
