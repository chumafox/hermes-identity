# Аудит approvals.mode — история проверок

## 2026-05-28 — Первичный аудит

**Запрос:** "режим в Hermes — hermes config set approvals.mode off. уже активен?"

**Результат:** Да, `approvals.mode: false` уже установлен в `~/.hermes/config.yaml`.

### Полный конфиг approvals

```yaml
approvals:
  mode: false       # off — без подтверждений
  timeout: 60
  cron_mode: deny
  mcp_reload_confirm: true
  destructive_slash_confirm: true
command_allowlist:
- recursive delete
```

### Что означают режимы

Источник: `hermes-agent` skill → Security & Privacy Toggles → Command approval prompts:

- `manual` — всегда спрашивать (по умолчанию)
- `smart` — LLM-фильтр: auto-approve для низкорисковых, спросить для опасных
- `off` / `false` — всё без вопросов, эквивалент `--yolo`

### Что блокировалось в истории

Поиск через `session_search` по паттернам sudo/approve/approval/разрешение показал:

**Единственный реальный блокер:** `sudo` на display Mac (jenyanovak, HK).

Сессия 20260520: Установка Go через `sudo installer -pkg` — не сработало, пришлось спросить пароль.
Сессия 20260515: `sudo networksetup`, `sudo dscacheutil` — выполнялось напрямую (вероятно, passwordless sudo или пользователь уже ввёл пароль).
Сессия 20260523: `sudo profiles`, `sudo rm` на headless Mac — работало через `sshpass` (пароль известен).

**Не блокировалось:** brew install, pip install, mkdir, rm (нерекурсивное), kill, curl, git, любые обычные команды.

### Вывод

С `approvals.mode: off` Hermes никогда не показывает approval-диалог. Единственный
оставшийся барьер на display Mac — системный запрос пароля macOS для `sudo`.
На headless Mac `sudo` работает через `sshpass`.
