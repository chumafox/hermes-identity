# System Proxy Breaks CLI Tools When HTTP Bridge is Dead

## Симптом
CLI-инструменты (agy, curl, Go/Python утилиты) падают с:
- `proxyconnect tcp: dial tcp 127.0.0.1:8888: connect: operation timed out`
- `context deadline exceeded (Client.Timeout exceeded while awaiting headers)`

## Причина
macOS system proxy (`networksetup`) установлен на `127.0.0.1:8888` (HTTP bridge), но bridge остановлен. CLI-инструменты читают системные прокси-настройки и пытаются подключиться к мёртвому порту.

## Диагностика
```bash
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
# или
scutil --proxy | grep -E "HTTP|SOCKS|Enable"
```

## Фикс
Выключить HTTP/HTTPS прокси (SOCKS5 оставить):
```bash
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off
```

## Важно
macOS управляет HTTP и HTTPS прокси как двумя независимыми настройками. Отключение HTTP не отключает HTTPS. SOCKS5 управляется отдельно.
