---
name: apple-mail
description: "Управление Apple Mail.app через osascript (AppleScript) — отправка, чтение, поиск писем из терминала. Не требует установки сторонних CLI."
tags: [email, mail, macos, applescript, osascript, imap, smtp]
---

# Apple Mail.app via osascript

Управление Apple Mail.app через `osascript` — без установки сторонних CLI (himalaya и т.д.). Работает на macOS с настроенным аккаунтом в Mail.app.

## Prerequisites

- Mail.app должен быть настроен хотя бы с одним аккаунтом
- Для отправки: Mail.app может быть закрыт (система сама запустит фоновый процесс отправки)

## Проверка аккаунтов

```bash
osascript -e '
tell application "Mail"
    set accs to every account
    set resultList to ""
    repeat with acc in accs
        set resultList to resultList & name of acc & " | " & (get account type of acc) & return
    end repeat
    return resultList
end tell
'
```

## Получение адресов аккаунта

```bash
osascript -e '
tell application "Mail"
    set acc to account "iCloud"
    set emailAddrs to email addresses of acc
    set addrList to ""
    repeat with addr in emailAddrs
        set addrList to addrList & addr & return
    end repeat
    return addrList
end tell
'
```

## Отправка письма

### Быстрая отправка

```bash
osascript -e '
tell application "Mail"
    set newMsg to make new outgoing message with properties {subject:"Тема письма", content:"Текст письма" & return & return}
    tell newMsg
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
        set sender to "your@email.com"
    end tell
    send newMsg
end tell
'
```

### Создать, показать для проверки, потом отправить

Полезно когда нужно дать пользователю проверить письмо перед отправкой:

```bash
# Шаг 1 — создать и показать
osascript -e '
tell application "Mail"
    set newMsg to make new outgoing message with properties {sender:"chumafox@me.com", subject:"Тема", content:"Текст"}
    tell newMsg
        set visible to true
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
    end tell
end tell
'

# Шаг 2 — после подтверждения пользователя, отправить
osascript -e '
tell application "Mail"
    set newMsg to make new outgoing message with properties {sender:"chumafox@me.com", subject:"Тема", content:"Текст"}
    tell newMsg
        make new to recipient at end of to recipients with properties {address:"recipient@example.com"}
        send
    end tell
end tell
'
```

### Закрыть все окна Mail.app

```bash
osascript -e 'tell application "Mail" to close every window'
```

## Чтение входящих (последние N писем)

```bash
osascript -e '
tell application "Mail"
    set inboxMessages to messages of inbox
    set msgCount to count of inboxMessages
    if msgCount > 5 then set msgCount to 5
    set output to ""
    repeat with i from 1 to msgCount
        set msg to item i of inboxMessages
        set output to output & "From: " & sender of msg & return
        set output to output & "Subject: " & subject of msg & return
        set output to output & "Date: " & date received of msg & return
        set output to output & "---" & return
    end repeat
    return output
end tell
'
```

## Поиск писем

```bash
osascript -e '
tell application "Mail"
    set matchingMessages to (messages of inbox whose subject contains "keyword")
    set output to ""
    repeat with msg in matchingMessages
        set output to output & subject of msg & " — " & sender of msg & return
    end repeat
    return output
end tell
'
```

## Проверка версии Mail.app

```bash
osascript -e 'tell application "Mail" to get version'
```

## SQLite Direct Access (быстрый анализ больших почтовых ящиков)

osascript `messages of inbox` на 2000+ писем таймаутится. Для быстрого анализа используй прямые SQLite запросы к Envelope Index.

### База

```bash
# Путь
~/Library/Mail/V10/MailData/Envelope\ Index
```

### Ключевые таблицы

| Таблица | Назначение |
|---------|-----------|
| `mailboxes` | Почтовые ящики: url (содержит GUID аккаунта), total_count, unread_count |
| `messages` | Письма: mailbox (FK), subject (FK), sender (FK), read, date_received |
| `subjects` | Темы писем: subject |
| `senders` | Отправители: contact_identifier (UUID:ABPerson) |
| `addresses` | Email адреса: address, comment |
| `sender_addresses` | Связь sender → address (sender, address — обе FK) |

### Привязка mailbox к аккаунту

GUID в url mailbox совпадает с id аккаунта в Mail.app:

```bash
# Узнать id аккаунтов
osascript -e 'tell application "Mail" to set accs to every account
repeat with acc in accs
    return name of acc & " | id: " & id of acc
end tell'

# Найти mailbox по GUID
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT ROWID, url, total_count, unread_count
FROM mailboxes WHERE url LIKE '%<GUID>/INBOX%';
"
```

### Полезные запросы

