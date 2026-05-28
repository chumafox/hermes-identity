---
name: udemy-lecture-downloader
description: Скачивает лекции Udemy курса — через Puyodead1/udemy-downloader (основной) или Hermes tools (fallback)
category: web-automation
---

# Udemy Lecture Downloader

Скачивает видео лекций Udemy курса.

**Два метода (в порядке приоритета):**
1. **Puyodead1/udemy-downloader** — через Udemy API, обходит антибот, HLS/DRM/1080p
2. **Hermes tools** (CDP → performance entries → curl) — когда Puyodead1 не установлен или для 1-2 лекций

---

## Метод 1: Puyodead1/udemy-downloader (ОСНОВНОЙ)

Использует Udemy API-2.0 напрямую, минуя антибот на странице плеера. Поддерживает HLS, DASH, DRM, mp4, resume.

### Установка

```bash
cd /tmp && git clone --depth 1 https://github.com/Puyodead1/udemy-downloader.git
cd /tmp/udemy-downloader && pip install -r requirements.txt
```

**Зависимости:**
- `aria2` — параллельная загрузка HLS сегментов: `brew install aria2` (уже установлен на этом Mac)
- `shaka-packager` — для DRM-лекций (curl + chmod, brew нет formula)
- `ffmpeg` — уже есть

### Использование

```bash
cd /tmp/udemy-downloader
python3 main.py \
  -c "https://www.udemy.com/course/{SLUG}" \
  --browser brave \
  -q 1080 \
  --out ~/Downloads/udemy \
  --continue-lecture-numbers \
  --concurrent-downloads 10 \
  --log-level INFO
```

