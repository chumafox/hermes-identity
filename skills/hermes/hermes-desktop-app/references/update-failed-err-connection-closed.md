# Update failed — анализ лога

## Лог (updater.log)

```
07:11:48 [info] Checking for update
07:11:53 [info] Update for version 0.6.2 is not available (latest version: 0.6.2)
07:36:53 [info] Checking for update
07:37:08 [error] Error: Error: net::ERR_CONNECTION_CLOSED
    at SimpleURLLoaderWrapper.<anonymous> (node:electron/js2c/browser_init:2:130147)
07:37:11 [error] Error: Error: Please check update first
    at MacUpdater.downloadUpdate (electron-updater/out/AppUpdater.js:438:27)
    at /out/main/index.js:31028:25
07:37:12 [error] Error: Error: Please check update first
... (повторяется ~10 раз до 07:46)
```

## Причина каскада "Please check update first"

1. Первая проверка (07:11) — успешна, версия актуальна
2. Вторая (07:36) — `ERR_CONNECTION_CLOSED` (intermittent GitHub API timeout)
3. `electron-updater/AppUpdater.js:438`:
   ```js
   downloadUpdate(cancellationToken) {
       const updateInfoAndProvider = this.updateInfoAndProvider;
       if (updateInfoAndProvider == null) {
           const error = new Error("Please check update first");
           this.dispatchError(error);
           return Promise.reject(error);
       }
       // ...
   }
   ```
4. После неудачной проверки `updateInfoAndProvider` = null
5. Все последующие вызовы `downloadUpdate()` сразу падают — не делают повторной проверки
6. При `autoDownload: true` (включено) приложение само вызывает `downloadUpdate()` после `checkForUpdates()` — но если check упал, он не запускает download

## Факторы

- `app-update.yml`: owner=fathah, repo=hermes-desktop, provider=github
- GitHub API из Китая блокирован — даже через прокси intermittent (TCP reset)
- В данном случае Mac в HK (dispo) — но даже там бывают rate limits / TCP drops
- Первичная проблема: **нет retry в checkForUpdates**
- Вторичная: **downloadUpdate не делает re-check перед отказом**

## Фикс

Патч `out/main/index.js`:
- `check-for-updates` → 3 retry с backoff 2s/4s/8s
- `download-update` → при ошибке делает `checkForUpdates()` и повторяет download
