---
name: multi-cli-config
description: "Centralise and deploy shared configuration (agents, MCP, AGENTS.md) across multiple CLI AI agents: Claude Code, OpenCode, Cursor, agy, and Hermes. Symlink-based single source of truth with a deploy script."
tags: [cli, config, agents, mcp, claude-code, opencode, cursor, agy, hermes]
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

| Инструмент | Агенты | MCP | Провайдеры |
|---|---|---|---|
| Claude Code | symlink | jq merge в ~/.claude.json | — |
| OpenCode | symlink | вручную в opencode.json | — |
| Cursor | symlink | symlink ~/.cursor/mcp.json | — |
| agy | dynamic (/goal) | N/A | — |
| Hermes | своя система (skills) | config.yaml | config.yaml (custom_providers) |
| Kimi CLI | `agents/*.md` → `~/.config/kimi/agents/` | `--mcp-config-file` | `~/.kimi/config.toml` секция `[[providers]]` |

### Инициализация `~/.kimi/config.toml` на новом Mac

```bash
# Установка
uv tool install kimi-cli

# Первый запуск создаёт файл по умолчанию
kimi --version
# Выведет версию и создаст ~/.kimi/config.toml
```

### Два бинарника: старый kimi vs kimi-code

Начиная с v0.14.x, Kimi CLI переименован в **kimi-code**. Возможна ситуация, когда:

- Старый бинарник `~/.kimi/bin/kimi` — может быть удалён или не обновляться
- Новый бинарник `~/.kimi-code/bin/kimi` — актуальная версия
- Конфиги раздельные: `~/.kimi/config.toml` (старый) vs `~/.kimi-code/config.toml` (новый)
- В PATH должен быть `~/.kimi-code/bin`

**При переустановке/обновлении:** проверь какой бинарник реально используется. Старый конфиг может содержать провайдеров, которых нет в новом.

Проверить:
```bash
which kimi
~/.kimi-code/bin/kimi --version
~/.kimi-code/bin/kimi provider list
~/.kimi-code/bin/kimi doctor
```

### Поддерживаемые типы провайдеров в `config.toml`

| type | Описание | Версия |
|---|---|---|
| `kimi` | Kimi API (managed:kimi-code, moonshot.cn) | все |
| `openai` | OpenAI Chat Completions / совместимые (Volcengine Coding) | kimi-code v0.14+ |
| `openai_legacy` | OpenAI Chat Completions (старый формат) | **устарел** в v0.14.3+ |
| `openai_responses` | OpenAI Responses API | kimi-code |
| `anthropic` | Anthropic Claude | kimi-code |
| `gemini` / `vertexai` | Google Gemini / Vertex AI | kimi-code |

**Важно:** `openai_legacy` невалиден в kimi-code v0.14.3+. Используй `openai`. `kimi doctor` покажет `providers.xxx.type: Invalid input`.

### Миграция провайдеров из старого конфига в kimi-code

Старый `~/.kimi/config.toml` и новый `~/.kimi-code/config.toml` — **разные файлы**. Если провайдер (volc-coding и т.п.) был настроен в старом, в новом его нет.

**Процедура добавления провайдера в kimi-code:**

1. Добавить секцию `[providers.<name>]` в `~/.kimi-code/config.toml`
2. Добавить `[models."<name>/<model>"]` для каждой модели
3. Проверить: `kimi doctor` — должен быть OK
4. Подтвердить: `kimi provider list` — новый провайдер должен появиться

**Типичная ошибка:** скопировать секцию `[providers.volc-coding]` из старого конфига, где `type = "openai_legacy"`. В kimi-code v0.14.3+ это Invalid input. Фикс: заменить на `type = "openai"`.

**Имена моделей с точками** в TOML требуют кавычек: `[models."volc-coding/deepseek-v4-flash"]`.

### Пример: Volcengine Coding

```toml
[providers.volc-coding]
type = "openai"
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
api_key = "ark-..."

[models."volc-coding/deepseek-v4-flash"]
provider = "volc-coding"
model = "deepseek-v4-flash"
max_context_size = 102400
capabilities = ["thinking", "image_in"]
display_name = "DeepSeek V4 Flash (Volc)"
```

**Ключевые моменты:**
- Имена моделей с точками в TOML — в кавычках: `[models."provider/model"]`
- `type = "openai"` (не `openai_legacy`) для kimi-code v0.14+
- После добавления — проверить: `kimi doctor` (OK) и `kimi provider list` (новый провайдер виден)

### `/login` shortcut

В интерактивном режиме Kimi CLI поддерживает `/login` (alias `/setup`):
1. Select an API platform → Kimi Code / Moonshot AI
2. Enter API key
3. Select model from list

Для нестандартных провайдеров (Volcengine, etc.) — редактировать config.toml вручную.

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
