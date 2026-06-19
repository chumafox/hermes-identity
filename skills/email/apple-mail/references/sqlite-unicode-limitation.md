# SQLite LIKE с Unicode/кириллицей/эмодзи — не работает

## Проблема

`WHERE sj.subject LIKE '%паттерн%'` с кириллицей, эмодзи (🚀, 🎉, ✅) или спецсимволами ([GitHub]) возвращает **0 результатов**, даже если письма с такими темами есть в базе.

## Причина

SQLite collation по умолчанию (BINARY) сравнивает байты. Для ASCII это ок, но для многобайтовых символов (UTF-8 кириллица, эмодзи) сравнение ломается. COLLATE NOCASE на `addresses.address` есть, но на `subjects.subject` — COLLATE RTRIM (только trim пробелов справа, без регистра/юникода).

## Что работает

- `sj.subject = 'Точное совпадение'` — работает
- `sj.subject LIKE '%GitHub%'` — работает (ASCII)
- `sj.subject LIKE '%100%'` — работает (цифры)
- `sj.subject LIKE ''` — работает (пустая строка)

## Что НЕ работает

- `sj.subject LIKE '%Чукреева%'` — 0 результатов (кириллица)
- `sj.subject LIKE '%验证码%'` — 0 результатов (китайские иероглифы)
- `sj.subject LIKE '%🍩%'` — 0 результатов (эмодзи)

## Обход

1. Выгрузить все темы через `SELECT sj.subject` в Python
2. Фильтровать в Python через `if pattern in subject.lower()`
3. Удалять через osascript (osascript `contains` корректно работает с Unicode)

## Проверка

```bash
# Этот запрос вернёт 0, хотя письма с Чукреева есть
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT COUNT(*) FROM messages m
JOIN subjects sj ON m.subject = sj.ROWID
WHERE m.mailbox = 48 AND sj.subject LIKE '%Чукреева%';
"

# А этот покажет все темы — фильтруй в Python
sqlite3 ~/Library/Mail/V10/MailData/Envelope\ Index "
SELECT sj.subject FROM messages m
JOIN subjects sj ON m.subject = sj.ROWID
WHERE m.mailbox = 48 AND m.deleted = 0;
" | python3 -c "import sys; [print(l.strip()) for l in sys.stdin if 'чукреева' in l.lower()]"
```
