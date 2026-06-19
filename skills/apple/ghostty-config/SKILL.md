---
name: ghostty-config
description: Настройка Ghostty терминала на macOS — keybindings, опции, работа с не-Latin раскладками клавиатуры.
domain: apple
tags: [ghostty, terminal, keyboard-layout, macos, keybindings]
---

# Ghostty Config

Ghostty — терминал для macOS. Конфиг: `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`.

Перезагрузка конфига: `ghostty +reload-config` (или бинд `super+shift+,`).

## Keybindings

Формат:
```
keybind = trigger=action
```

**ВАЖНО**: между `trigger` и `action` НЕ должно быть пробелов. `ctrl+tab=next_tab` ✓, `ctrl+tab = next_tab` ✗ — выдаст `error.InvalidAction`.

Триггер: `[модификаторы]+клавиша`. Модификаторы: `shift`, `ctrl`, `alt`/`opt`, `super`/`cmd`. Клавиша — символ (Unicode codepoint) или именованная (Tab, Enter, Escape и т.д.).

### Важно: Ghostty матчит по символу, не по физической клавише

Ghostty использует **Unicode codepoint**, который генерирует нажатие, а не USB HID код клавиши. Это значит:

- В US раскладке клавиша `]` генерирует `]` → бинд `ctrl+]` срабатывает
- В русской ЙЦУКЕН та же физическая клавиша генерирует `ъ` → бинд `ctrl+]` **не срабатывает**

Решение: дублировать бинды для символов других раскладок. Ghostty поддерживает несколько биндов на один action.

### Способ 1 (предпочтительный): Named keys — работают в любой раскладке

Некоторые клавиши в Ghostty — **named keys**, матчатся по USB HID коду (физической клавише), а не по символу. Они работают одинаково во всех раскладках.

Известные named keys: `Tab`, `Enter`, `Escape`, `Backspace`, `Space`, `PageUp`, `PageDown`, `Home`, `End`, `ArrowLeft`, `ArrowRight`, `ArrowUp`, `ArrowDown`, `F1`–`F24`, `Digit_0`–`Digit_9` (основной ряд), `Numpad*`, и т.д.

```
keybind = ctrl+tab=next_tab
keybind = ctrl+shift+tab=previous_tab
keybind = ctrl+pageup=previous_tab
keybind = ctrl+pagedown=next_tab
```

### Способ 2 (fallback): дублирование для не-Latin раскладок

Если нужной named key нет, дублировать бинды для символов других раскладок. Ghostty поддерживает несколько биндов на один action.

```
# English layout
keybind = super+shift+]=next_tab
keybind = super+shift+[=previous_tab
# Russian layout (ъ/х = физические клавиши ]/[ в ЙЦУКЕН)
keybind = super+shift+ъ=next_tab
keybind = super+shift+х=previous_tab
```

### Маппинг US → Russian (ЙЦУКЕН) для символьных клавиш

| US | Russian | Shift+Russian |
|----|---------|---------------|
| `[` | `х` | `Х` |
| `]` | `ъ` | `Ъ` |
| `;` | `ж` | `Ж` |
| `'` | `э` | `Э` |
| `,` | `б` | `Б` |
| `.` | `ю` | `Ю` |

Бинд пишется с символом **без shift** (базовый символ клавиши). Shift указывается как модификатор отдельно.

## TERM compatibility

Ghostty выставляет `TERM=xterm-ghostty` — это корректно для локальной работы, но **терминфо записи `xterm-ghostty` нет** на большинстве удалённых машин (серверы, headless Mac, Linux VPS). `clear`, `less`, `top`, `htop` и другие terminfo-зависимые команды падают с `'xterm-ghostty': unknown terminal type.`.

**Решение при SSH/ET:** переопределить TERM для команды подключения:
```bash
TERM=xterm-256color ssh user@host
# или в alias:
alias myserver='TERM=xterm-256color ssh user@host'
```

**Решение при ET (Eternal Terminal):**
```bash
TERM=xterm-256color et remote
```

**Альтернатива:** доставить terminfo для xterm-ghostty на удалённую машину:
```bash
# На удалённой машине (если есть доступ)
infocmp xterm-256color | ssh user@host "tic -x -"
```

## Pitfalls

- **Пробелы в keybind**: `keybind = trigger = action` — **ошибка**. Правильно: `keybind = trigger=action`. Пробелы ДО и ПОСЛЕ первого `=` — ок, пробелы между trigger и вторым `=` — ошибка.
- **Символы с Shift**: бинд пишется с базовым символом (без shift). `super+shift+]` = Super + Shift + клавиша, чей базовый символ `]`. Не путать — `]` уже требует Shift на некоторых раскладках, но в Ghostty это просто символ клавиши без модификатора.
- **Не все клавиши — named keys**: `Tab`, `Enter` и т.д. — да. `[`, `]`, `;` — символьные, матчатся по Unicode. На US клавиатуре разницы нет, на не-Latin — критично.
- **Дублирование**: Named keys (Tab, PageUp, F-клавиши) работают во всех раскладках без дублирования.

## Linked files

- `references/russian-layout-keybindings.md` — детали по работе с русской раскладкой и маппинг символьных клавиш
