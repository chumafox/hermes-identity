---
name: macos-project-organizer
description: Реорганизация проектов и папок на macOS — сканирование ~/, обнаружение дубликатов/пустых папок, deduplication, схема ~/projects/ + ~/Documents/. Использовать, когда пользователь просит «привести в порядок проекты» или «прочесать комп» по файловой структуре.
version: 1
author: hermes-agent
---

# macOS Project Organizer

Сканирует домашнюю директорию, классифицирует папки и разложет по схеме ~/projects/active|archived|agent + ~/Documents/audits|coursework|media.

## Target layout

```
~/projects/
├── active/       ← текущие рабочие проекты (СНГ, SaaS, iot)
├── archived/     ← законченное / замороженное
├── agent/        ← ИИ-агенты, Hermes, shelf-проекты
└── env/          ← виртуальные окружения (перенос из ~/env)

~/Documents/
├── audits/       ← все JSON/MD аудитов
├── coursework/   ← Course/, EDU
└── media/        ← личная медиа из ~/Downloads

~/vendor/         ← внешние бинарники-инструменты (google-cloud-sdk, v2rayN, JDownloader)
```

## Loose file cleanup (файлы в корне ~/)

Помимо директорий, в корне ~/ часто скапливаются разрозненные файлы (.py, .sh, .png, .md, .log, .zip и т.д.). Пользователь просит «разложить чтобы было красиво».

1. **SCAN ROOT FILES** — `ls -1aF ~/ | grep -v '^\\.' | grep -v '/$'` (только файлы, не dotfiles)
2. **CHECK SIZE FIRST** — `du -sh ~/*/ 2>/dev/null | sort -rh` — понять, что занимает место
3. **CHECK REFERENCES BEFORE MOVING** — перед перемещением скриптов проверить не ссылаются ли на них:
   ```bash
   grep -r "script-name" ~/.zshrc ~/.zshenv ~/.zprofile ~/.bashrc ~/.bash_profile 2>/dev/null
   ```
   Если не ссылаются — можно безопасно перемещать.
4. **IDENTIFY CATEGORIES** по расширению/типу:

   | Тип | Расширения | Папка назначения |
   |-----|-----------|-----------------|
   | Скрипты | `.py`, `.sh` | `~/scripts/` |
   | Скриншоты | `.png`, `.jpg`, `.jpeg` | `~/screenshots/` |
   | Документы | `.md`, `.txt`, `.pdf` | `~/docs/` |
   | Логи | `.log`, `last_seen.txt` | `~/logs/` |
   | Архивы | `.zip`, `.pkg`, `.crx`, `.dmg`, `.aria2` | `~/archives/` |
   | Аудиотесты | `.aiff`, `.wav`, `.mp3` | `~/audio-tests/` |
   | Остальное | `typescript`, `cookies.txt`, `request.json`, `QR.vncloc` | `~/misc/` |

   **Дополнительные категории для vendor-приложений:**

   | Тип | Примеры | Папка назначения |
   |-----|--------|-----------------|
   | Electron-приложение (сборка) | `package.json`, `*.compiled.jsc`, `vendor.js`, `index.html`, `bun.lock`, `package-lock.json` | `vendor/<app-name>/` |
   | Launcher-скрипт для приложения | `adrive-en.sh`, `doubao-en.sh` | `vendor/<app-name>/` |
   | Конфиг-бэкапы приложения | `doubao-backup/` (Local State.bak, Preferences.bak) | `vendor/<app-name>/` |
   | Документация по сети/прокси | `reverseproxy/` с `.md` файлами | `docs/<topic>/` |
   | Тяжёлые ML модели | `models-too-heavy/` (ollama, etc) | `projects/active/ai-ml/models/` |

5. **CREATE DIRS** — `mkdir -p ~/scripts ~/screenshots ~/docs ~/logs ~/archives ~/audio-tests ~/misc`
6. **MOVE** — `mv <file> <category>/` для каждой группы
7. **SKIP** — не трогать: macOS папки (Library, Applications, Desktop, Documents, Downloads, Movies, Music, Pictures, Public), уже организованные (Projects, cli-common, shelf, vendor, bin, gym), dotfiles, AGENTS.md symlink (системный, не трогать)
8. **FILE TYPE CHECK** — перед перемещением проверить `file <name>` на неочевидные форматы
9. **VERIFY** — после всех перемещений проверить что в ~/ остались только папки:
   ```bash
   ls -1apF ~/ | grep -v '^\\.' | grep -v '/$'
   # Должен показать только AGENTS.md@ (symlink)
   ```

