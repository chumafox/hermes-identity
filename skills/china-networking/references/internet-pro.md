# Internet Pro — SSH tunnel internet sharing

**Tool:** `~/projects/tools/internet-pro/internet_pro.py`  
**Alias:** `inpro`  
**Purpose:** Share internet from headless Mac (pro, 192.168.103.70) to display Mac (dispo) via SSH dynamic port forwarding.

## Quick start

```bash
inpro
# P — включить туннель
# K — включить KeepAlive (авто-восстановление после сна)
```

## Limitations

- **TUI-only, no background mode.** internet_pro uses Python `curses` and requires a terminal. You CANNOT run it in the background (via `&`, terminal background, or nohup) — it crashes with `_curses.error: cbreak() returned ERR`. Always open it in a dedicated terminal window/tab.
- **Network change breaks tunnel.** When the display Mac switches networks (e.g., ship WiFi → BT tethering from iPhone), the SSH tunnel to pro Mac dies because pro is on the old network (`192.168.103.70`). internet_pro must be restarted on the new network. If the new network can't reach pro (different subnet), the tunnel won't re-establish.
- **System proxy survives tunnel death.** internet_pro sets macOS system proxy to `127.0.0.1:8888` (HTTP) and `127.0.0.1:1080` (SOCKS). When the tunnel dies, browsers STILL try to use these ports and fail with "No internet connection". After switching networks without internet_pro, DISABLE system proxy:

```bash
networksetup -setwebproxystate Wi-Fi off
networksetup -setsocksfirewallproxystate Wi-Fi off
```

Then restart browsers for the change to take effect.

## Architecture

```
dispo (нет интернета)
  → SSH -D 1080 → pro (192.168.103.70, есть интернет + utun4 прокси)
    → SOCKS5 :1080
    → HTTP bridge :8888 (для pip/npm/cargo)
    → system proxy via networksetup (опционально, клавиша Y)
```

## KeepAlive mode (клавиша K)

- Добавляет `-o ServerAliveInterval=15 -o ServerAliveCountMax=3` к SSH
- Если туннель упал (сон/потеря сети) — автоматически переподключается
- Отображает статус в TUI

## Bugfix: статус системного прокси

Функция `get_system_socks_proxy_state()` проверяла `if "Enabled:" in line` — но строка `"Authenticated Proxy Enabled: 0"` тоже содержит `"Enabled:"`, перезаписывая корректное значение. **Фикс:** `line.startswith("Enabled:")`. Аналогично для HTTP.

## Требования

- SSH доступ к pro по ключу (`admin-remote` в `~/.ssh/config`)
- Ключ: `~/.ssh/id_ed25519_headless`

## Файлы

```
~/projects/tools/internet-pro/
├── internet_pro.py              # TUI-клиент (709 строк)
├── internet_sharing_utility.md  # Оригинальная документация
└── README.md                    # Быстрый старт
```
