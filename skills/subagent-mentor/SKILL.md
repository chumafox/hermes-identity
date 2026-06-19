---
name: subagent-mentor
description: "Интерактивное обучение настройке саб-агентов в CLI-инструментах: Claude Code, OpenCode, Hermes, Antigravity, Cursor. Пошагово: конфигурация, делегирование, мониторинг, практика."
tags: ["autonomous-ai-agents"]
---

# Subagent Mentor

Интерактивное обучение настройке саб-агентов в CLI-средах.

## Структура обучения (4 фазы)

### Фаза 0: Определение инструмента
Спросить через clarify какой CLI-инструмент пользователь хочет настроить:
- Claude Code
- OpenCode
- Hermes Agent (уже работает -- но можно улучшить)
- Antigravity CLI (agy)
- Cursor CLI

### Фаза 1: Конфигурация саб-агентов
Объяснить где создаются файлы, формат, обязательные поля.

### Фаза 2: Безопасность и permissions
Ограничение инструментов, принцип минимальных прав.

### Фаза 3: Делегирование
Автоматическое vs явное, параллельное выполнение.

### Фаза 4: Мониторинг
Как отслеживать прогресс, TUI-оверлеи, Todo-листы.

После каждой фазы -- clarify(choices=["да", "нет"]) -- спросить "продолжить?".

---

## Claude Code

### Конфигурация
- Файлы: `.claude/agents/` (проектные) или `~/.claude/agents/` (глобальные)
- Формат: Markdown + YAML frontmatter
- Обязательные поля: name (kebab-case), description
- Опционально: tools, model (haiku/sonnet/opus/inherit), permissionMode, memory, isolation, color, effort, initialPrompt

### Пример code-reviewer
```markdown
---
name: code-reviewer
description: Proactively reviews code for quality, security, and maintainability.
tools: Read, Grep, Glob, Bash
model: sonnet
permissionMode: dontAsk
---
You are a senior code reviewer. Focus on security, performance, maintainability.
```

### Делегирование
- Автоматическое: по полю description
- Явное: @code-reviewer проверь этот PR

### Мониторинг
- claude agents -- Agent View (полноэкранный)
- TodoWrite/TodoRead -- трекинг задач в сессии
- /cost -- затраты

---

## OpenCode

### Конфигурация
- Файлы: opencode.json / opencode.jsonc (глобальный или проектный)
- Или Markdown в ~/.config/opencode/agents/ / .opencode/agents/
- Primary agent: mode: "primary"
- Subagent: mode: "subagent" + description
- Поля: tools, model, temperature, steps, permissions

### Пример
```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices",
      "mode": "subagent",
      "tools": { "write": false, "edit": false }
    }
  }
}
```

### Permissions (безопасность)
- allow / ask / deny для каждого инструмента
- Glob-паттерны: "bash": {"git status *": "allow", "git push": "ask"}
- permission.task -- запрет каскадного вызова агентов

### Pitfall: формат tools
OpenCode ожидает `tools` как объект (`{read: true, write: false}`), а не как строку (`Read, Write` — как в Claude Code/Cursor).
Если шарить .md агент между CLI через symlink — OpenCode упадёт с "Expected object | undefined".
Решение: deploy.sh должен конвертировать формат для OpenCode, а для Claude/Cursor — symlink.

### Делегирование
- @explore найди утечки -- явный вызов
- Автоматический -- по description

### Мониторинг
- TUI-навигация: <Leader>+Down в сессию суб-агента
- Right/Left -- переключение между суб-агентами
- Up -- возврат к оркестратору
- opencode-monitor -- отдельный дашборд

---

## Hermes Agent (наш контекст)

### Конфигурация
- Секция delegation: в ~/.hermes/config.yaml
- Параметры: max_concurrent_children (default 3), max_spawn_depth (default 1), orchestrator_enabled, child_timeout_seconds

### Делегирование
- delegate_task(goal, context, toolsets, role) -- основной инструмент
- Leaf role (default): не может делегировать дальше
- Orchestrator role: может создавать своих суб-агентов
- Важно: контекст передаётся явно -- суб-агент стартует tabula rasa

