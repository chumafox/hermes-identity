# Session: 2026-05-23 — Brave CDP + HLS (m3u8) обход антибота

## Контекст
Попытка скачать лекции 26-28 курса "Как замедлить старение организма" (slug: romikwvf).

## Проблема
Лекция 25 скачалась нормально через Brave CDP (mp4-cdn URL в performance entries).
Лекции 26+ — только blob URL в Brave CDP, HLS (m3u8) в Safari.
Антибот срабатывает выборочно.

## Что пробовали

### 1. Прямой mp4-cdn через Brave CDP (лекция 26)
- browser_navigate + sleep(15) + performance.getEntriesByType
- Результат: blob URL (readyState=4, но только blob)
- performance entries показывал только thumb-sprites

### 2. Safari через osascript (лекция 26)
- osascript в Safari:
  tell application "Safari" to set URL of current tab of window 1 to "..."
- document.querySelector("video")?.currentSrc → реальный m3u8 URL
- ffmpeg с Referer + User-Agent → 403 (куки Safari не передаются)

### 3. Brave CDP — вкладка пользователя (лекции 26-27)
- Пользователь открыл лекцию вручную в Brave
- Target.getTargets показал target с пользовательской вкладкой
- Runtime.evaluate на этом target дал доступ к DOM/cookies
- fetch() через браузер сработал — получили содержимое m3u8
- ffmpeg/yt-dlp → 403 на .ts сегменты

### 4. "Go to course" обход
- browser_navigate на страницу курса, клик "Go to course" через JS
- Антибот всё равно сработал — blob URL

## Рабочие находки

### Получить m3u8 URL из вкладки пользователя
1. browser_cdp(method="Target.getTargets") — найти targetId
2. browser_cdp(method="Runtime.evaluate", params={expression:"document.querySelector('video')?.currentSrc"}, target_id="...")
3. browser_cdp(method="Runtime.evaluate", params={awaitPromise:true, expression:"(async () => { const r = await fetch('{URL}'); return r.ok ? await r.text() : 'HTTP ' + r.status; })()"}, target_id="...")

## Выводы
1. Прямые mp4-cdn URL (когда есть) — лучший способ
2. HLS (m3u8) лекции — не качаются автоматически
3. Вкладка пользователя через CDP Runtime.evaluate — работает для чтения, не для скачивания
4. Для полной автоматизации HLS нужен скрипт, скачивающий .ts через браузерный fetch
