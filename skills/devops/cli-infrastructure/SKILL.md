---
name: cli-infrastructure
description: "Управление общей инфраструктурой CLI-агентов: ~/cli-common как единый source of truth для агентов, MCP, AGENTS.md. Развёртывание конфигов во все CLI (Claude Code, OpenCode, Cursor, Hermes, agy). Конвертация форматов саб-агентов между разными frontmatter-схемами."
tags: [cli, infrastructure, mcp, agents, devops, deploy, config, multi-cli]
related_skills: [subagent-mentor, hermes-agent, hermes-provider-config]
---

# CLI Infrastructure

Единый source of truth для конфигов всех CLI-агентов на машине.
Избавляет от дублирования MCP-серверов, агентов и контекста между Claude Code, OpenCode, Cursor, Hermes и Antigravity.

## Архитектура

```
~/cli-common/
├── agents/                # Source .md файлы агентов (формат Claude Code)
├── mcp/mcp-source.json    # Source of truth для MCP серверов
├── skills/                # Единый YAML-формат скиллов
│   └── <name>/skill.yaml  #   description, body, claude:, opencode:, cursor:, hermes:
├── AGENTS.md              # Общий контекст (user preferences, env, conventions)
├── deploy.sh              # Развернуть агенты + MCP во все CLI
├── convert-skills.py      # Конвертер: skill.yaml → agents/*.md + Hermes SKILL.md
└── README.md
```

## Различия форматов frontmatter между CLI

| Поле | Claude Code | OpenCode | Cursor |
|---|---|---|---|
| tools | `tools: Read, Grep` (str) | `tools: {read: true}` (obj) | `tools: Read, Grep` (str) |
| model | `model: sonnet` | `model: provider/model-id` | `model: fast/inherit` |
| readonly | permissionMode | — | `readonly: true/false` |
| background | `background: true` | — | `is_background: true` |
| mode | нет | `mode: subagent/primary` | нет |

**Питфолл:** OpenCode не принимает строковый `tools` — только объект.
**Решение:** deploy.sh копирует (не symlink) .md агенты в OpenCode с конвертацией `tools` через regex.

## MCP: единый source of truth

`mcp/mcp-source.json` — все MCP серверы в одном JSON (формат Cursor). deploy.sh раскладывает:

| Инструмент | Куда пишет | Механизм |
|---|---|---|
| **Cursor** | ~/.cursor/mcp.json | symlink на mcp-source.json |
| **Claude Code** | ~/.claude.json (mcpServers) | jq merge |
| **OpenCode** | ~/.config/opencode/opencode.json (секция mcp) | Python конвертация |
| **Hermes** | ~/.hermes/config.yaml (mcp_servers) | Python YAML-запись |

**Важно:** `mcp-source.json` в формате Cursor — command как строка + args массив.
OpenCode и Hermes ожидают command как единую строку или массив.
Конвертация делается в deploy.sh скриптом.

## Конвертер скиллов (convert-skills.py)

Читает `skills/<name>/skill.yaml` — единый YAML с секциями под каждый CLI:

```yaml
description: "Проверяет код"
body: |
  Ты — ревьюер кода.
claude:
  tools: "Read, Grep, Glob, Bash"
  model: "sonnet"
opencode:
  mode: "subagent"
  temperature: 0.1
  steps: 15
cursor:
  readonly: false
  is_background: false
hermes:
  tags: ["code-review"]
  content: |
    # Инструкции для Hermes...
```

Генерирует:
- `agents/<name>.md` — общий .md агент (для Claude/Cursor/OpenCode после конвертации)
- `~/.hermes/skills/<name>/SKILL.md` — Hermes-скилл

## Workflow

### Добавить MCP сервер
1. Отредактировать mcp-source.json
2. `cd ~/cli-common && bash deploy.sh`
3. Появится во всех CLI

### Создать новый скилл
1. `mkdir ~/cli-common/skills/my-skill && vim skill.yaml`
2. `convert-skills.py my-skill`
3. `deploy.sh`

### Добавить агента (прямой .md)
1. Положить `.md` в `~/cli-common/agents/`
2. `deploy.sh` — symlink в Claude/Cursor, копия с конвертацией в OpenCode

### Развернуть всё
```bash
cd ~/cli-common && bash deploy.sh
```

## AGENTS.md стратегия

Один `AGENTS.md` в `~/cli-common/` — user preferences, env, conventions.
Symlink во все проекты. Если проект уже имеет свой AGENTS.md — не трогать.
Для проект-специфичного контекста — редактировать файл в проекте напрямую (разорвёт symlink).

**Питфолл:** Hermes `patch` tool заблокирован для `~/.hermes/config.yaml`. MCP туда пишется через Python скрипт внутри deploy.sh, который патчит YAML напрямую.

## kimi-code provider config

kimi-code (v0.14.3) uses TOML at `~/.kimi-code/config.toml`. Provider type `openai_legacy` is **invalid** — use `openai` instead. See `references/kimi-code-provider-types.md` for volc-coding setup and verification.
