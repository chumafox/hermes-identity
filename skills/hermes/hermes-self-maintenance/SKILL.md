---
name: hermes-self-maintenance
description: Поддержка identity-файлов (SOUL.md, AGENTS.md, soul.md, memory), git-бэкап, cron-синхронизация
tags: [identity, git, backup, cron, auto-sync]
related_skills: []
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

## Проактивное управление памятью (memory compaction)

Память лимитирована (2,200 символов). Когда она заполнена, новые добавления падают с ошибкой `Memory at X/2,200 chars`. Чтобы этого избежать:

1. **Заменяйте, а не добавляйте** — при каждом добавлении проверяй, можно ли заменить существующую запись вместо добавления новой. Используй `action: "replace"` с `old_text` для поиска.
2. **Сжимайте похожие записи** — если два факта можно объединить в один (например, "предпочитает X" + "не использует Y" → один абзац), сделайте replace одной записи расширенной версией и удалите вторую.
3. **Переносите процедурные знания в skills** — если memory содержит инструкции вида "как делать X", это сигнал, что X должен быть skill'ом. Создайте skill и удалите запись из памяти.
4. **Проверяйте актуальность** — записи о завершённых задачах, временных путях, session-specific деталях подлежат удалению при compaction.
5. **Не копируйте system prompt в memory** — правила "всегда делать X", "никогда не делать Y" уже есть в system prompt. Если пользователь их повторил, это reinforcement, а не новый факт.

Когда память заполнена >90%, действуйте проактивно: просмотрите все записи, найдите кандидатов на объединение/удаление и освободите 200+ символов.

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

## Правило автоматизации

**Пользователь требует:** рутинные/повторяющиеся задачи НЕ делать руками.
Сразу создавать скрипт или skill. Это экономит токены и время.
Сигнал: пользователь сказал "создай скрипт" или сделал однотипное действие дважды.
