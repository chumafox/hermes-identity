---
name: multi-cli-common
description: "Shared agents/MCP/AGENTS.md/skills across multiple CLI AI tools (Claude Code, OpenCode, Cursor, agy, Hermes). Central source of truth in ~/cli-common/, symlinks, deploy script, and skill converter."
tags: [claude-code, opencode, cursor, hermes, agy, mcp, agents, config, multi-tool, antigravity]
related_skills: [macos-project-organization, subagent-mentor, hermes-agent, cli-tool-unification]
---

# Multi-CLI Common Config

Управление общими агентами, MCP серверами, скиллами и AGENTS.md для нескольких CLI AI-инструментов одновременно.

## Проблема

При использовании нескольких CLI-агентов (Claude Code, OpenCode, Cursor, agy, Hermes) каждый хранит свои конфиги отдельно. Агенты, MCP серверы и контекст проекта дублируются. Добавление нового MCP сервера требует правки 3-4 разных конфигов. Скиллы/агенты пишутся в разных форматах для каждого инструмента.

## Решение: ~/cli-common/

Центральное хранилище с симлинками во все инструменты + конвертер единого формата.

### Структура

```
~/cli-common/
├── agents/                # Общие саб-агенты (.md) — symlink во все CLI
├── skills/                # Единый YAML формат скиллов
│   └── <name>/
│       └── skill.yaml     #   description, body, claude:, cursor:, opencode:, hermes:
├── mcp/
│   └── mcp-source.json    # Source of truth для всех MCP серверов
├── AGENTS.md              # Общий контекст (user preferences, env)
├── deploy.sh              # Развернуть агенты + MCP во все CLI (авто)
├── convert-skills.py      # Конвертер: skill.yaml -> agents/*.md + hermes SKILL.md
└── README.md
```

### Покрытые инструменты

| Инструмент | Агенты | MCP | AGENTS.md |
|---|---|---|---|
| Claude Code | symlink from cli-common/agents/ | auto (jq merge) | из проекта |
| OpenCode | symlink from cli-common/agents/ | auto (python merge) | из проекта |
| Cursor | symlink from cli-common/agents/ | symlink to mcp-source.json | из проекта |
| Antigravity (agy) | dynamic via /goal (не поддерживает файлы) | N/A | из проекта |
| Hermes Agent | convert-skills.py -> SKILL.md | auto (python YAML) | из проекта |

### Батч-конвертация существующих Hermes скиллов → единый формат

Сценарий: у вас уже есть скиллы в `~/.hermes/skills/`, и вы хотите разом
раздать их во все CLI-агенты (Claude Code, OpenCode, Cursor, agy).

```bash
# Шаг 1: Конвертировать все Hermes SKILL.md → unified skill.yaml
python3 ~/cli-common/convert-hermes-to-unified.py

# Шаг 2: Конвертировать unified → agents/*.md
python3 ~/cli-common/convert-skills.py

# Шаг 3: Разложить symlinks во все CLI
cd ~/cli-common && bash deploy.sh
```

**Что делает convert-hermes-to-unified.py:**
- Сканирует `~/.hermes/skills/` рекурсивно (включая вложенные категории)
- Читает frontmatter (name, description, tags) и body из каждого SKILL.md
- Генерирует `~/cli-common/skills/<name>/skill.yaml` с секциями для:
  - **claude:** tools + model + permissionMode
  - **opencode:** mode: subagent, temperature: 0.2
  - **cursor:** readonly, is_background
  - **hermes:** исходный контент обратно
- Копирует supporting files (references/, templates/, scripts/, assets/)
- Пропускает Hermes-специфичные скиллы (plan, subagent-driven-development и т.д.)
- Защита от дубликатов имён

**Результат:** один запуск = все скиллы доступны во всех CLI-инструментах.

## Рабочий процесс

### Добавить MCP сервер
1. Отредактировать `~/cli-common/mcp/mcp-source.json`
2. Запустить `deploy.sh` — автоматом раскладывает во все 4 инструмента

