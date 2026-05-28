# Session Troubleshooting Notes

## 2026-05-23: DRM lecture downloaded via CDP performance entries

**Цель:** Скачать лекцию 44 (Выбор индивидуальной диеты), которая не расшифровалась через Puyodead1 (Widevine CENC DRM, KID: c11cc20e...).

**Проблема:** Puyodead1 скачал зашифрованные `.encrypted.mp4` и `.encrypted.m4a` (30 MB + 1.4 MB) и сообщил:
```
ERROR: Audio key not found for c11cc20e6c1a4cc1be7680bb36d3e463
```

Ключа нет, keyfile отсутствует.

**Решение** (подтверждено рабочим):
1. Открыл страницу курса `browser_navigate → https://www.udemy.com/course/romikwvf/`
2. Кликнул "Go to course" → попал на SPA-плеер
3. Развернул Section 7 в сайдбаре, кликнул "Play" на лекции 44
4. Плеер показал "Unable to play media." (DRM)
5. Выполнил в browser_console:
   ```js
   performance.getEntriesByType('resource')
     .filter(r => r.name.includes('mp4-cdn'))
     .map(r => r.name)
   ```
6. **Результат:** Нашёлся прямой mp4-cdn URL (WebHD_720p) — Udemy кладёт незашифрованный mp4 параллельно DRM-потоку
7. Скачал curl'ом с Referer (без кук): 18 MB, файл рабочий

**Вывод:** Даже при DRM-шифровании (Widevine CENC), Udemy часто оставляет незащищённый mp4-cdn поток. Проверять через performance entries ДО того, как сдаваться.

## 2026-05-23: Puyodead1 successful batch download

**Цель:** Докачать лекции 26-44 (19 lectures) через Puyodead1/udemy-downloader с resume.

**Команда:**
```bash
cd /tmp/udemy-downloader
python3 main.py \
  -c "https://www.udemy.com/course/romikwvf" \
  --browser brave \
  -q 1080 \
  --out ~/Downloads/udemy \
  --continue-lecture-numbers \
  --concurrent-downloads 10 \
  --log-level INFO
```

**Результат:**
- Пропустил лекции 1-22 (были в выходной папке) ✅
- Скачал 023-028 (секция 4): 138 MB, 136 MB, 204 MB, 76 MB, 269 MB, 140 MB ✅
- Скачал 029-042 (секция 5, все в HLS 1080p): от 37 MB до 493 MB ✅
- Скачал 043 (секция 6): 18 MB ✅
- Не расшифровал 044 (секция 7, DRM) — решено через CDP (см. выше) ✅

**Производительность aria2:**
- Десятки параллельных сегментов, скорость ~10-15 MB/s
- Самая большая лекция (042): 493 MB за 32 сек

**Важное наблюдение:** `-q 1080` выбрало 720p для прямых mp4-лекций, но HLS-лекции в секции 5 реально скачались в 1920x1080. Это не баг — тулза выбирает лучшее доступное качество для каждого формата.

**Варнинги (безопасно игнорировать):**
- `Keyfile not found!` — только для DRM-лекций
- `RequestsDependencyWarning: urllib3` — безвреден
- `Downloading 2 format(s): video_avc1_5, audio_en_mp4a.40.2` — для DASH DRM

## 2026-05-20: Cookie expiration and interrupted downloads

**Проблема:** После перезапуска Brave, Hermes использует headless Chromium для browser_navigate через CDP. Куки Udemy в нём нет — плеер показывает "Loading" бесконечно или требует логина.

**Решение:** Пользователь должен залогиниться вручную в том браузере, к которому подключён CDP. После логина куки сессии живут ~12-24 часа.

## 2026-05-18: Initial CDP anti-bot discovery

**Проблема:** При подключении через Hermes browser_navigate, Udemy плеер иногда показывает blob URL вместо mp4-cdn, и video.readyState = 0 (блокировка).

**Наблюдение:** Блокировка выборочная — одна лекция работает, следующая — нет. Зависит не от CDP как такового, а от чего-то другого (CDN? размер видео? количество запросов с IP?).

**Обход:** 
1. Обновить страницу через `browser_navigate` на ту же лекцию
2. Если не помогло — использовать метод "Go to course": `browser_navigate` на страницу курса, затем кликнуть "Go to course"
3. Если всё равно blob — только Puyodead1
