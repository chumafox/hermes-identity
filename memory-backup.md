# Hermes Identity: Memory Backup

## User Profile
- Имя: Jenya (логин jenyanovak)
- iMessage: chumafox@me.com
- Язык: Русский (предпочитает)
- Стиль: кратко, технично, без предисловий
- ОС: macOS 15.7.5 (на обоих Mac)
- hostname экранного: dispo
- Локация: Китай (с быстрым доступом через HK)

## Projects & Interests
- ACE-Step-1.5 (генерация музыки)
- OpenVox (голосовые задачи)
- Изучение курса "Как замедлить старение" (Udemy)

## Hardware Setup
- **Экранный Mac** (jenyanovak, HK): быстрый интернет, основная рабочая станция
- **Безголовый Mac** (admin, M1 Pro 32GB, Китай): серверные задачи, LM Studio, Ollama
- Связь: Thunderbolt Bridge (192.168.2.x, приоритет) + Type-C (192.168.3.x)
- Thunderbolt скорость: ~17.5 Gbps
- USB-C скорость: ~340 Mbps

## Network
- Безголовый интернет: iPhone USB tethering (172.20.10.x)
- WiFi на безголовом выключен
- Happ (Xray-core) прокси на экранном
- Поиск из Китая: Bing China, Baidu, Gitee, ModelScope
- ModelScope предпочтительнее HuggingFace для загрузок

## Software (экранный)
- Hermes Agent (текущая версия)
- Brave Browser (CDP порт 9222)
- websocket-client (Python, для CDP)
- yt-dlp, ffmpeg, curl

## Software (безголовый)
- Hermes Agent v0.13.0
- LM Studio (gemma-4-e4b-it-mlx)
- Node.js v22
- Ollama 0.22.0
- Claude Code 2.1.119
- Goose Agent v1.33.1
- Cursor IDE 3.3.27
- Playwright + Chromium
- Zettlr 3.4.2
- OpenVox

## LLM Providers
| Провайдер | Модель | Роль |
|-----------|--------|------|
| deepseek | deepseek-v4-flash | Основной, быстрые задачи |
| deepseek | deepseek-chat | Fallback при rate limit |
| kimi-coding | (default) | При rate limit DeepSeek (backoff 2ч) |
| anthropic | claude-sonnet-4 | Сложный код, рефакторинг |

## Credentials & Config
- API ключи в ~/.hermes/.env
- browser.cdp_url: http://127.0.0.1:9222
- Куки Brave зашифрованы (macOS Keychain)
- Для curl/yt-dlp: cookies из document.cookie

## Known Tool Quirks
- yt-dlp → Udemy 403 (антибот)
- CDP Page.navigate → антибот (видео не грузится)
- Hermes browser_navigate → работает (mp4-cdn URL из performance entries)
- AppleScript `set URL of active tab` → обходит детекцию
- Для диагностики соединений: sudo lsof / sudo netstat
- Screen Sharing: Caps Lock для смены языка (Cmd+Space не проходит)
- SSH на безголовый: ключ + expect (sshpass не работает)

## Skills Created
- udemy-lecture-downloader: скачивание лекций Udemy через Hermes tools
- (будут добавляться)

## Udemy Course Download
- Курс: "Как замедлить старение организма" (43 лекции)
- Метод: browser_navigate → sleep(15) → browser_console → curl
- Папка: ~/udemy-aging-course/
- Прогресс: 7/43 лекций скачано