**Параметры:**
| Параметр | Описание |
|----------|----------|
| `-c URL` | URL курса (например, https://www.udemy.com/course/romikwvf) |
| `--browser brave` | Извлекать куки из Brave (или safari/chrome) |
| `-q 1080` | Запрошенное качество. HLS лекции → 1080p, mp4 → может упасть на 720p |
| `--out ~/Downloads/udemy` | Выходная папка |
| `--continue-lecture-numbers` | Сквозная нумерация + пропуск уже скачанных |
| `--concurrent-downloads 10` | Параллельных сегментов (нужен aria2) |
| `--chapter "1,3-5"` | Конкретные главы |
| `--info` | Только инфо, без скачивания |
| `--skip-hls` | Пропустить HLS если есть mp4 вариант |

### Как работает resume

`--continue-lecture-numbers` проверяет наличие файла `{OUTPUT}/{SLUG}/{Chapter}/NNN Title.mp4`.
Если файл есть — пропускает. Достаточно повторно запустить ту же команду после прерывания.

**Структура выходной папки:**
```
~/Downloads/udemy/romikwvf/
├── 01 - Оцениваем свое здоровье/
│   ├── 001 Первая лекция.mp4
│   └── ...
├── 02 - Питание/
├── ... (7 chapters total)
└── 07 - Индивидуальный подбор диеты/
```

### DRM (лекции с шифрованием)

Некоторые лекции защищены DRM (Widevine). Утилита скачивает зашифрованные `.encrypted.mp4` и `.encrypted.m4a`, но для расшифровки нужен keyfile.

**Симптомы:**
```
ERROR: Audio key not found for {KID}, if you have the key then you
probably didn't add them to the key file correctly.
```

**Решение 1 — CDP performance entries (ПОДТВЕРЖДЁННЫЙ МЕТОД):**
Даже если видео плеер показывает "Unable to play media." или "Your browser can't play this media" (DRM), Udemy **часто кладёт незашифрованный mp4-cdn URL** параллельно DRM-потоку. Этот URL виден через `performance.getEntriesByType('resource')`.

**Проверено на практике:** лекция 44 курса romikwvf — Widevine CENC DRM. Плеер показывал "Unable to play media.", но mp4-cdn URL (WebHD_720p) был в resource entries. Скачан curl'ом — 18 MB, работает.

**Шаги:**
1. Открой лекцию через SPA-навигацию (сайдбар курса → разверни секцию → клик "Play" на нужной лекции)
2. Убедись, что URL в адресной строке стал `/learn/lecture/{ID}/`
3. Выполни в консоли браузера:
   ```js
   performance.getEntriesByType('resource')
     .filter(r => r.name.includes('mp4-cdn'))
     .map(r => r.name)
   ```
4. Если вернулся URL — скачай curl'ом:
   ```bash
   curl -L -o "lecture.mp4" \
     -H "Referer: https://www.udemy.com/" \
     "URL_из_шага_3"
   ```
   **Куки не нужны** — достаточно Referer. Токен `?secure=` живёт ~6 часов.
5. Если mp4-cdn URL не найден — переоткрой лекцию через сайдбар и проверь снова (иногда URL появляется после полной загрузки плеера).

**Решение 2 — Hermes tools fallback (см. Метод 2):** прямой browser_navigate на лекцию.

**Проверка:**
```bash
find ~/Downloads/udemy/romikwvf -name "*.encrypted.*" 2>/dev/null
```

### Постуборка после скачивания

После завершения скачивания — удалить мусор и дубликаты:

```bash
# 1. Удалить .aria2 временные файлы
find ~/Downloads/udemy/romikwvf -name "*.aria2" -delete

# 2. Удалить зашифрованные DRM-файлы (бесполезны без ключа)
find ~/Downloads/udemy/romikwvf -name "*.encrypted.*" -delete

# 3. Удалить старые дублирующиеся папки
rm -rf ~/udemy-aging-course/
rm -rf ~/Downloads/udemy-test/

# 4. Переименовать лекцию 44 если скачана вручную (curl)
# Было: "044-Выбор-индивидуальной-диеты.mp4"
# Стало: "044 Выбор индивидуальной диеты.mp4"
```

### Предостережения (безопасно игнорировать)

- `Keyfile not found! You won't be able to decrypt any encrypted videos!` — только для DRM-лекций
- `RequestsDependencyWarning: urllib3` — безвредный warning от requests библиотеки
- Если `-q 1080` не находит 1080p версию в API, молча падает на 720p (пишет "Selected quality: video 720")

### Пример с реального курса (romikwvf, 44 лекции, 8.1 GB)

Скачано 43/44 лекций за ~8 минут. Одна лекция (44) с DRM — не расшифрована.
Скорость: ~10-15 MB/s на HLS сегментах через aria2.

---

## Метод 2: Hermes tools (FALLBACK)

Когда Puyodead1 недоступен, или для 1-2 лекций, или лекция под DRM и нужен mp4-cdn URL.

### Подготовка браузера

1. Brave запущен с `--remote-debugging-port=9222`
2. `hermes config set browser.cdp_url http://127.0.0.1:9222`
3. Пользователь залогинен в Udemy в Brave

### Пайплайн для одной лекции

**Slug курса:** `romikwvf` (не `kak-zamedlit-starenie-organizma`)

```
browser_navigate(url="https://www.udemy.com/course/romikwvf/learn/lecture/{ID}")
sleep(15)                       # ждём загрузки видео
browser_console(expression="...")  # получаем mp4-cdn URL
terminal(background, curl -L -o '{FILE}' ... '{URL}')  # скачиваем
```

### Перехват URL видео

```js
// Через performance entries (основной)
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('mp4-cdn') && r.name.includes('WebHD'))
  .map(r => r.name)[0]

// Через video.currentSrc (fallback)
document.querySelector('video')?.currentSrc
```

Если URL не найден — подождать ещё 10с и повторить (макс 3 раза).

### Скачивание curl'ом

```bash
curl -L -o "{FILENAME}.mp4" \
  -H "Referer: https://www.udemy.com/" \
  -H "User-Agent: Mozilla/5.0" \
  --cookie "...куки из браузера..." \
  '{VIDEO_URL}'
```

### Загрузка после "Loading" (сброс сессии)

Когда `browser_navigate` на `learn/lecture/{ID}` показывает только "Loading":

1. `browser_navigate` → `https://www.udemy.com/course/{SLUG}/`
2. Найти и кликнуть "Go to course" (через JS)
3. После загрузки плеера — `browser_navigate` на нужную лекцию (работает)

### Навигация к конкретной лекции через сайдбар (SPA)

Когда прямой `browser_navigate` на `learn/lecture/{ID}` не загружает видео (Loading, антибот):

1. Открой страницу курса: `browser_navigate` → `https://www.udemy.com/course/{SLUG}/`
2. Кликни "Go to course" — попадёшь на SPA-версию курса
3. В сайдбаре "Course content" **разверни нужную секцию** кликом по заголовку
4. Найди нужную лекцию в списке и **кликни "Play"** на ней
5. URL в адресной строке обновится на `learn/lecture/{ID}` (SPA-навигация)
6. Проверь видео через `performance.getEntriesByType('resource')`

**Подтверждено:** этот метод обходит антибот для лекций, которые отказывались грузиться через прямой `browser_navigate`. Использовано для лекции 44 (56230185) — видео "Unable to play media" (DRM), но mp4-cdn URL был в ресурсах.

### Ограничения метода

- CDP-подключение триггерит антибот — видео не грузится на некоторых лекциях (blob URL)
- Антибот срабатывает выборочно — одна лекция качается, следующая нет
- Для blob/HLS-лекций бесполезен — нужен Puyodead1

---

## Работа через существующую вкладку пользователя (обход CDP-антибота)

Когда антибот блокирует видео на attached-вкладке, но пользователь открыл лекцию вручную в Brave, можно перехватить через CDP Runtime.evaluate на target_id этой вкладки.

**Шаги:**
1. Попросить пользователя открыть лекцию в Brave
2. `browser_cdp(method="Target.getTargets")` — найти вкладку с url содержащим `learn/lecture/{ID}`
3. `Runtime.evaluate` на target_id: получить m3u8 URL через `performance.getEntriesByType('resource')`
4. Получить содержимое m3u8 через fetch в браузере
5. Скачать .ts сегменты curl'ом с Referer (без кук — достаточно одного Referer)
6. Собрать mp4 через ffmpeg concat

### Проваленные подходы (не тратить время)

| Метод | Результат |
|-------|-----------|
| CDP `Page.navigate` через WebSocket | ❌ антибот — видео не грузится |
| `yt-dlp --cookies-from-browser brave` | ❌ 403 Forbidden |
| ffmpeg с m3u8 + Referer/User-Agent | ❌ 403 (не хватает куков) |
| Proxyman с Brave | ❌ Brave игнорирует системный прокси |
| AppleScript `open location` | ❌ открывает новую вкладку |
| curl на .ts с `Referer:` | ✅ Работает! Токен secure= живёт ~6ч |

---

## Список лекций

См. `references/lecture-list.md` — полный список с ID, названиями, статусом.

## Прогресс скачивания

См. `references/download-progress.md` — текущий статус по курсам.

## Транскрибация (следующий шаг)

После скачивания — транскрибация аудио в текст. См. `references/transcription-options.md`:

- **mlx-whisper** (рекомендуется) — Apple MLX native, fastest on M-series
- faster-whisper — второй выбор
- openai-whisper (PyTorch MPS) — медленнее всего

## Истории сессий и отладка

См. `references/session-troubleshooting.md` — ошибки, диагностика, решённые проблемы.

## Batch Download Script (DEPRECATED)

Скрипт `scripts/udemy-batch-download.py` работает только внутри `execute_code` и страдает от антибота.
**Используй Puyodead1/udemy-downloader (Метод 1) вместо него.**
