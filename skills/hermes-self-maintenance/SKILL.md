---
name: hermes-self-maintenance
description: "Поддержка identity-файлов (SOUL.md, AGENTS.md, soul.md, memory), git-бэкап, cron-синхронизация"
tags: ["hermes"]
---

# Hermes Self-Maintenance

Поддерживает identity-файлы агента в актуальном состоянии и синхронизирует их с GitHub,
чтобы при переустановке Hermes на другом железе не пришлось переучивать агента.

## Как Hermes грузит identity

Система в `agent/prompt_builder.py`:

- **SOUL.md** — грузится из `~/.hermes/SOUL.md` в identity-слот system prompt **всегда**
- **AGENTS.md** — грузится из текущей рабочей директории (cwd)
- **.cursorrules / CLAUDE.md** — альтернативы cwd, если нет AGENTS.md

Поэтому identity держим в `~/.hermes/SOUL.md`, а дублируем в `~/hermes-identity/soul.md`.

## Файлы

Все в `~/hermes-identity/` (git-репозиторий, remote: `git@github.com:chumafox/hermes-identity.git`):

| Файл | Содержание | Куда грузится |
|------|-----------|---------------|
| `soul.md` | Личность, стиль, принципы, LLM-модели | → `~/.hermes/SOUL.md` |
| `AGENTS.md` | Копия личности (для cwd) | Из текущей папки |
| `memory-backup.md` | Слепок памяти: пользователь, железо, сеть, проекты | Не грузится автоматом |
| `hermes-backlog.md` | Полка задач | Не грузится |
| `.gitignore` | Игнор .env, .log, .DS_Store | — |
| `skills/` | Копии всех созданных навыков | — |
| `sync.sh` | Скрипт синхронизации | Запускается по крону |

## Когда обновлять identity-файлы

1. **Новый skill создан** — скопировать в `~/hermes-identity/skills/<name>/`
2. **Память (memory) обновилась** — обновить `memory-backup.md`
3. **Изменился стиль/принципы** — обновить `soul.md` → `~/.hermes/SOUL.md`
4. **Новое железо/сеть/провайдер** — добавить в `memory-backup.md`
5. **Пользователь сказал "создай скрипт / автоматизацию"** — сохранить как skill + скопировать
6. **По прямой команде пользователя** — запустить `~/hermes-identity/sync.sh`

## sync.sh — скрипт синхронизации

```bash
#!/bin/bash
IDENTITY_DIR="$HOME/hermes-identity"

# Copy identity files from Hermes home → repo
cp "$HOME/.hermes/SOUL.md" "$IDENTITY_DIR/soul.md" 2>/dev/null || true
cp -r "$HOME/.hermes/skills/" "$IDENTITY_DIR/skills/" 2>/dev/null || true

# Copy back from repo → Hermes home (for files loaded by Hermes)
cp "$IDENTITY_DIR/soul.md" "$HOME/.hermes/SOUL.md" 2>/dev/null || true

# Git operations
cd "$IDENTITY_DIR"
git add -A
if ! git diff --cached --quiet; then
  git commit -m "identity sync $(date +%Y-%m-%d_%H:%M)"
  git pull --rebase origin main 2>/dev/null
  git push
fi
```

## SSH-конфиг для GitHub (China-friendly)

В `~/.ssh/config`:

```
Host github.com
HostName ssh.github.com
Port 443
User git
IdentityFile ~/.ssh/id_ed25519_hermes
StrictHostKeyChecking no
```

Ключ `id_ed25519_hermes` добавлен в GitHub-аккаунт chumafox.

## Расписание синхронизации

**Экранный Mac (jenyanovak):** Hermes cron `identity-sync`, каждый день в 4:00
**Безголовый Mac (admin):** launchd `com.hermes.identity-sync`, каждый день в 4:05

На безголовом: `launchctl list | grep hermes`

## Аудит безопасности и конфигурации Hermes

