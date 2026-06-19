---
name: internet-pro
description: "Internet Pro — TUI-утилита для интернета экранного Mac через SSH-туннель на безголовый Mac. SOCKS5 + HTTP bridge + system proxy + keepalive."
tags: [ssh-tunnel, socks5, proxy, macos, networking, tui, internet-sharing]
---

# Internet Pro

**Internet Pro** — curses-based TUI for sharing internet from a headless Mac (pro) to the display Mac (dispo) via SSH dynamic port forwarding.

## Critical: Network Architecture

**Dispo (display Mac) has NO internet of its own.** Both Macs are on the same ship/local WiFi only (no WAN). Internet exists ONLY through pro's ZTE 4G/5G modem connected via Type-C. Pro's Shadowrocket TUN (utun4) routes all TCP traffic through a VPN node. Without internet_pro, dispo is completely offline — no Google, no GitHub, no anything.

```
ship WiFi (LAN only, no WAN)
├── dispo (M1 Air) ← NO internet
│   └── SSH -D 1080 → pro ← единственный путь к WAN
└── pro (M1 Pro)
    ├── ZTE 4G/5G Type-C ← единственный интернет
    └── Shadowrocket TUN (utun4) ← прокси для доступа к Google/GitHub
```

**KeepAlive is essential** — ship WiFi can be unstable, pro may go to sleep.

## Files

- `~/projects/tools/internet-pro/internet_pro.py` — main script (709 lines)
- `~/projects/tools/internet-pro/README.md` — quick start
- `~/projects/tools/internet-pro/internet_sharing_utility.md` — full docs
- `~/.internet_pro.json` — config (saved via `C` key)
- `/tmp/internet_pro.socks` — SSH control socket

## Reference Files

- `references/vibe-coding-prompt.md` — архитектурный промпт для пересборки inpro AI-агентом (vibe-coding)

## Quick Start

```bash
inpro
# TUI opens. Press:
#   P — включить туннель
#   K — включить KeepAlive (авто-восстановление после сна)
#   Y — системный прокси macOS
#   S — shell с прокси
#   Q — выход
```

## Prerequisites

### 1. SSH config (`~/.ssh/config`) for keyless auth

The script defaults to host `admin-remote`. Add to `~/.ssh/config`:

```
Host admin-remote
  HostName 192.168.103.70
  User admin
  IdentityFile ~/.ssh/id_ed25519_headless
  PreferredAuthentications publickey
  StrictHostKeyChecking no
  ServerAliveInterval 5
```

### 2. SSH key on pro

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_headless admin@192.168.103.70
```

## Key Features

### TUI Controls

| Key | Action | Description |
|-----|--------|-------------|
| `P` | Tunnel toggle | Connect/disconnect SSH SOCKS5 tunnel |
| `Y` | System proxy | Toggle macOS system-wide proxy (via networksetup, needs sudo) |
| `K` | KeepAlive | Auto-reconnect tunnel if it drops (sleep/wake, network blips) |
| `N` | Cycle interface | Switch network interface for system proxy |
| `S` | Spawn shell | Opens subshell with http_proxy/https_proxy set |
| `C` | Configure | Change SSH host/user/port (saved to ~/.internet_pro.json) |
| `Q` | Quit | Close tunnel and exit |

### Ports

- **SOCKS5**: `127.0.0.1:1080` — SSH dynamic forwarding
- **HTTP bridge**: `127.0.0.1:8888` — HTTP CONNECT → SOCKS5 conversion
- **System proxy**: Uses selected network interface (default: Wi-Fi)

### KeepAlive

When enabled (`K`), the script:
1. Uses SSH `ServerAliveInterval=15 ServerAliveCountMax=3` — detects dropped connections quickly
2. Monitors port 1080 every second
3. Auto-restarts the tunnel if dropped (sleep/wake, network blips)
4. Restarts HTTP bridge automatically with the tunnel

## proxy_on Integration

The zsh function `proxy_on` sets terminal proxy env vars (default: SOCKS5 :1082, HTTP :1083 — Shadowrocket). To use with Internet Pro instead:

```bash
# Fix proxy_on in .zshrc:
proxy_on() {
  export http_proxy=http://127.0.0.1:8888
  export https_proxy=http://127.0.0.1:8888
  export all_proxy=socks5://127.0.0.1:1080
  export HTTP_PROXY=http://127.0.0.1:8888
  export HTTPS_PROXY=http://127.0.0.1:8888
  export ALL_PROXY=socks5://127.0.0.1:1080
}

