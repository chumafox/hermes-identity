# Google Antigravity (Project IDX Native Client)

**Antigravity.app** — нативный клиент облачной IDE **Project IDX** от Google со встроенным AI-агентом на базе Gemini.

## Bundle Info

| Поле | Значение |
|---|---|
| Bundle ID | `com.google.antigravity` |
| Версия | 2.0.6 (на момент документации) |
| Тип | Electron-based (app.asar) |
| Подпись | Developer ID Application: Google LLC (EQHXZ8M8AV) |
| Категория | Developer Tools |
| Минимальная macOS | 12.0 |
| Архитектура | arm64 (Apple Silicon) |
| URL Scheme | `antigravity://` |

## Установка

Приложение находится в `/Applications/Antigravity.app`. Устанавливается стандартно — перетаскиванием в /Applications. Auto-update через Google Cloud Run: `https://antigravity-hub-auto-updater-974169037036.us-central1.run.app/manifest/`

## Запуск

```bash
open -a "/Applications/Antigravity.app"
```

## Структура бандла

- `Contents/MacOS/Antigravity` — основной бинарник (Mach-O arm64)
- `Contents/Frameworks/` — Electron framework + Helper процессы
- `Contents/Resources/app.asar` — зашифрованный код приложения (~2MB)
- `Contents/Resources/app.asar.unpacked/node_modules/` — расшарованные node-модули
- `Contents/Resources/bin/language_server` — **Go-бинарник Google language server** (127MB, ключевой компонент)
- `Contents/Resources/bin/webm_encoder` — encoder для записи экрана

## language_server

Бинарник `/Applications/Antigravity.app/Contents/Resources/bin/language_server` — ключевой Backend-компонент. Написан на Go, предоставляет API для моделей Google Gemini.

### Ключевые CLI флаги

| Флаг | Назначение |
|---|---|
| `-headless=true` | Запуск без GUI |
| `-http_server_port=0` | HTTP API порт (0 = random) |
| `-https_server_port=0` | HTTPS порт |
| `-cdp_port=9222` | Chrome DevTools Protocol порт |
| `-model_api_client_type=ccpa\|gemini` | Какой клиент модели использовать |
| `-api_server_url` | URL API сервера (по умолч. http://0.0.0.0:50001) |
| `-inference_api_server_url` | Кастомный URL инференса |
| `-cloud_code_endpoint` | CCPA API URL |
| `-generative_service_addr` | Адрес Generative Language Service |
| `-browser_eval_env=true` | Включить Playwright/браузерное окружение |
| `-enable_lsp=true` | Включить LSP |
| `-app_data_dir` | Директория данных (по умолч. antigravity-ide) |
| `-csrf_token` | CSRF токен для API |
| `-local_chrome_headless=true` | Chrome в headless режиме |
| `-local_chrome_user_data_dir` | Chrome user data directory |

### Использованные флаги при реальном запуске (из ps aux)

```
-standalone
-override_ide_name antigravity
-subclient_type hub
-override_ide_version 2.0.6
-override_user_agent_name antigravity
-https_server_port 0
-csrf_token 50f1c5e4-72c1-4326-ac44-8740e4f69721
-app_data_dir antigravity
-api_server_url https://generativelanguage.googleapis.com
-cloud_code_endpoint https://daily-cloudcode-pa.googleapis.com
-enable_sidecars
```

## User Data

Путь: `~/Library/Application Support/Antigravity/`

## Рендер-процессы

При запуске создаёт:
- Основной процесс (Antigravity)
- GPU процесс (Antigravity Helper --type=gpu-process)
- Рендеры (Antigravity Helper (Renderer))
- Утилиты: network, audio, video_capture
- Language server (отдельный бинарник)

## Полезное для Hermes Agent

При необходимости автоматизировать Antigravity через Hermes:
1. Подключить `computer_use` tool (через `hermes tools`)
2. Запустить Antigravity, делать скриншоты, кликать по элементам
3. Альтернатива: запустить `language_server` с `-http_server_port` и `-headless=true` для HTTP API-доступа
4. CDP порт (9222) можно использовать для Chrome DevTools Protocol — открыть в браузере `chrome://inspect`

## Ссылки

- Project IDX: https://idx.dev
- Google AI Studio: https://aistudio.google.com
