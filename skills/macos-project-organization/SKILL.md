---
name: macos-project-organization
description: "Организация проектов и домашней директории на macOS: схема ~/projects/{active,archived,agent,env}, слияние дубликатов, очистка мусора."
tags: ["devops"]
---

# macOS Project Organization

Стандартная схема организации проекта на MacBook (для 1 пользователя).

## Целевая структура

```
~/projects/
├── active/       ← текущие рабочие проекты
│   ├── ai-ml/    ← ML/AI: модели, fine-tuning, STT/TTS
│   ├── audio/    ← аудио/DAW проекты
│   ├── ios/      ← Xcode проекты
│   ├── telegram/ ← боты, warmup, постинг
│   ├── trademyapple/ ← WP темы/сайты клиентов
│   ├── video/    ← видео-редакторы, motion
│   ├── voice/    ← voice notes, диктовка
│   ├── web/      ← SPA, landing, SEO инструменты
│   └── windboss/ ← SEO-аудит, клиентские работы
├── archived/     ← замороженные/устаревшие
│   ├── ru-de-translator/
│   ├── composer-2/
│   └── other/
├── agent/        ← ИИ-агенты и их инструменты
│   ├── hermes-identity
│   ├── codexai/
│   ├── opencode/
│   └── pm-claude-skills/
└── env/          ← virtual env чужие проектов

~/shelf/          ← только легкие GitHub-клоны (<200MB)
~/vendor/         ← внешние инструменты (SDK, CLI)
~/Documents/      ← docs, coursework, media, backups
~/Downloads/      ← НЕ трогать без запроса
```

## Merge rules (дубликаты)

| Было | Стало |
|------|-------|
| `~/AG` + `~/ANT` | `~/projects/active/trademyapple/` |
| `~/Fish*` x3 + `~/А` | `~/projects/active/windboss/` |
| `~/Cursor/*` | по категориям в active/ |
| `~/Studio/neurorank` | `~/projects/active/audio/` |

## Очистка

- Пустые папки в корне `~/`: удалять (`rmdir`)
- Мусор без `.git`/ценности: `~/node_modules/` глобальный, `postman/files`, `AGY`, `ghl`, `osacurus`, `v2rayN-windows-arm64`
- Windows-артефакты (`$RECYCLE.BIN`, `desktop.ini`): удалять
- Ярлыки Alfred/Quicksilver без actionable content: удалять

## Питфоллы

1. **Не удалять `~/Downloads/`** — там installer-ы и временные файлы, которые пользователь может ещё нуждаться. Всегда спрашивать.
2. **Не трогать `~/Library/`, `~/Applications/`** — системные.
3. **Копировать перед перемещением**: `cp -a` → проверить `ls` → `rm -rf` оригинала только после подтверждения.
4. **`env/` может быть вложенной**: `~/projects/env/env/*` → flatten в `~/projects/env/`.
5. **Не создавать категории "на будущее"** — только то, что уже есть. Пустые категории не нужны.

## Проверка после

```
find ~/projects -maxdepth 2 -type d | sort
ls -d1 ~/*/  # проверка корня
```
