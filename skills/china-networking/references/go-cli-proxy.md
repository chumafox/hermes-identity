# Go CLI Tools Proxy (China)

Go-бинарники (net/http) — единственные, кто нативно понимает `socks5h://` в `HTTP_PROXY`. Не нужен HTTP-мост (tinyproxy/privoxy).

## Быстрая проверка

```
curl -s -x socks5h://127.0.0.1:1080 -o /dev/null -w "%{http_code}" https://oauth2.googleapis.com/token
# 404 = OK, 000/таймаут = прокси не работает
```

## Использование

```bash
# SOCKS5 с DNS через прокси (рекомендуется в Китае)
HTTP_PROXY=socks5h://127.0.0.1:1080 HTTPS_PROXY=socks5h://127.0.0.1:1080 agy auth --provider google

# SOCKS5 с локальным DNS
HTTP_PROXY=socks5://127.0.0.1:1080 HTTPS_PROXY=socks5://127.0.0.1:1080 gh auth login
```

## Какие тулы страдают

- `agy` — OAuth через Google (oauth2.googleapis.com)
- `gh` — GitHub CLI (api.github.com)
- `hugo` — темы, модули (github.com)
- `terraform` — провайдеры (registry.terraform.io)
- `gcloud` CLI — API Google Cloud
- `opentofu` — registry
- `syft` / `grype` — бд уязвимостей
- `cosign` — sigstore

## Почему Go — исключение

Node.js (`http-proxy-agent`), Python (`requests`), curl — все требуют HTTP-прокси для SOCKS5 (HTTP CONNECT метод). Go через `net/http.ProxyFromEnvironment()` нативно поддерживает socks5+h как протокол и делает CONNECT сам. Это значит: если у тебя только SSH -D SOCKS5 туннель (1080), Go-тулы заработают с `HTTP_PROXY=socks5h://127.0.0.1:1080`, а Node/Python — нет.

## Известная проблема: TUN-режим bypass

Sing-box/Xray/mihomo в TUN-режиме могут НЕ маршрутизировать трафик от конкретного Go-бина, если:
- Бин использует TCP-соединение до маршрута по умолчанию
- Loopback трафик (127.0.0.1) не идёт через TUN
Решение: всегда явно указывать `HTTP_PROXY` для Go-тул.

## OAuth на экранном Mac

Тулы, открывающие браузер для OAuth (agy, gh, gcloud), запрашивают `/dev/tty` — не работают из Hermes/SSH. Запускать в реальном терминале.

```bash
# В iTerm2/Terminal.app на экранном Mac
export HTTP_PROXY=socks5h://127.0.0.1:1080
export HTTPS_PROXY=socks5h://127.0.0.1:1080
agy auth --provider google
```

## Известные проблемы Go CLI OAuth (agy)

### Token exchange failed для Google OAuth

Симптом: `token exchange failed: Post "https://oauth2.googleapis.com/token": dial tcp X.X.X.X:443: i/o timeout`

Две независимые проблемы:

**1. agy не использует HTTP_PROXY (баг #113)**
`HTTP_PROXY=socks5h://127.0.0.1:1080` может не работать — Go `Transport.ProxyFromEnvironment()` делает SOCKS5 CONNECT, но редирект OAuth-сервера на localhost браузером ломает цепочку. Фикс: запускать браузер с явным прокси:
```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave \
  --proxy-server=socks5://127.0.0.1:1080
```
Затем запустить `agy` — браузер уже идёт через SOCKS5.

**2. HTTP→SOCKS5 мост не проходит TLS**
Простые Node.js/Python HTTP CONNECT→SOCKS5 бриджи могут фейлиться с `SSL_ERROR_SYSCALL`. TLS хендшейк не завершается через двойной прокси (HTTP→SOCKS5). 
- curl `-x http://127.0.0.1:18888 https://...` → SSL_ERROR_SYSCALL 
- curl `--socks5-hostname 127.0.0.1:1080 https://...` → работает
Решение: использовать `socks5://` напрямую везде, где возможно. Только для тулов без поддержки SOCKS5 — ставить настоящий HTTP-прокси (privoxy/tinyproxy).

### proxychains-ng arm64e (macOS 26.5+)

proxychains-ng, установленный через brew на macOS 26.5, вылетает с `Abort trap: 6` и ошибкой architecture mismatch:
```
dyld: ...libproxychains4.dylib' (mach-o file, but is an incompatible architecture (have 'arm64', need 'arm64e'))
```
Причина: Homebrew собирает arm64, а macOS 26.5+ использует arm64e (ARMv8.5-A pointer authentication) для системных процессов. `DYLD_INSERT_LIBRARIES` для arm64 dylib блокируется. **proxychains не работает на arm64e.**

### SSH SOCKS5 + TUN = не для всех процессов

Sing-box в TUN-режиме маршрутизирует системный трафик, но `HTTP_PROXY` всё равно нужен, потому что:
- Loopback трафик не идёт через TUN
- Некоторые Go-бинарники привязываются к конкретному интерфейсу
- sing-box может не обрабатывать трафик от процессов, запущенных до старта TUN

## Alias для частого использования

```bash
alias proxy-go='HTTP_PROXY=socks5h://127.0.0.1:1080 HTTPS_PROXY=socks5h://127.0.0.1:1080'
alias proxy-socks='ALL_PROXY=socks5://127.0.0.1:1080 http_proxy=socks5://127.0.0.1:1080 https_proxy=socks5://127.0.0.1:1080'
# proxy-go agy auth --provider google
# proxy-socks curl -s https://httpbin.org/ip
```