### Создать новый скилл (единый формат — рекомендуется)

```bash
mkdir -p ~/cli-common/skills/my-skill
```

Создать `skill.yaml`:

```yaml
description: "Проверяет код на качество"
tags: ["code-review"]

# Общее тело — вставляется во все форматы
body: |
  Ты — старший ревьюер кода.
  Формат ответа: [CRITICAL], [WARNING], [SUGGESTION].

# Секция для Claude Code (опционально)
claude:
  tools: "Read, Grep, Glob, Bash"
  model: "sonnet"
  permissionMode: "dontAsk"

# Секция для Cursor (опционально)
cursor:
  readonly: false
  is_background: false

# Секция для OpenCode (опционально)
opencode:
  mode: "subagent"
  temperature: 0.1
  steps: 15

# Секция для Hermes (опционально — создаёт SKILL.md)
hermes:
  tags: ["code-review"]
  content: |
    # Code Reviewer
    Инструкции для Hermes агента...
```

Потом:
```bash
convert-skills.py my-skill   # -> agents/my-skill.md + hermes skills/my-skill/SKILL.md
deploy.sh                     # -> symlink во все CLI
```

### Добавить агента (быстрый путь — .md напрямую)
1. Положить .md файл в `~/cli-common/agents/`
2. Запустить `deploy.sh`
3. Агент появляется во всех CLI-инструментах (symlink)

### Новый проект
```bash
cd ~/projects/active/my-project
ln -s ~/cli-common/AGENTS.md ./AGENTS.md
# Добавить проект-специфичные правила в AGENTS.md ниже общих
```

## AGENTS.md стратегия

- `~/cli-common/AGENTS.md` — общие правила (user preferences, conventions, env vars)
- Проектный `AGENTS.md` — symlink на общий + проект-специфичные дополнения
- Если проекту нужен уникальный контекст — break symlink, скопировать файл и добавить своё
- Claude Code читает `CLAUDE.md`, не `AGENTS.md` — нужен symlink: `ln -s AGENTS.md CLAUDE.md`
- Cursor использует `.cursorrules` — отдельный формат

## Форматы MCP по инструментам (auto-deploy)

| Инструмент | Где конфиг | Механизм deploy.sh |
|---|---|---|
| Cursor | ~/.cursor/mcp.json | Symlink на mcp-source.json |
| Claude Code | ~/.claude.json (mcpServers) | jq merge (мерж с существующими) |
| OpenCode | ~/.config/opencode/opencode.json (mcp секция) | Python merge (конвертация формата) |
| Hermes | ~/.hermes/config.yaml (mcp_servers секция) | Python YAML writer |

deploy.sh обрабатывает разные форматы:
- Cursor/Claude: command + args (stdio)
- OpenCode: command как массив строк + type: local/http
- Hermes: command как строка конкатенация
- HTTP-серверы (web-search-prime, zread): type: http во всех поддерживающих

## Pitfalls

- **Project-специфичные AGENTS.md** — deploy.sh НЕ перезаписывает существующие файлы. Если symlink не встал — значит там уже был свой AGENTS.md.
- **Claude Code читает CLAUDE.md**, а не AGENTS.md — нужно или symlink, или дублировать.
- **Cursor использует .cursorrules** — отдельный формат, не поддерживает AGENTS.md.
- **symlink может не работать** — некоторые старые версии CLI не читают симлинки.
- **git init в ~/cli-common/** — рекомендуется для версионирования.
- **agy не поддерживает файловые конфиги** — саб-агенты только динамические через /goal, MCP не конфигурируется через файлы.
- **Несколько Google аккаунтов в agy** — см. `references/agy-multi-account.md`. Используй `CLOUDSDK_CORE_ACCOUNT=email agy` в каждой сессии или HOME-изоляцию.

## Kimi Code provider config

См. `references/kimi-code-provider-config.md` — добавление custom провайдеров (Volcengine Coding Plan и др.) в kimi-code v0.14.3. Ключевой питфолл: kimi-code не принимает `type = "openai_legacy"`, только `type = "openai"`.