```bash
# Топ отправителей по количеству писем в ящике
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT a.address, COUNT(*) as cnt
FROM messages m
JOIN senders s ON m.sender = s.ROWID
JOIN sender_addresses sa ON s.ROWID = sa.sender
JOIN addresses a ON sa.address = a.ROWID
WHERE m.mailbox = <MAILBOX_ID>
GROUP BY a.address
ORDER BY cnt DESC
LIMIT 30;
"

# Топ тем (сгруппировано)
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT sj.subject, COUNT(*) as cnt
FROM messages m
JOIN subjects sj ON m.subject = sj.ROWID
WHERE m.mailbox = <MAILBOX_ID>
GROUP BY sj.subject
ORDER BY cnt DESC
LIMIT 50;
"

# Непрочитанные письма
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT COUNT(*) FROM messages
WHERE mailbox = <MAILBOX_ID> AND read = 0;
"

# Все mailbox с количеством писем
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT ROWID, url, total_count, unread_count
FROM mailboxes ORDER BY total_count DESC;
"
```

### Поиск писем по теме для удаления

```bash
# Найти ROWID писем по паттерну темы
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT m.ROWID, sj.subject, m.date_received
FROM messages m
JOIN subjects sj ON m.subject = sj.ROWID
WHERE m.mailbox = <MAILBOX_ID>
  AND sj.subject LIKE '%спам%'
ORDER BY m.date_received DESC;
"
```

### Удаление писем через SQLite

Mail.app использует `deleted` флаг (не физическое удаление):

```bash
# Пометить как удалённые
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
UPDATE messages SET deleted = 1
WHERE mailbox = <MAILBOX_ID>
  AND subject IN (SELECT ROWID FROM subjects WHERE subject LIKE '%спам%');
"
```

После этого нужно запустить Mail.app, чтобы он синхронизировал удаление с сервером (или через osascript `delete`).

## Массовое удаление спама по теме письма

Удаление большого количества писем (500+) через osascript — нетривиальная задача из-за ограничений AppleScript.

### Проблемы AppleScript при массовом удалении

1. **`messages of inbox`** — крайне медленный на 1000+ писем. Для анализа используй SQLite.
2. **Удаление в прямом цикле** — сдвигает индексы, пропускает письма.
3. **`message id X of inbox`** — не работает с отрицательными message_id (~50% писем).
4. **Длинный список паттернов** (>30-40 элементов) вызывает syntax error.
5. **JXA (JavaScript for Automation)** — ненадёжен с Mail.app, часто возвращает 0 удалённых.
6. **Чтение паттернов из файла** через `open for access` — тоже ненадёжно.

### Рабочий подход: обратный проход + группы паттернов

Единственный надёжный способ — разбить паттерны на группы по ~30, итерировать письма **в обратном порядке** (от msgCount к 1):

```python
import subprocess

pattern_groups = [
    ["паттерн1", "паттерн2", ...],  # ~30 штук
    ["паттерн31", "паттерн32", ...],
]

def make_script(patterns):
    items = "{" + ", ".join(f'"{p}"' for p in patterns) + "}"
    return f'''
set patternList to {items}
tell application "Mail"
    set msgs to messages of inbox
    set msgCount to count of msgs
    set totalDeleted to 0
    repeat with i from msgCount to 1 by -1
        set msg to item i of msgs
        set msgSubject to subject of msg
        set shouldDelete to false
        if msgSubject is "" then
            set shouldDelete to true
        else
            repeat with p in patternList
                if msgSubject contains p then
                    set shouldDelete to true
                    exit repeat
                end if
            end repeat
        end if
        if shouldDelete then
            delete msg
            set totalDeleted to totalDeleted + 1
        end if
    end repeat
    return totalDeleted
end tell
'''

for group in pattern_groups:
    result = subprocess.run(["osascript", "-e", make_script(group)],
                          capture_output=True, text=True, timeout=600)
```

### Порядок действий для очистки

1. **Анализ через SQLite** — быстрый, без таймаутов
2. **Формирование списка паттернов** — на основе топ-тем из SQLite
3. **Разбивка на группы по ~30 паттернов**
4. **Запуск osascript с обратным проходом** для каждой группы
5. **Проверка остатка** через SQLite `SELECT COUNT(*) FROM messages WHERE mailbox = <ID> AND deleted = 0`

### Готовый скрипт

См. `references/mass-delete-patterns.py` — полный скрипт с 7 группами паттернов (~200 паттернов), покрывающий русский маркетинг, realty-спам, GitHub уведомления, квитанции Apple, проверочные коды, китайские сервисы и generic spam. Запуск:

```bash
python3 ~/.hermes/skills/email/apple-mail/references/mass-delete-patterns.py
```

**Перед запуском:** обнови `MAILBOX_ID` в скрипте (узнать через `SELECT ROWID, url FROM mailboxes WHERE url LIKE '%INBOX%'`).

**После каждого запуска:** проверь остаток через SQLite и покажи пользователю список оставшихся тем. Он решит, что ещё удалять.

**При следующей чистке:** обнови список паттернов через SQLite топ-тем.

### Пример: получение топ-тем для формирования паттернов