Периодически проверять `approvals.mode` и связанные настройки — они определяют, какие операции агент может выполнять без вмешательства пользователя.

### Проверка статуса approvals

```bash
grep -A5 "approvals:" ~/.hermes/config.yaml
```

Режимы:
- `manual` — спрашивать перед опасными командами (по умолчанию)
- `smart` — LLM решает спрашивать или нет
- `off` / `false` — всё выполняется без вопросов

### Практические ограничения на macOS

С `approvals.mode: off` Hermes никогда не показывает approval-диалог. Но системная безопасность macOS остаётся:

| Барьер | Решение | Статус |
|--------|---------|--------|
| `sudo` на display Mac | Требует пароль macOS — Hermes его не знает | Блокер |
| `sudo` на headless Mac | `sshpass` с известным паролем | Работает |
| `rm -rf`, destructive | Больше не спрашивает | Снят |
| Любые обычные команды | Не спрашивал и раньше | ОК |

### Как проверить, что реально блокировало

Использовать `session_search` для поиска паттернов:
```
session_search(query="sudo пароль approve approval разрешение")
```

Это покажет, какие операции в истории ждали пользовательского ввода. На display Mac в практике блокировался только `sudo`.

### Когда включать/выключать approvals

- **off** — когда работа идёт быстро, пользователь рядом и понимает риски
- **manual** — при опасных операциях (удаление, перезапись) на production-подобных средах
- **smart** — золотая середина с LLM-фильтром

См. `references/approvals-audit.md` для истории проверок.

## Клонирование Hermes на другой Mac

Полная копия Hermes на другом Mac (той же версии). Нужно когда на втором Mac тоже должен работать агент с тем же identity.

**Условия:**
- Hermes той же версии уже установлен на целевом Mac
- SSH доступ (ключ id_ed25519_hermes) от исходного Mac к целевому
- На исходном Mac: обновлённые SOUL.md, AGENTS.md, config.yaml, skills

**Процедура (выполняется с исходного Mac):**

```bash
# 1. Сохранить backup существующего config.yaml на целевом Mac
ssh -i ~/.ssh/id_ed25519_hermes admin@<IP_целевого> \
  "cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup"

# 2. Скопировать identity и конфиг
scp -i ~/.ssh/id_ed25519_hermes \
  ~/.hermes/SOUL.md \
  ~/.hermes/AGENTS.md \
  ~/.hermes/config.yaml \
  admin@<IP_целевого>:~/.hermes/

# 3. Скопировать skills (rsync — не трогает curator_backups и скрытые файлы)
rsync -avz -e "ssh -i ~/.ssh/id_ed25519_hermes" \
  ~/.hermes/skills/ \
  admin@<IP_целевого>:~/.hermes/skills/

# 4. Проверить что Hermes работает с новым конфигом
ssh -i ~/.ssh/id_ed25519_hermes admin@<IP_целевого> \
  "hermes chat -q 'Привет, какой у тебя title из SOUL.md?'"
```

**Что копируется (~7-15MB):** SOUL.md, AGENTS.md, config.yaml, все skills
**Что НЕ копируется:** venv (~170-670MB), модели (~2-29GB), .env (API ключи)

**Примечания:**
- `.env` не трогать — на целевом Mac свои API ключи
- model.provider может различаться — проверить что deepseek работает с местным .env
- После копирования проверить: `hermes chat -q 'привет'` — должен ответить
- SOUL.md и AGENTS.md идентичны — агент на обоих Macах ведёт себя одинаково

**Когда нужно:**
- Настройка второго рабочего Mac с таким же агентом
- Восстановление identity после переустановки Hermes
- Делегирование задач между Mac

## Правило автоматизации

**Пользователь требует:** рутинные/повторяющиеся задачи НЕ делать руками.
Сразу создавать скрипт или skill. Это экономит токены и время.
Сигнал: пользователь сказал "создай скрипт" или сделал однотипное действие дважды.
