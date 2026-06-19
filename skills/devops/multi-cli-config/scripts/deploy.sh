#!/bin/bash
# deploy.sh — развернуть общие конфиги во все CLI-инструменты
# Usage: cd ~/cli-common && bash deploy.sh [--dry-run]

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

for tool_dir in ~/.claude ~/.config/opencode ~/.cursor; do
  DRY mkdir -p "$tool_dir/agents"
  for f in ~/cli-common/agents/*.md; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    DRY ln -sf "$f" "$tool_dir/agents/$name"
    echo "  -> $(basename $tool_dir): $name"
  done
done

# agy — динамические, создаём dir для future-proof
DRY mkdir -p ~/.config/agy/agents ~/.config/agy/mcp
echo "  -> agy: dirs created"

# ── 2. MCP ─────────────────────────────────────
echo ""
echo "[2/3] MCP"

# Cursor: symlink
DRY ln -sf ~/cli-common/mcp/mcp-source.json ~/.cursor/mcp.json
echo "  -> Cursor: mcp symlinked"

# Claude Code: jq merge
if command -v jq &>/dev/null; then
  echo "  -> Claude: merging MCP..."
  if ! $DRY_RUN; then
    NEW_MCP=$(cat ~/cli-common/mcp/mcp-source.json | jq '.mcpServers')
    EXISTING=$(cat ~/.claude.json 2>/dev/null || echo '{}')
    MERGED=$(echo "$EXISTING" | jq --argjson new "$NEW_MCP" '.mcpServers = (.mcpServers // {}) * $new')
    echo "$MERGED" > ~/.claude.json
    echo "  -> Claude: MCP merged"
  fi
else
  echo "  -> !!! jq not found. Install: brew install jq"
fi

echo "  -> OpenCode: MCP manual (section 'mcp' in opencode.json)"
echo "  -> Hermes: MCP manual (plugins/mcp in config.yaml)"

# ── 3. AGENTS.md ───────────────────────────────
echo ""
echo "[3/3] AGENTS.md"

PROJECTS_DIR="$HOME/projects/active"
if [ -d "$PROJECTS_DIR" ]; then
  for project in "$PROJECTS_DIR"/*/; do
    name=$(basename "$project")
    target="$project/AGENTS.md"
    if [ ! -f "$target" ]; then
      DRY ln -sf "$HOME/cli-common/AGENTS.md" "$target"
      echo "  -> $name: AGENTS.md linked"
    else
      echo "  -> $name: already has AGENTS.md — skipped"
    fi
  done
fi

echo ""
echo "=== Done ==="
echo ""
echo "Notes:"
echo "  - New agent: add to ~/cli-common/agents/ -> deploy.sh"
echo "  - New MCP: update ~/cli-common/mcp/mcp-source.json -> deploy.sh"
echo "  - New project: ln -s ~/cli-common/AGENTS.md path/to/AGENTS.md"