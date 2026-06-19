---
name: moonlight-sunshine-streaming
title: Moonlight + Sunshine/Lumen Game Streaming
description: Настройка Moonlight (клиент) и Sunshine/Lumen (сервер) для удалённого рабочего стола и игр между двумя Mac (клиент — экранный Mac, сервер — безголовый Mac c HDMI-дисплеем).
tags: [moonlight, sunshine, lumen, game-streaming, remote-desktop, macos, hardware-encoding]
---

# Moonlight + Sunshine/Lumen Game Streaming

## Компоненты

### Клиент — Moonlight
- Open-source клиент GameStream/Sunshine/Lumen
- macOS Universal binary, VideoToolbox аппаратное декодирование
- Установка: `brew install --cask moonlight`
- Путь: `/Applications/Moonlight.app`
- CLI: `/opt/homebrew/bin/moonlight`

### Сервер — Sunshine или Lumen
- **Sunshine** — открытый сервер (LizardByte)
- **Lumen** — форк Sunshine с дополнительными патчами (виртуальные дисплеи)
- **Несовместимы с VNC** — только GameStream/Sunshine/Lumen протокол

## Быстрый старт

### 1. Установка сервера
На целевую машину (где будет стримиться экран):

```bash
# Sunshine через brew
brew install --cask sunshine

# Или скачать dmg с GitHub:
# https://github.com/LizardByte/Sunshine/releases
```

### 2. Установка клиента
На машину с которой подключаешься:

```bash
brew install --cask moonlight
```

### 3. Подключение

1. Открыть Moonlight на клиентской машине
2. Должен найти сервер автоматически (mDNS/Bonjour)
3. Если не нашёл — Add Host → ввести IP сервера
4. Moonlight покажет 4-значный PIN
5. Открыть браузер → `https://<IP сервера>:47990`
6. Войти (логин/пароль из настройки Sunshine/Lumen)
7. Pair — ввести PIN
8. Выбрать Desktop → стрим

## Переключение между рабочими столами (Mission Control)

Moonlight по умолчанию не перехватывает Ctrl+←/→ для переключения Spaces на *сервере*.

**Способы решения:**

1. **В настройках Sunshine/Lumen Web UI**:
   - `https://<IP>:47990` → `Keyboard/Mouse` → `Keybinds`
   - Поле "Cycle through displays" — задать уникальную комбинацию, которую Moonlight не перехватывает (например `Meta+1`, `Meta+2`)

2. **Настройки Moonlight** (шестерёнка):
   - Включить `Gamepad navigation`
   - Включить `Keyboard passthrough`

3. **Горячие клавиши по умолчанию**:
   - `Ctrl+Shift+←/→` — переключение дисплеев (работает если Moonlight не перехватывает)
   - `Ctrl+Alt+Shift` — переключение режима захвата

## Диагностика скорости

```bash
# Проверить связь
ping <IP сервера>

# Тест пропускной способности
# На сервере:
iperf3 -s -D
# На клиенте:
iperf3 -c <IP сервера> -t 10
```

## Полезные факты

- **HEVC аппаратное кодирование**: на M1 Pro/Max Sunshine/Lumen используют `hevc_videotoolbox` — нагрузка на CPU минимальна
- **Virtual display**: Lumen может создавать виртуальный дисплей, если физический не подключён
- **Bitrate**: по умолчанию часто ~80 Mbps. В Web UI можно увеличить/уменьшить
- **Логин по умолчанию**: admin / admin (Sunshine) или admin / lumen123 (Lumen)

## Pitfalls

- Moonlight НЕ работает с VNC — только GameStream/Sunshine/Lumen
- Если SSH на сервер тупит — вероятно сервер занят стримом, подождать
- После смены WiFi сети IP сервера может измениться — проверять через ARP или Web UI
- Без физического HDMI-дисплея может не быть видеовыхода — использовать virtual display в Lumen или HDMI-ловушку
- Moonlight не находит сервер при смене подсети — добавлять вручную по новому IP
