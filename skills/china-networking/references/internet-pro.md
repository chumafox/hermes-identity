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
    → HTTP bridge :8888 (для pip/npm/cargo) — inpro
    → system proxy via networksetup (опционально, клавиша Y)
```

## Performance: inpro vs direct SOCKS5

**inpro (HTTP bridge :8888) — Python asyncio — ~0.7 MB/s (5.6 Mbps)**
**Direct SOCKS5 (:1080) — native SSH — ~3.9 MB/s (31 Mbps)**

inpro — Python asyncio скрипт (`~/bin/inpro`), он перегоняет данные через SOCKS5 в user-space. Это добавляет **5-6x оверхед**. Если скорость критична — используй SOCKS5 напрямую, минуя inpro:

```bash
# Вместо --proxy http://127.0.0.1:8888:
export ALL_PROXY=socks5://127.0.0.1:1080
export http_proxy=socks5://127.0.0.1:1080
export https_proxy=socks5://127.0.0.1:1080

# curl напрямую:
curl --socks5-hostname 127.0.0.1:1080 https://...
```

**Когда inpro всё ещё нужен:**
- Инструменты, которые не умеют SOCKS5 (старые CLI, pip без socks поддержки)
- Когда нужен HTTP-прокси (некоторые библиотеки не понимают `socks5://` схему)

**Когда SOCKS5 напрямую лучше:**
- Браузеры, curl, wget, git (с `http.proxy=socks5://...`)
- Любые задачи, где скорость важнее совместимости

### Измерение скорости между Mac-ами

```bash
# WiFi скорость Air↔pro (iperf3):
# На pro:
iperf3 -s -1 -D

# На dispo:
iperf3 -c 192.168.103.70 -t 10 -f m

# Ожидание: 100-120 Mbit/s (WiFi 5GHz, 802.11ax)
```

### Измерение скорости интернета через туннель

```bash
# Через SOCKS5 (5MB тест):
curl --socks5-hostname 127.0.0.1:1080 \
  --max-time 30 \
  -o /dev/null -w "%{speed_download} b/s\n" \
  "https://speed.cloudflare.com/__down?bytes=5242880"

# Через inpro:
curl --proxy http://127.0.0.1:8888 \
  -o /dev/null -w "%{speed_download} b/s\n" \
  "https://speed.cloudflare.com/__down?bytes=1048576"
```

**Бутылочное горлышко:** интернет на pro Mac (через Shadowrocket). Если pro выдаёт ~3.5 MB/s, быстрее через туннель не получится — это потолок прокси-провайдера.

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