### Параллельное выполнение
- Batch mode: delegate_task(tasks=[...]) -- до 3 параллельно
- Toolsets: ["terminal", "file"] для кода, ["web"] для исследования

### Мониторинг
- /agents (alias /tasks) в TUI -- дерево, токены, стоимость
- SQLite kanban-доска: Triage -> Todo -> Ready -> In progress -> Blocked -> Done

### Pitfalls
- clarify заблокирован для leaf subagents -- не спрашивать пользователя
- Стоимость растёт мультипликативно при глубокой вложенности

---

## Antigravity CLI (agy)

### Ограничение
- Кастомные персистентные суб-агенты -- только Ultra Plan
- Базовые: бесплатно, но эфемерные

### Встроенные суб-агенты
- research -- навигация по codebase
- browser -- headless Chrome через MCP
- self -- клон оркестратора

### Делегирование
- /goal -- автономный режим: оркестратор сам декомпозирует задачу
- define_subagent -- создание временного кастомного агента
- Git worktree для изоляции файлов

### Мониторинг
- /agents -- TUI Agent Manager Panel
- Стрелки вверх/вниз -- выбор агента
- Enter -- Subagent Detail View (логи, вызовы инструментов)
- Esc -- возврат
- /tasks -- для фоновых bash-скриптов

---

## Cursor CLI

### Конфигурация
- Файлы: .cursor/agents/ (проектные) или ~/.cursor/agents/ (глобальные)
- Формат: Markdown + YAML frontmatter
- Поля: name, description, model, readonly, is_background

### Пример
```markdown
---
name: test-writer
description: Only for writing Jest unit tests
model: fast
readonly: false
is_background: true
---
You write comprehensive Jest tests.
```

### Изоляция файлов (критично!)
- Параллельные агенты = race condition => git worktree-toolbox
- Каждый агент в своём worktree на своей ветке
- Результаты => отдельные PR => без merge conflicts

### Делегирование
- Task tool внутри одного ответа для параллелизма
- Последовательные вызовы = последовательное выполнение

### Мониторинг
- Agents Window -- вкладки для каждого фонового процесса
- Переключение между вкладками без засорения основного чата

---

## Общие принципы (говорить в начале и в конце)

1. Один суб-агент = одна ответственность. Не смешивай роли.
2. Description -- самое важное поле. По нему принимается решение об автоматическом делегировании.
3. Принцип минимальных прав: Read-only агенту не нужен Write/Bash.
4. Изоляция контекста: суб-агент не видит историю родителя.
5. Модели: быстрая (haiku) для поиска, средняя (sonnet) для реализации, мощная (opus) для архитектуры.
6. Формат frontmatter различается между CLI: Claude/Cursor используют строку `tools: Read, Grep`, OpenCode требует объект `tools: {read: true, grep: true}`. При шаринге .md агентов между инструментами нужна конвертация.

## Процесс обучения

При загрузке скилла:

1. clarify(question="Какой CLI-инструмент?", choices=["Claude Code", "OpenCode", "Hermes Agent", "Antigravity CLI", "Cursor CLI"]) -- определить инструмент
2. clarify(question="Начинаем с конфигурации?", choices=["да", "нет"]) -- Фаза 1
   - Объяснить где создавать файлы, формат, обязательные поля
   - Показать пример
   - Спросить "попробуешь создать?" через clarify
3. clarify(question="Теперь безопасность и permissions?", choices=["да", "нет"]) -- Фаза 2
   - Объяснить принцип минимальных прав
   - Показать настройки tools/permissions
4. clarify(question="Делегирование -- автоматическое и явное?", choices=["да", "нет"]) -- Фаза 3
   - Объяснить @agent-name и авто-делегирование
   - Параллельное выполнение
5. clarify(question="Мониторинг -- как отслеживать?", choices=["да", "нет"]) -- Фаза 4
   - TUI-оверлеи, Todo, дашборды
6. В конце: clarify(question="Хочешь попрактиковаться на реальном примере?", choices=["да", "нет"])
   - Если да: предложить создать простого саб-агента