# Or use inpro's Shell (S key) — already sets env vars

# Or auto-detect: if port 8888 open → Internet Pro, else if 1083 → Shadowrocket
```

## Russian Localization

The entire TUI is in Russian. Translations done via direct string replacements:
- All UI labels, statuses, and control descriptions
- Terminal prompts (SSH password, sudo prompts)
- Log messages
- Config wizard

## Troubleshooting

### SSH master socket alive but port not listening

Симптом: `ssh -S /tmp/internet_pro.socks -O check admin@admin-remote` возвращает `Master running (pid=1407)`, но `lsof -i :1080` пустой, и curl не может подключиться.

Причина: SSH-соединение оборвалось (remote host изменил IP, DNS перестал резолвиться, сеть упала), но мастер-процесс SSH всё ещё висит с контрольным сокетом. Туннель мёртв, но процесс жив.

Диагностика:
```bash
# Проверить что host резолвится
ping admin-remote  # может не работать — ping не читает SSH config!
# А лучше:
ssh admin-remote -o BatchMode=yes -o ConnectTimeout=5 echo "OK"

# Проверить порт
lsof -i :1080 -P -n | head -3

# Проверить контрольный сокет
ls -la /tmp/internet_pro.socks
```

Фикс:
```bash
# Убить старый туннель
ssh -S /tmp/internet_pro.socks -O exit admin@admin-remote 2>/dev/null
rm -f /tmp/internet_pro.socks

# Перезапустить через TUI (нажать P)
# Или вручную:
ssh -M -S /tmp/internet_pro.socks -f -N -D 1080 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  admin@admin-remote
```

**Важно:** `ping admin-remote` может фейлиться даже когда SSH работает — потому что ping не читает `~/.ssh/config`, а SSH читает. Используй `ssh admin-remote echo OK` для реальной проверки.
- Check SSH key: `ssh admin-remote -o BatchMode=yes echo OK`
- If password prompted: SSH key not accepted on pro
- Default host is `admin-remote` — must match `~/.ssh/config`

### UI shows wrong system proxy status
- Fixed in v1.1: `"Enabled:" in line` → `line.startswith("Enabled:")`
- The old check matched `"Authenticated Proxy Enabled: 0"` and overwrote state

### Bridge status shows "ОСТАНОВЛЕН" when HTTP bridge is actually running

**Симптом:** в TUI статус HTTP моста — "ОСТАНОВЛЕН", хотя в логах пишет "HTTP мост автоматически запущен", и порт 8888 реально открыт (curl через него работает).

**Причина:** статус bridge определялся через глобальный флаг `bridge_running`, который устанавливался внутри треда `run_bridge()` после bind/listen. Race condition — `draw_ui()` проверяла флаг до того как тред успевал его выставить. Кроме того, если порт 8888 уже был занят (предыдущий запуск), `run_bridge()` падал на bind и сбрасывал флаг в False, хотя порт был открыт и работал.

**Фикс (3 части):**

1. Статус bridge проверять через `is_port_in_use(port)` вместо глобального флага:
```python
bridge_status = "АКТИВЕН" if is_port_in_use(state['local_http_port']) else "ОСТАНОВЛЕН"
```

2. В главном цикле перед попыткой перезапуска проверять что порт реально не открыт:
```python
bridge_port_open = is_port_in_use(state['local_http_port'])
if state['socks_active'] and not bridge_port_open and not bridge_running:
    start_bridge_thread(...)
