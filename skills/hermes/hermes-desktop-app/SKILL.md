---
name: hermes-desktop-app
description: Hermes Desktop (Hermes One) — electron-based GUI, установка, апдейтер, прокси, отладка
tags: [hermes, desktop, electron, updater, troubleshooting]
related_skills: [hermes-self-maintenance, hermes-agent]
---

# Hermes Desktop App

Hermes Desktop (Hermes One.app) — Electron GUI для Hermes Agent. GitHub: `fathah/hermes-desktop`.

## Установленные версии и пути

- **App:** `/Applications/Hermes One.app`
- **Bundle ID:** `com.nousresearch.hermes`
- **Данные:** `~/Library/Application Support/hermes-desktop/`
- **Логи апдейтера:** `~/Library/Application Support/hermes-desktop/logs/updater.log`
- **ASAR:** `Hermes One.app/Contents/Resources/app.asar`
- **Конфиг обновлений:** `Hermes One.app/Contents/Resources/app-update.yml`

## "Update failed" — диагностика и починка

### Симптом

В десктопном приложении появляется "Update failed". В `updater.log`:

```
[error] Error: Error: net::ERR_CONNECTION_CLOSED
# затем россыпь:
[error] Error: Error: Please check update first
```

### Причина

`electron-updater` (MacUpdater) проверяет `github.com/fathah/hermes-desktop/releases`. В Китае GitHub блокирован без прокси. Даже при работающем прокси возможны intermittent `ERR_CONNECTION_CLOSED`.

После неудачной `checkForUpdates()`:
- `updateInfoAndProvider` = null
- `downloadUpdate()` сразу падает с "Please check update first"
- Повторной проверки не происходит — deadlock

### Фикс

Патчится `app.asar/out/main/index.js` — два IPC-хендлера:

**1. `check-for-updates` — retry 3× с exponential backoff:**

```js
const maxRetries = 3;
for (let attempt = 1; attempt <= maxRetries; attempt++) {
  try {
    return await autoUpdater.checkForUpdates();
  } catch (err) {
    if (attempt < maxRetries) {
      await new Promise(r => setTimeout(r, Math.min(2000 * 2**(attempt-1), 10000)));
    } else {
      // send update-error to renderer
    }
  }
}
```

**2. `download-update` — re-check перед download:**

```js
try {
  await autoUpdater.downloadUpdate();
} catch (err) {
  // re-check and retry download
  await autoUpdater.checkForUpdates();
  await autoUpdater.downloadUpdate();
}
```

### Порядок действий при починке

1. Извлечь asar: `npx asar e app.asar /tmp/extract`
2. Найти `check-for-updates` и `download-update` IPC handlers в `out/main/index.js`
3. Накатить патч (retry + re-check)
4. Запаковать: `npx asar p /tmp/extract app.asar`
5. Бэкап: `cp app.asar app.asar.bak`
6. Переподписать ad-hoc:
   ```bash
   codesign --remove-signature "/Applications/Hermes One.app"
   codesign --sign - --force --deep "/Applications/Hermes One.app"
   ```

### Pitfall: кодовая подпись

App подписан Developer ID + notarized. Модификация `app.asar` ломает `Sealed Resources`. Без переподписи macOS выдаёт "is damaged and can't be opened". Решение: ad-hoc signing (`codesign --sign -`). TeamIdentifier сбрасывается — приложение всё равно запускается.

Если нужна оригинальная подпись — восстановить из бэкапа `app.asar.bak`.

## Прокси для апдейтера

Electron использует `ELECTRON_HTTP_PROXY` env var для `net` module (которым пользуется `electron-updater`):

```bash
export ELECTRON_HTTP_PROXY="socks5://127.0.0.1:1080"
exec "/Applications/Hermes One.app/Contents/MacOS/Hermes One" "$@"
```

Лаунчер: `~/bin/hermes-desktop`

## Ссылки

- `references/update-failed-err-connection-closed.md` — полный лог и анализ ошибки
- `references/electron-updater-ipc-patch.md` — точный патч IPC-хендлеров
