# Two-Brave Approach (CDP Anti-Detect)

## Проблема

Udemy определяет, что браузер подключён к Chrome DevTools Protocol (CDP),
и блокирует загрузку видео (readyState вечно 0, видео не грузится).

При этом:
- Пользователь **залогинен** (видно "Jenya Novak", "Leave a rating")
- Страница курса и сайдбар **загружаются**
- Но плеер показывает "Loading" навечно
- `performance.getEntriesByType('resource')` не содержит mp4-cdn URL

## Решение: два Brave

Использовать **два разных экземпляра Brave**:

1. **Первый Brave** — открыт вручную (без CDP). В нём пользователь логинится
   в Udemy и открывает лекцию. Видео грузится нормально — антибот не срабатывает.

2. **Второй Brave** — запускается отдельно с флагами CDP:
   ```bash
   "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
     --remote-debugging-port=9222 \
     --no-first-run \
     --user-data-dir=/tmp/brave-cdp-profile
   ```
   У этого Brave **отдельный профиль** (через `--user-data-dir`),
   поэтому он не пересекается с основным.
   Пользователь логинится в Udemy и в нём.

3. Настройка CDP:
   ```bash
   hermes config set browser.cdp_url http://127.0.0.1:9222
   ```
   Теперь Hermes подключается ко второму Brave, а первый остаётся чистым.

## Рабочий метод (проверено)

1. `browser_navigate` на страницу курса → `https://www.udemy.com/course/{SLUG}/`
2. Найти кнопку "Go to course" и кликнуть
3. После этого плеер появляется (Video, Play button, progress bar)
4. `sleep(15)` — ждём readyState=4
5. `browser_console` — получаем mp4-cdn URL
6. `curl` в фоне

**Важно:** Если навигироваться напрямую на `learn/lecture/{ID}` без
предварительного "Go to course", плеер не отрендерится.

## Почему второй Brave?

Если запустить CDP на том же Brave, где открыт Udemy, то Udemy
детектит DevTools и блокирует видео. Разделение на два экземпляра
решает проблему, т.к. первый (основной) Brave не имеет открытого CDP,
а второй (с CDP) используется только для чтения performance entries
и навигации уже после логина.

## Важно

- Второй Brave нужен с `--user-data-dir=...` чтобы не сбросить
  сессию основного браузера
- Пользователь должен залогиниться в обоих Brave
- После перезапуска второго Brave (например, из-за падения) —
  нужно снова залогиниться
