---
name: udemy-lecture-downloader
description: Скачивает лекции Udemy курсов через Hermes tools (browser_navigate → browser_console → terminal/curl)
category: web-automation
---

# Udemy Lecture Downloader

Скачивает видео лекций Udemy через Hermes tools. Обходит антибот-детекцию.

## Как это работает

```
1. browser_navigate → 2. sleep(15-20s) → 3. browser_console (get URL) → 4. terminal/curl (download)
```

**Ключевое:** CDP `Page.navigate` триггерит антибот Udemy → видео не грузится. Hermes `browser_navigate` НЕ триггерит, поэтому video URL доступен через Performance API или `video.currentSrc`.

## Подготовка браузера

Brave должен быть запущен с remote debugging. **Без `--remote-allow-origins=*`** — этот флаг меняет fingerprint браузера и включает антибот:

```
killall "Brave Browser" 2>/dev/null; sleep 3
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 --no-first-run --no-default-browser-check &
sleep 8
hermes config set browser.cdp_url http://127.0.0.1:9222
```

После перезапуска нужно залогиниться в Udemy вручную (один раз за сессию).

## Процедура скачивания одной лекции

### Шаг 1: Навигация
```
browser_navigate(url="https://www.udemy.com/course/{COURSE_SLUG}/learn/lecture/{LECTURE_ID}")
```
Hermes browser_navigate использует Playwright Chromium с фингерпринтом, не триггерящим антибот.

### Шаг 2: Ожидание загрузки видео
Подождать 15-20 секунд. Видео должно загрузиться (readyState 4).

Использовать:
```
terminal(command="sleep 20 && echo ok", timeout=30)
```

### Шаг 3: Перехват URL видео
Два способа получения URL (оба работают):

**A. Через Performance API:**
```js
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('mp4-cdn') && r.name.includes('WebHD'))
  .map(r => r.name)[0]
```

**B. Через video.currentSrc (содержит secure-токен):**
```js
document.querySelector('video').currentSrc
```

Возвращает URL вида:
```
https://mp4-cdn77.udemycdn.com/{HASH}/2/WebHD_720p.mp4?secure={TOKEN}%3D%3D%2C{TIMESTAMP}
```

Если не найден — ждать ещё 10с и повторить (до 3 раз).

### Шаг 4: Скачивание
```python
terminal(background=True, command="curl -L -o '{OUTPUT_DIR}/{FILENAME}.mp4' \
  -H 'Referer: https://www.udemy.com/' \
  -H 'User-Agent: Mozilla/5.0' \
  --cookie '__udmy_2_v57r=...; csrftoken=...; ud_cache_logged_in=1; ud_cache_user=...' \
  '{VIDEO_URL}'", notify_on_complete=True)
```

Куки берутся из `document.cookie` браузера (те, что не зашифрованы). Основные: `__udmy_2_v57r`, `csrftoken`, `ud_cache_logged_in`, `ud_cache_user`.

## Конвейер (pipelinable)

Пока одна лекция качается в фоне, можно навигировать на следующую — видео предзагрузится:

```
# 1. Начать download лекции N в background
terminal(background=True, notify_on_complete=True, ...)

# 2. Пока качается, навигировать на лекцию N+1
browser_navigate(url="...lecture/{NEXT_LECTURE_ID}")

# 3. Когда придёт notify — URL следующей уже готов, сразу download
```

## Конвейер (pipelinable download)

Пока одна лекция качается в фоне, можно навигировать на следующую — видео предзагрузится:

```python
# 1. Начать download лекции N в background
terminal(background=True, notify_on_complete=True,
  command="curl -L -o '...' -H '...' --cookie '...' 'VIDEO_URL'")

# 2. Пока качается, навигировать на лекцию N+1
browser_navigate(url="https://www.udemy.com/course/romikwvf/learn/lecture/{NEXT_ID}")

# 3. Через 15-20с URL следующей будет готов
# 4. Когда придёт notify — сразу download
```

Этот паттерн сокращает общее время ~вдвое (загрузка видео в браузере совмещается с curl'ом).

## Данные курса

См. `references/lecture-list.md` — ID и названия всех 43 лекций.

## Антибот-детекция: что НЕ РАБОТАЕТ

| Метод | Результат | Причина |
|-------|-----------|---------|
| CDP `Page.navigate` | ❌ Видео не грузится | Udemy детектит CDP WebSocket |
| Python `websocket` + `Runtime.evaluate` | ❌ readyState=0 | Тот же CDP детект |
| AppleScript `open location` | ❌ Новая вкладка без сессии | Не передаёт куки |
| `--remote-allow-origins=*` | ❌ Включает антибот | Меняет fingerprint браузера |
| yt-dlp | ❌ HTTP 403 | Udemy блокирует |
| Прямой requests к API | ❌ 403 без кук | Куки зашифрованы (macOS Keychain) |

| Метод | Результат | Комментарий |
|-------|-----------|-------------|
| Hermes `browser_navigate` | ✅ Работает | Использует Playwright |
| Hermes `browser_console` | ✅ Работает | Performance API доступен |
| AppleScript `set URL of active tab` | ⚠️ Иногда | Может не сработать если таб в фоне |
| curl с куками | ✅ Работает | Куки живы ~1 час |

## Провайдеры и куки

Куки Brave хранятся в зашифрованном виде (macOS Keychain). Единственный способ получить — через `document.cookie` в браузере. Для curl используются только незашифрованные куки (те, что доступны через `document.cookie`).

Жизнь secure-токена в URL: ~1 час. Если токен протух — curl скачает 868 байт (не видео). Нужно получить свежий URL через browser_console.

## Данные курса

См. `references/aging-course-data.md` — ID и названия всех 43 лекций.
