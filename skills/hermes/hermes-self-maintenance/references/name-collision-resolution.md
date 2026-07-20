# Name Collision: hermes-self-maintenance

## Ситуация

Скилл `hermes-self-maintenance` существует в двух местах:

| Путь | Тип | Когда появился |
|------|-----|----------------|
| `~/.hermes/skills/hermes-self-maintenance/` | Flat | Ранее (original) |
| `~/.hermes/skills/hermes/hermes-self-maintenance/` | Categorized | Позже (при категоризации) |

## Симптомы

- `skill_view(name='hermes-self-maintenance')` → AmbiguousSkillError (2 matches)
- `skill_view(name='hermes/hermes-self-maintenance')` → работает (categorized)
- `skill_manage(action='patch', name='hermes-self-maintenance')` → работает (редактирует flat)
- `skill_manage(action='write_file', name='hermes/hermes-self-maintenance')` → "skill not found"

## Решение для каждого инструмента

| Инструмент | Как вызывать |
|-----------|--------------|
| `skill_view` | `name='hermes/hermes-self-maintenance'` (qualified path) |
| `skill_manage` | `name='hermes-self-maintenance'` (bare name — редактирует flat, пишет файлы в categorized) |

## Причина расхождения

`skill_manage` ищет скиллы только в `~/.hermes/skills/<name>/` (flat layout) и не видит categorized-версии `~/.hermes/skills/<category>/<name>/`. Но при `write_file` физически создаёт файл в categorized-пути — вероятно, потому что Hermes загрузил categorized-версию в память и использует её `skill_dir`.

## Статус

Оба скилла содержат одинаковый SKILL.md (синхронизируются при патче flat, так как categorized был создан копированием). Рекомендуется удалить один из дубликатов — скорее всего flat, т.к. categorized лучше для организации.
