---
name: multi-cli-config
description: "Centralise and deploy shared configuration (agents, MCP, AGENTS.md) across multiple CLI AI agents: Claude Code, OpenCode, Cursor, agy, and Hermes. Symlink-based single source of truth with a deploy script."
tags: ["devops"]
---

# Multi-CLI Config

Управление общими конфигами (агенты, MCP, контекст) для нескольких CLI AI-инструментов.

## Проблема

При использовании нескольких CLI-агентов (Claude Code, OpenCode, Cursor, agy, Hermes) каждый хранит свои конфиги отдельно. Агенты, MCP-сервера и AGENTS.md дублируются.

## Решение: единый source of truth + deploy-скрипт

### Архитектура

```
~/cli-common/
├── agents/*.md
├── mcp/mcp-source.json
├── AGENTS.md
├── deploy.sh
└── README.md
```

### Принципы

1. Symlink где можно — agents/*.md во все agents/ директории
2. Merge где нужно — MCP мержится через jq в ~/.claude.json
3. Source of truth = Cursor (самый полный набор MCP)
4. Existing preserved — проекты с собственным AGENTS.md не перезаписываются

### Покрытие по инструментам

| Инструмент | Агенты | MCP |
|---|---|---|
| Claude Code | symlink | jq merge в ~/.claude.json |
| OpenCode | symlink | вручную в opencode.json |
| Cursor | symlink | symlink ~/.cursor/mcp.json |
| agy | dynamic (/goal) | N/A |
| Hermes | своя система (skills) | config.yaml |

## Развёртывание

### deploy.sh — ключевые шаги

```bash
# 1. Агенты — symlink во все CLI
for tool in ~/.claude ~/.config/opencode ~/.cursor; do
  mkdir -p "$tool/agents"
  for f in ~/cli-common/agents/*.md; do
    ln -sf "$f" "$tool/agents/$(basename "$f")"
  done
done

# 2. MCP — Cursor symlink, Claude jq merge
ln -sf ~/cli-common/mcp/mcp-source.json ~/.cursor/mcp.json

if command -v jq &>/dev/null; then
  NEW=$(cat ~/cli-common/mcp/mcp-source.json | jq '.mcpServers')
  EXISTING=$(cat ~/.claude.json 2>/dev/null || echo '{}')
  echo "$EXISTING" | jq --argjson n "$NEW" '.mcpServers = (.mcpServers // {}) * $n' > ~/.claude.json
fi

# 3. AGENTS.md — symlink в проекты (где нет своего)
for project in ~/projects/active/*/; do
  target="$project/AGENTS.md"
  [ ! -f "$target" ] && ln -sf ~/cli-common/AGENTS.md "$target"
done
```

### Когда запускать

- Добавил агента → agents/*.md → deploy.sh
- Добавил MCP сервер → mcp-source.json → deploy.sh
- Новый проект → ln -s ~/cli-common/AGENTS.md проект/AGENTS.md

## AGENTS.md — содержимое

В общий AGENTS.md идёт проект-независимый контекст:
- Communication conventions (язык, стиль)
- Environment (OS, location, прокси, регион)
- Project layout
- Code conventions
- CLI tools available

Проект-специфичный контекст — в отдельном AGENTS.md в корне проекта.

## Pitfalls

- OpenCode MCP — формат отличается (секция mcp внутри opencode.json, не отдельный файл)
- Hermes MCP — через config.yaml (plugins/mcp), не автоматизируется
- agy subagents — динамические, конфиг не нужен
- Без jq (brew install jq) Claude MCP merge не сработает
- Существующие AGENTS.md в проектах не перезаписываются — удали вручную если нужен shared
