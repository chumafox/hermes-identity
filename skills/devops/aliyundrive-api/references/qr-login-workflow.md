# QR Login workflow for aliyundrive-webdav v2.3.3+

## Проблема
refresh_token из браузера (32 hex, валидный для REST API) отвергается aliyundrive-webdav v2.3.3:
```
Error: Invalid refresh token value found in `--refresh-token` argument
```

## Решение — QR login

### 1. Генерация QR
```bash
aliyundrive-webdav qr generate
```
→ возвращает JSON:
```json
{
  "qrCodeUrl": "https://openapi.alipan.com/oauth/qrcode/<sid>",
  "sid": "..."
}
```

### 2. Открыть QR пользователю
Через Safari:
```bash
osascript -e 'tell application "Safari" to set URL of current tab of window 1 to "<qrCodeUrl>"'
```
Пользователь сканирует QR приложением 阿里云盘 на телефоне (扫一扫).

### 3. Запуск с QR логином
```bash
aliyundrive-webdav qr login
```
Утилита ждёт сканирования, сама получает токен и запускает WebDAV сервер.

### 4. Finder mount
Cmd+K → `http://127.0.0.1:18080` → Connect

## Заметки
- refresh_token из REST API (`curl -X POST https://api.aliyundrive.com/v2/account/token`) возвращает новый refresh_token при каждом вызове — нужно сохранять
- refresh_token из Safari localStorage может быть просрочен — лучше сначала обновить через API
- Токен из API (формат: 32 hex) работает с REST, но не с aliyundrive-webdav v2.3.3
- Бинарный файл: `/Library/Frameworks/Python.framework/Versions/3.13/bin/aliyundrive-webdav`
- safari-web-scraping skill: Safari → Settings → Advanced → Allow JavaScript from Apple Events