```bash
sqlite3 ~/Library/Mail/V10/MailData/Envelope\\ Index "
SELECT sj.subject, COUNT(*) as cnt
FROM messages m
JOIN subjects sj ON m.subject = sj.ROWID
WHERE m.mailbox = <MAILBOX_ID> AND m.deleted = 0
GROUP BY sj.subject
ORDER BY cnt DESC
LIMIT 100;
"
```

### ⚠️ SQLite LIKE с Unicode/кириллицей/эмодзи — НЕ РАБОТАЕТ

`WHERE sj.subject LIKE '%паттерн%'` с кириллицей, эмодзи или спецсимволами (проверочный код, 验证码, 🚀, [GitHub]) возвращает **0 результатов**, даже если письма с такими темами есть. Это известное ограничение SQLite collation для не-ASCII.

**Не трать время на SQLite LIKE для фильтрации.** Используй SQLite ТОЛЬКО для:
- Подсчёта `COUNT(*)`
- Выгрузки всех тем (`SELECT sj.subject`) — потом фильтруй в Python
- Поиска mailbox ID

**Для удаления используй osascript с обратным проходом** (см. раздел выше). Паттерны для osascript пиши в оригинальном регистре (как они выглядят в письме), osascript `contains` корректно работает с Unicode.

### ⚠️ `message id X of inbox` не работает с отрицательными ID

~50% писем имеют отрицательный `message_id`. AppleScript `message id X of inbox` выбрасывает ошибку для таких ID. Единственный надёжный способ удаления — **итерация всех писем** с обратным проходом (`repeat with i from msgCount to 1 by -1`), а не обращение по ID.

### ⚠️ Безопасность паттернов

Широкие паттерны (например, "ученица", "скидка", "купить", "бесплатно", "доход", "бизнес", "курс", "результат", "секрет", "советы") удаляют важные письма — квитанции, security-уведомления, личные сообщения, письма от госорганов.

**Правило:** каждый паттерн должен быть достаточно специфичным, чтобы не зацепить:
- Письма с кодами подтверждения (OpenAI, GitHub, банки)
- Квитанции и чеки
- Личные сообщения
- Уведомления от сервисов, которыми пользуешься
- Письма о визах, поездах, бронированиях
- Выписки по счетам (Lotusmiles, банки)
- Security-уведомления (Vercel, Supabase, npm)

**Лучше сделать 5-7 проходов с узкими паттернами, чем 1 проход с широкими.**

### Финальная верификация

После каждого раунда удаления:
1. Проверить остаток через SQLite `SELECT COUNT(*)`
2. Выгрузить оставшиеся темы
3. Показать пользователю — он может решить, что ещё удалить

Не удаляй всё подряд без показа пользователю. После 3-4 проходов остаётся ~100 писем, среди которых есть важное (визы, поезда, личные сообщения, security). Дальнейшее удаление — только по явному указанию пользователя.

### Стратегия многоэтапной очистки

1. **SQLite → выгрузка всех тем** → фильтр в Python → формирование узких паттернов
2. **Проход 1**: самые очевидные паттерны (конкретные рассылки, известные спамеры)
3. **Проверка остатка** через `SELECT COUNT(*)`
4. **Проход 2**: следующие группы паттернов по результатам проверки
5. **Повторять** пока не останутся только нужные письма
6. **Финальная проверка**: выгрузить оставшиеся темы, показать пользователю

### Формирование паттернов из SQLite

```python
import sqlite3, subprocess

# 1. Выгрузить все темы
conn = sqlite3.connect("~/Library/Mail/V10/MailData/Envelope Index")
cur = conn.cursor()
cur.execute("""
    SELECT sj.subject FROM messages m
    JOIN subjects sj ON m.subject = sj.ROWID
    WHERE m.mailbox = <ID> AND m.deleted = 0
""")
subjects = [row[0] for row in cur.fetchall()]
conn.close()

# 2. Отфильтровать мусор в Python
patterns = [s for s in subjects if any(spam_word in (s or "").lower() 
            for spam_word in ["чукреева", "вебинар", "распродаж"])]

# 3. Разбить на группы по ~30 и удалить через osascript
# (см. раздел "Рабочий подход" выше)
```

После каждого прохода перепроверяй остаток — не удалилось ли нужное.

## Особенности

- **iCloud аккаунт** может иметь несколько алиасов (me.com, icloud.com и др.) — все они доступны как `email addresses` аккаунта
- **Sender** нужно указывать явно, если аккаунт имеет несколько адресов
- Mail.app не обязательно должен быть открыт — `send` работает через фоновый процесс
- Для писем с китайскими/русскими символами кодировка определяется автоматически
- **osascript `messages of inbox`** — крайне медленный на 1000+ писем. Для анализа используй SQLite.
- **sender_addresses** таблица: колонки называются `sender` и `address` (не sender_id/address_id)
- **senders.contact_identifier** — UUID вида `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX:ABPerson`, не email. Email лежит в `addresses` через `sender_addresses`.