## Шаги (по проектам)

1. **SCAN** — terminal: `find ~ -maxdepth 1 -type d ! -name '.*' ! -name '.' | sort`
   - Пропустить системные: Library, Applications, Music, Movies, Pictures, Public, Downloads, Desktop, Documents, .cache, .config, .npm, .cargo, .nvm, .ssh, .Trash, .hermes
   - Для каждого каталога: размер (`du -sh`), кол-во файлов (find | wc -l), наличие .git, краткое описание (ls head)

2. **CLASSIFY** — сопоставить со схемой:
   - `active/<project>` — любые рабочие проекты с кодом/документами
   - `agent/` — проекты про ИИ-агентов, Hermes-экосистему, shelf-клон
   - `archived/<project>` — замороженный код / старые версии
   - `audits/` — SEO/GEO аудиты JSON/MD (перенос из Fish*)
   - `env/` — папки с виртуальными окружениями
   - `vendor/` — глобальные инструменты

3. **DEDUP / MERGE** — перед переездом:
   - Дубликаты: AG + ANT (TrademyApple) → слить в `active/trademyapple`
   - Серии: Fish / Fish_1 / Fish_2 → `audits/fish` (все аудиты + примеры)
   - Отдельные папки-дубли рядом с основными (ANTIGRA vs opencode)

4. **EMPTY CLEANUP** — удалить пустые/зombie папки:
   - AGY, Postman, SAAS, Linked, geminicli, cd, Screen Studio Projects, Cursor_Claude_Code, osacurus, dwhelper, API

5. **MOVE** — mv с сохранением истории:
   - Сначала пустые, потом archived, потом active
   - symlink-ы только по явному запросу

6. **VERIFY** — после переезда:
   - `find projects/ -maxdepth 2 -type d | sort` — убедиться, что активные проекты на месте
   - Размер Projects/ <= бывший top-level суммарный

## Питфоллы

- Не трогать ~/Library/, ~/Applications/, ~/Documents-iCloud-симлинки без явного запроса
- node_modules внутри проектов ЛУЧШЕ оставлять рядом с проектом — не переносить в vendor
- env/ с путями внутри может сломать проекты — перемещать только копированием + проверкой активации
- iCloud Drive папки требуют отдельного внимания (возможные симлинки)
- Cursor IDE часто создаёт ~/Cursor/*/ с проектами внутри — при реорганизации content из ~/Cursor/*/ должен разматываться по appropriate категориям, оставляя саму Cursor как временную папку для чистки
- ~/Downloads/ часто содержит installer-ы и ISO, которые пользователь не хочет удалять — трогать только если явно указано
- `~/Projects` (с большой буквы на Case-Insensitive macOS) часто дублирует `~/projects` — при N+1 скан принять во внимание хэш+Caps; при merge сливать, не падать на одинаковое имя
- Bash loops with spaces in paths: не использовать `for d in */` + `$dir` в кавычках внутри цикла — терминал tool часто падает на `du "$dir"` если путь содержит пробелы. Вместо этого: `cd ~ && for d in DIRNAME; do ...` без кавычек, либо `find … -print0 | xargs -0`.
- При merge дубликатов: сначала `cp -a source/. dest/` (с trailing slash!), потом `ls dest`, только потом `rm -rf source`. Никогда не удалять источник до проверки.
- `~/shelf/` по факту может стать мусорной корзиной для непонятных клонов — реорганизация должна оставить там только легкие (<200MB) experiment-материалы. Heavy-вейight проекты (SeamlessM4T 839M, etc) → `~/projects/active/ai-ml/`.

## Скрипт

`scripts/scan_projects.sh` — сканирует `~/`, выводит `name|size|items|git|top_content` per line, отсортирован по размеру.

## References

См. `references/macos-project-inventory-2026-06.md` — полная инвентаризация этого дома с классификацией.