```

3. Флаг `bridge_running = True` ставить **оптимистично** сразу при вызове `start_bridge_thread()`, до старта треда — чтобы TUI не показывал "ОСТАНОВЛЕН" в промежутке между вызовом и bind.

### Column alignment: bridge status overwrites parenthesis

**Симптом:** `HTTP/HTTPS мост:  127.0.0.1:8888 (ОСТАНОВЛЕН)` — скобка `(` перезаписывается статусом, получается `8888 ОСТАНОВЛЕН)`.

**Причина:** строка `HTTP/HTTPS мост:  127.0.0.1:8888 (` заканчивается на колонке 38 (символ `(`). Статус пишется с колонки 38, перезаписывая `(`.

**Фикс (применён 16.06.2026):** сдвинуть статус на 1 колонку — писать с колонки 39:
```python
stdscr.addstr(10, 5, f"HTTP/HTTPS мост:  127.0.0.1:{state['local_http_port']} (")
stdscr.addstr(10, 39, bridge_status, bridge_color | curses.A_BOLD)
stdscr.addstr(10, 39 + len(bridge_status), ")")
```

### Bridge status shows "ОСТАНОВЛЕН" when actually working (persistent)

**Симптом:** после применения всех фиксов (is_port_in_use, optimistic flag, column fix) строка всё ещё показывает `8888 (ОСТАНОВЛЕН)` хотя HTTP bridge реально работает — curl через порт 8888 проходит, lsof показывает LISTEN.

**Текущая диагностика:** `is_port_in_use()` на строке 107-110 использует `connect_ex()` с таймаутом 0.2с. Возможно race condition между вызовом `is_port_in_use()` в `draw_ui()` и моментом когда bridge thread успевает открыть порт. Либо порт открыт процессом от предыдущего запуска, а `bridge_running` флаг сброшен.

**Проверить:**
```bash
lsof -i :8888 -P -n | head -5
# Если Python процесс есть — bridge работает, проблема в draw_ui
# Если нет — bridge не стартовал
```

### KeepAlive not reconnecting
- Check SSH key works without password
- Tunnel uses SSH control socket at `/tmp/internet_pro.socks`
- If socket is stale: `rm -f /tmp/internet_pro.socks`

### Network switch: tunnel dies silently

When dispo switches networks (ship WiFi → BT tethering, or back), the SSH control socket survives but the tunnel's TCP connection to pro becomes stale. The SSH master process stays alive holding the control socket, but `lsof -i :1080` shows nothing and no data flows.

**Fix:** after any network change, kill and restart:
```bash
ssh -S /tmp/internet_pro.socks -O exit admin@admin-remote 2>/dev/null
rm -f /tmp/internet_pro.socks
kill $(lsof -ti :1080) 2>/dev/null
# Then re-launch internet_pro TUI
```

### System HTTPS proxy is separate from HTTP

macOS `networksetup` manages HTTP and HTTPS proxy as **two independent settings**. Disabling HTTP (`setwebproxystate off`) does NOT disable HTTPS (`setsecurewebproxystate`). When re-enabling for internet_pro:

```bash
# ENABLE both:
networksetup -setwebproxy Wi-Fi 127.0.0.1 8888
networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 8888

# DISABLE both:
networksetup -setwebproxystate Wi-Fi off
networksetup -setsecurewebproxystate Wi-Fi off

# CHECK actual state (all proxy types in one view):
scutil --proxy | grep -E "HTTP|SOCKS|Enable"
```

`scutil --proxy` is more reliable than `networksetup` for reading the actual system proxy state — it shows all proxy types in one dictionary. Use this for verification.

## HTTP Bridge (inpro)

HTTP bridge (`~/bin/inpro`) — конвертирует HTTP/HTTPS запросы в SOCKS5-соединения. Слушает `127.0.0.1:8888`, форвардит через SOCKS5 `127.0.0.1:1080`.

### Управление

```bash
inpro              # запустить (фоново)
inpro stop         # остановить
```

Скрипт: `~/bin/inpro` — Python asyncio, понимает HTTP (GET/POST) и HTTPS (CONNECT). Логи в stderr.

### Как это работает

1. HTTP-запрос (`GET http://example.com/`) — парсит URL, извлекает хост/порт/путь, делает SOCKS5 CONNECT, переписывает request-line с путём вместо полного URL
2. HTTPS CONNECT — устанавливает SOCKS5 CONNECT к целевому хосту, шлёт `HTTP/1.1 200 Connection Established`, затем релеит байты напрямую (туннель)

### Почему не privoxy/tinyproxy

brew из Китая не качается. Python-скрипт работает без установки, использует только stdlib (asyncio, struct, socket).

### Диагностика

```bash
# Проверить что порт слушает
lsof -i :8888 | grep LISTEN

# Проверить что bridge отвечает
curl -x http://127.0.0.1:8888 -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://google.com

# Проверить SOCKS5 напрямую (минуя bridge)
curl -x socks5://127.0.0.1:1080 -s -o /dev/null -w "%{http_code}" --connect-timeout 10 https://google.com
```

### Известные проблемы

- Если bridge не отвечает, хотя порт слушает — проблема в SOCKS5 рукопожатии внутри bridge. Проверить логи: `inpro 2>&1` (не фоном).

### Browser proxy bypass (--no-proxy-server)

After disabling system proxy, browsers that were launched before the change may still cache the proxy setting in their Network Service process. Chromium browsers (Brave, Yandex, Chrome) need a full restart with:
```bash
open -a "Brave Browser" --args --no-proxy-server
```

Safari uses system proxy exclusively — it only needs the macOS proxy state to be correct (verify via `scutil --proxy`).

### Port conflicts
- Default: SOCKS5=1080, HTTP bridge=8888
- Change via `C` in TUI or edit `~/.internet_pro.json`

### nchat / Telegram MTProto — нюансы прокси

**Симптом:** nchat показывает "offline" или висит на "Connecting 🔒". Контакты могут показывать online, но сообщения не отправляются.

**Диагностика — проверить куда nchat стучится:**
```bash
lsof -c nchat -P | grep TCP
# Ожидаемый адрес: 149.154.171.5:5222 (Telegram MTProto)
# Статус SYN_SENT = нет ответа, ESTABLISHED = соединение есть
```

**Два слоя проксирования:**

1. **SOCKS5 (порт 1080)** — nchat его **не понимает** напрямую. nchat использует системный TCP socket, настройки proxy_host/port в app.conf ожидают HTTP CONNECT, не SOCKS5.
2. **HTTP bridge (порт 8888)** — nchat через него подключается (CONNECT tunnel), НО **сообщения могут не отправляться**, хотя контакты показывают online. HTTP CONNECT + MTProto = коннект есть, но DPI может резать данные после установки туннеля.

**Проверка какой проктип работает:**
```bash
# Включить SOCKS5 (1080) — работает для отправки сообщений:
sed -i '' 's/proxy_port=8888/proxy_port=1080/' ~/.config/nchat/app.conf

# Включить HTTP bridge (8888) — контакты online, но сообщения могут не лететь:
sed -i '' 's/proxy_port=1080/proxy_port=8888/' ~/.config/nchat/app.conf

# Проверить настройки:
grep proxy_ ~/.config/nchat/app.conf
# Ожидается: proxy_host=127.0.0.1, proxy_port=1080 или 8888
```

**Важно:** "Connecting 🔒" в углу nchat — это **индикатор статуса попытки подключения**, а не статическое состояние. 🔒 означает "использую прокси-настройки". Если контакты online и сообщения не летят — проблема в DPI/блокировке MTProto поверх CONNECT, не в самом прокси.

**Альтернатива — TUN:** Shadowrocket utun4 на pro перехватывает весь TCP трафик системно, шифруя MTProto целиком. Через TUN nchat работает без настройки прокси вообще.

### Multiple SSH processes fighting over port 1080

После обрыва туннеля может остаться старый SSH-процесс, удерживающий порт. Новый туннель не стартует (`bind [127.0.0.1]:1080: Address already in use`), старый мёртв.

**Фикс:**
```bash
kill $(lsof -ti :1080) 2>/dev/null
sleep 2
# затем перезапустить через TUI (P) или вручную
ssh -M -S /tmp/internet_pro.socks -f -N -D 1080 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  admin@admin-remote
```

### SSH tunnel alive but TLS fails on remote end

Симптом: SOCKS5 рукопожатие проходит (`SOCKS5 request granted.`), curl соединяется, но TLS handshake обрывается (`SSL_ERROR_SYSCALL`). Туннель forwarding работает, но на удалённой стороне (pro) Shadowrocket TUN отвалился — TCP пакеты доходят до TUN, но VPN-нода не отвечает. ICMP (ping) при этом может работать.

**Диагностика:**
```bash
ssh admin-remote "curl -s --max-time 10 https://github.com"
# Если timeout — проблема в Shadowrocket на pro, не в internet_pro
```

**Фикс:** переподключить Shadowrocket на pro:
```bash
ssh admin-remote 'scutil --nc restart Shadowrocket 2>/dev/null; sleep 5'
```
