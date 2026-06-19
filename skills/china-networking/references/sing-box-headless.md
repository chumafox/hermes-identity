# sing-box: Headless Mac Proxy Client

## Overview

[sing-box](https://github.com/SagerNet/sing-box) (★34.7k) — универсальная прокси-платформа от SagerNet. Один бинарник (~15MB Go), без GUI, идеально подходит для безголового Mac (pro). Работает с subscription URL из Shadow Rocket / Clash.

## Установка

```bash
brew install sing-box
```

Или скачать бинарник: https://github.com/SagerNet/sing-box/releases

## Быстрый старт

### 1. Сгенерировать дефолтный конфиг

```bash
sing-box rule-set compile --config config.json
# или
sing-box check -c config.json
```

### 2. Структура конфига

```json
{
  "log": {
    "level": "info",
    "output": "/tmp/sing-box.log"
  },
  "dns": {
    "servers": [
      {
        "tag": "google",
        "address": "tls://8.8.8.8",
        "detour": "proxy"
      },
      {
        "tag": "local",
        "address": "114.114.114.114",
        "detour": "direct"
      }
    ]
  },
  "inbounds": [
    {
      "type": "socks",
      "tag": "socks-in",
      "listen": "127.0.0.1",
      "listen_port": 1080
    },
    {
      "type": "http",
      "tag": "http-in",
      "listen": "127.0.0.1",
      "listen_port": 8080
    },
    {
      "type": "tun",
      "tag": "tun-in",
      "interface_name": "utun4",
      "inet4_address": "172.16.0.1/30",
      "auto_route": true,
      "strict_route": false
    }
  ],
  "outbounds": [
    {
      "type": "selector",
      "tag": "proxy",
      "outbounds": ["auto"]
    },
    {
      "type": "urltest",
      "tag": "auto",
      "outbounds": ["proxy-node-1", "proxy-node-2"]
    },
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ]
}
```

### 3. Subscription URL (конвертация из Shadow Rocket)

Подписка Shadow Rocket — base64-encoded список серверов. sing-box использует JSON.

**Конвертация вручную:**
```bash
# Получить подписку
curl -sL "https://your-subscription-url" | base64 -d | jq '.'
```

**Автоматическая конвертация через sub-store:**
```bash
# sub-store CLI конвертирует подписки в sing-box формат
npx sub-store
```

**Или через сторонние конвертеры:**
- https://sub.v1.mk/ — онлайн конвертер
- https://github.com/tindy2013/subconverter — локальный конвертер

### 4. Запуск

```bash
sing-box run -c config.json
```

Для systemd / launchd:
```bash
# macOS launchd
cp ~/projects/tools/sing-box/config.json ~/Library/LaunchAgents/
# см. launchd plist ниже
```

## Integration с Internet Pro

Можно комбинировать: sing-box на pro как SOCKS5-прокси, Internet Pro на dispo шлёт трафик через SSH туннель на pro:

```
dispo → SSH tunnel → pro → sing-box (SOCKS5 :1080) → интернет
```

Для этого на pro sing-box слушает `127.0.0.1:1080`, а SSH туннель с dispo форвардится туда же.

## Полезные команды

```bash
# Проверка конфига
sing-box check -c config.json

# Версия
sing-box version

# Логи в реальном времени
tail -f /tmp/sing-box.log

# Тест DNS
sing-box tools fetch -c config.json https://google.com

# Правила маршрутизации
sing-box rule-set match -c config.json --domain google.com
```

## Сравнение с Shadow Rocket

| Критерий | Shadow Rocket | sing-box |
|----------|-----------|----------|
| GUI | Да | Нет (CLI only) |
| Размер | 35MB | ~15MB |
| Зависимости | macOS App Store | Go binary |
| Headless | Нет (нужен экран) | Да |
| Subscription | Встроенный парсер | Через sub-store/конвертер |
| TUN | Встроен | Встроен |
| Обновления | App Store | brew upgrade |
