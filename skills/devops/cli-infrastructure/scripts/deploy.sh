#!/bin/bash
# deploy.sh — развернуть общие агенты, MCP и контекст во все CLI-инструменты
# Source: ~/cli-common/deploy.sh (copy referenced here for skill portability)
# Usage: cd ~/cli-common && ./deploy.sh [--dry-run]

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

# Claude Code — symlink
DRY mkdir -p ~/.claude/agents
for f in agents/*.md; do
  name=$(basename "$f")
  DRY ln -sf "$PWD/$f" "$HOME/.claude/agents/$name"
  echo "  -> Claude: $name"
done

# Cursor — symlink
DRY mkdir -p ~/.cursor/agents
for f in agents/*.md; do
  name=$(basename "$f")
  DRY ln -sf "$PWD/$f" "$HOME/.cursor/agents/$name"
  echo "  -> Cursor: $name"
done

# OpenCode — копия с конвертацией tools: str → obj
DRY mkdir -p ~/.config/opencode/agents
for f in agents/*.md; do
  name=$(basename "$f")
  target="$HOME/.config/opencode/agents/$name"
  if ! $DRY_RUN; then
    python3 << PYEOF
import re
with open("$PWD/$f") as fh:
    content = fh.read()
def convert_tools(m):
    tools_str = m.group(1)
    tool_names = [t.strip().lower() for t in tools_str.split(",")]
    return "tools:\n" + "\n".join(f"  {t}: true" for t in tool_names)
content = re.sub(r'^tools:\s*(.+)$', convert_tools, content, flags=re.MULTILINE)
with open("$target", "w") as fh:
    fh.write(content)
PYEOF
    echo "  -> OpenCode: $name (converted)"
  else
    echo "  -> OpenCode: $name [DRY]"
  fi
done

# agy — динамические, только создаём dir
DRY mkdir -p ~/.config/agy/agents ~/.config/agy/mcp
echo "  -> agy: dirs created"

# ── 2. MCP ─────────────────────────────────────
echo ""
echo "[2/3] MCP"

MCP_SOURCE="$PWD/mcp/mcp-source.json"
[ ! -f "$MCP_SOURCE" ] && { echo "  -> !!! mcp-source.json not found"; exit 1; }

# Cursor: symlink
DRY ln -sf "$MCP_SOURCE" "$HOME/.cursor/mcp.json"
echo "  -> Cursor: mcp symlink ✓"

# Claude Code: jq merge
if command -v jq &>/dev/null; then
  if ! $DRY_RUN; then
    NEW_MCP=$(cat "$MCP_SOURCE" | jq '.mcpServers')
    EXISTING=$(cat ~/.claude.json 2>/dev/null || echo '{}')
    echo "$EXISTING" | jq --argjson new "$NEW_MCP" '.mcpServers = (.mcpServers // {}) * $new' > ~/.claude.json
    echo "  -> Claude: mcp merged ✓"
  fi
else
  echo "  -> !!! jq not found"
fi

# Hermes: Python YAML update
if ! $DRY_RUN; then
  python3 << 'PYEOF'
import json, yaml
with open("/Users/jenyanovak/cli-common/mcp/mcp-source.json") as f:
    source = json.load(f)
hermes_mcp = {}
for name, cfg in source.get("mcpServers", {}).items():
    cmd = cfg.get("command", "")
    if cfg.get("args"):
        cmd = " ".join([cmd] + cfg["args"])
    hermes_mcp[name] = {"command": cmd, "timeout": 120, "connect_timeout": 30}
with open("/Users/jenyanovak/.hermes/config.yaml") as f:
    lines = f.readlines()
mcp_start = None; mcp_end = None
for i, line in enumerate(lines):
    if line.rstrip() == "mcp_servers:":
        mcp_start = i
    elif mcp_start is not None and i > mcp_start and line and not line[0].isspace():
        mcp_end = i; break
if mcp_end is None: mcp_end = len(lines)
new_mcp = ["mcp_servers:\n"]
for name, cfg in hermes_mcp.items():
    new_mcp += [f"  {name}:\n", f"    command: {cfg['command']}\n", f"    timeout: {cfg['timeout']}\n", f"    connect_timeout: {cfg['connect_timeout']}\n"]
if mcp_start is not None:
    lines = lines[:mcp_start] + new_mcp + lines[mcp_end:]
else:
    lines += ["\n"] + new_mcp
with open("/Users/jenyanovak/.hermes/config.yaml", "w") as f:
    f.writelines(lines)
print("  -> Hermes: mcp updated ✓")
PYEOF
fi

# OpenCode: Python JSON update
if command -v jq &>/dev/null && ! $DRY_RUN; then
  python3 << 'PYEOF'
import json
with open("/Users/jenyanovak/cli-common/mcp/mcp-source.json") as f:
    source = json.load(f)
with open("/Users/jenyanovak/.config/opencode/opencode.json") as f:
    oc = json.load(f)
oc.setdefault("mcp", {})
for name, cfg in source.get("mcpServers", {}).items():
    if cfg.get("type") == "http":
        oc["mcp"][name] = {"type": "http", "url": cfg["url"], "headers": cfg.get("headers",{}), "enabled": True}
    else:
        oc["mcp"][name] = {"command": [cfg.get("command","")] + cfg.get("args",[]), "enabled": True, "type": "local"}
with open("/Users/jenyanovak/.config/opencode/opencode.json", "w") as f:
    json.dump(oc, f, indent=2, ensure_ascii=False)
print("  -> OpenCode: mcp updated ✓")
PYEOF
fi

# ── 3. AGENTS.md ────────────────────────────────
echo ""
echo "[3/3] AGENTS.md"

PROJECTS="$HOME/projects/active"
if [ -d "$PROJECTS" ]; then
  for p in "$PROJECTS"/*/; do
    name=$(basename "$p")
    target="$p/AGENTS.md"
    [ ! -f "$target" ] && DRY ln -sf "$PWD/AGENTS.md" "$target" && echo "  -> $name: linked" \
      || echo "  -> $name: exists, skip"
  done
fi

echo ""
echo "=== Done ==="
