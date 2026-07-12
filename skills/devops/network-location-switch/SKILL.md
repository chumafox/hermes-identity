---
name: network-location-switch
description: Переключение между Ship (локальная сеть корабля — sing-box + DNS 172.19.0.1 + SOCKS5) и Normal (чистые настройки, sing-box остановлен).
---

# Network Location Switch

## Как работает сеть на MacBook Air

```
весь трафик → utun9 (TUN) → sing-box → SOCKS5 127.0.0.1:1080 → SSH туннель → внешний сервер
```

sing-box (root, launchd) перехватывает ВЕСЬ трафик через `auto_route: true` + `strict_route: true`.
Исключение: 192.168.x.x идёт напрямую.
DNS: hijack port 53 → CloudFlare 1.1.1.1 через SOCKS5.

SOCKS5 на 127.0.0.1:1080 — это SSH динамический туннель (ssh -D 1080).

На сети корабля SSH/SOCKS работает. На другой сети — нет.

## Созданные Location

### Ship
- Wi-Fi DNS: 172.19.0.1
- Wi-Fi SOCKS5: 127.0.0.1:1080 (Enabled)
- sing-box: запущен
- Использовать когда подключён к локальной сети корабля

### Normal
- Wi-Fi DNS: авто (DHCP)
- Wi-Fi SOCKS5: выключен
- sing-box: остановлен
- Использовать когда подключён к другому источнику интернета
- Чистые настройки, как на новом Mac

## Быстрое переключение

```bash
net-loc              # показать текущий Location и статус sing-box
net-loc ship         # переключиться на Ship (запускает sing-box, DNS+SOCKS5)
net-loc normal       # переключиться на Normal (останавливает sing-box, сброс настроек)
net-loc -l           # список всех Location
```

Скрипт: `~/bin/net-loc`

**Требует sudo** для управления sing-box (остановка/запуск через launchctl).

## Как это работает

Ship:
```
sudo сети → sing-box запущен → SOCKS5:1080 → SSH туннель → интернет есть
```

Normal:
```
sudo отключён → sing-box остановлен → трафик напрямую через DHCP → интернет есть
```

## Ручное управление sing-box

```bash
# Остановить
sudo launchctl unload -w /Library/LaunchDaemons/com.user.singbox.plist

# Запустить
sudo launchctl load -w /Library/LaunchDaemons/com.user.singbox.plist

# Статус
ps aux | grep sing-box
```

## Ручное переключение Location

```bash
networksetup -switchtolocation Ship
networksetup -switchtolocation Normal
```
