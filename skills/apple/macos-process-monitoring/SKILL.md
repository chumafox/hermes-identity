---
name: macos-process-monitoring
description: "Monitor macOS processes — CPU, RAM, RSS. Find resource hogs on Apple Silicon (M1 8GB). Kill hanging processes properly."
platforms: [macos]
---

# macOS Process Monitoring

Monitor system resources on macOS (Apple Silicon). Useful on memory-constrained machines (M1 8GB) where runaway processes eat CPU/RAM.

## Quick Commands

```bash
# Top CPU consumers
ps axo pid,pcpu,pmem,rss,comm -r | head -25

# Top RAM consumers
ps axo pid,pcpu,pmem,rss,comm -m | head -25

# RSS is in KB — divide by 1024 for MB
# Example output:
# PID  %CPU %MEM    RSS COMM
# 45081  31.9  2.0 171072 opencode  → 171MB RSS
```

## Battery Drain Diagnosis

Когда пользователь жалуется на быстрый разряд батареи — не просто смотри CPU, а делай три шага:

### 1. Текущее состояние батареи

```bash
pmset -g batt
# → "53%; discharging; 1:54 remaining"
```

### 2. Энергопотребление процессов (POWER)

`top` умеет сортировать по колонке POWER — она показывает энергопотребление каждого процесса относительно других. Это важнее %CPU для диагностики разряда.

```bash
top -l 2 -stats pid,cpu,power,mem,command -o power -n 20 | tail -25
```

Флаг `-l 2` нужен для двух выборок (первая — instant, вторая — усреднённая). Всегда используй `-l 2`.

Колонка POWER — относительная шкала 0.0–10.0+. Процессы с POWER > 3 — подозрительные. > 5 — аномалия.

### 3. Здоровье батареи

```bash
system_profiler SPPowerDataType | grep -E "Cycle Count|Condition|Maximum Capacity"
```

- Cycle Count < 200, Condition = Normal, Max Capacity > 90% — батарея в порядке
- Cycle Count > 800 или Max Capacity < 80% — пора менять

### 4. Причины пробуждения (если батарея уходит в спящем режиме)

```bash
pmset -g log | grep -i "Wake.*reason\|DarkWake\|Wake Requests" | tail -20
```

- `NUB.SPMI0Sw3IRQ` + `rtc/Maintenance` — нормальные фоновые пробуждения (~каждые 15-20 мин, 45 сек)
- `USB-C_plug` — физическое подключение кабеля
- `com.apple.dasd:501:com.apple.searchd.heartbeat` — Spotlight heartbeat
- Много частых DarkWake (>1 в 5 мин) = проблема

## Common Offenders on M1 8GB

| Process | Typical RSS | Notes |
|---------|-------------|-------|
| Yandex Helper (Renderer) | 180-590MB | Multiple renderers, biggest hog. 25+ processes. |
| opencode | 140-170MB | Can hang after cancel (31% CPU, loops build/compaction). Kill manually. |
| agy | 200-375MB | **Main battery killer.** `agy --continue` can hang for 90+ min CPU-time eating a full core. Проверять CPU time (`90:25.99` = 90 мин). Kill and restart. |
| Hermes (python3) | 60-340MB | Two+ processes possible (Hermes + bridge workers). PID 10672 main, PID 9350 bridge. |
| Ghostty | 553MB | High RSS but idle CPU — memory usage, not battery. |
| WindowServer | 468MB | Many open windows = high memory. Expected. |
| CloudflareWARP | 93MB | VPN — minimal CPU, fixed overhead. |
| IINA | 243MB | Media player — power impact depends on playback. |
| Finder | 135MB | **>2% CPU / >1 POWER = abnormal.** 7% CPU значит Finder завис или активно индексирует. Kill + relaunch: `killall Finder`. |
| omlx-server | 18-284MB | Grows when model loaded. launchd-managed — kill -9 + launchctl unload. |
| Brave Browser | 50-55MB | Per process |
| airportd | 16MB | Spikes to 17% CPU occasionally |

## Killing Processes

### Hierarchy of signals

```bash
kill PID           # TERM (15) — вежливо попросить
kill -HUP PID      # HUP (1) — перезагрузить (перечитать конфиг)
kill -INT PID      # INT (2) — как Ctrl+C
kill -KILL PID     # KILL (9) — безусловно, ядро убивает
```

### Order

1. `kill PID` — вежливо (TERM)
2. Подождать 3-5 секунд
3. Если жив — `kill -9 PID` — принудительно

`kill -9` без первого шага — грубо, процесс не успевает сохранить данные.

### By name

```bash
pkill -f process-name    # TERM по имени (осторожно — может зацепить не то)
pkill -9 -f process-name # KILL по имени
```

### launchd-managed processes

Если процесс перерождается после kill (PPID=1), у него есть launchd plist:

```bash
# Найти plist
find /Library/LaunchAgents /Library/LaunchDaemons ~/Library/LaunchAgents -name "*keyword*"

# Выгрузить из launchd
launchctl unload ~/Library/LaunchAgents/com.example.plist

# Удалить plist (чтобы не загрузился при перезагрузке)
rm ~/Library/LaunchAgents/com.example.plist

# Убить процесс
kill -9 PID
```

## Re-checking

После убийства процесса всегда перепроверять:

```bash
ps axo pid,pcpu,pmem,rss,comm -r | head -25
```

Некоторые процессы (omlx-server, opencode) могут переродиться с новым PID.

## Pitfalls

- **macOS ps ≠ Linux ps.** Флаг `--sort` не работает. Используй `-r` (reverse sort by CPU) или `-m` (sort by RSS).
- **RSS в KB,** не MB. 171072 RSS = ~171MB. Дели на 1024.
- **Процесс может игнорировать TERM** (SIGKILL-безопасные: omlx-server, launchd-демоны). Сразу используй `kill -9`.
- **opencode после cancel** может виснуть в цикле `agent=build` / `agent=compaction` с 31% CPU. Проверять `ps` и убивать вручную.
- **Yandex Browser** — самый жирный по памяти на этой системе (до 590MB на один рендерер).

### ОПАСНО: `sudo ifconfig en0 down` на Apple Silicon

**НИКОГДА не делай `sudo ifconfig en0 down` на M1/M2/M3/M4 Mac.** Это ломает драйвер Broadcom Wi-Fi (BCM4378) на уровне IOKit. Симптомы:

- `ifconfig en0` показывает `status: inactive` даже после `up`
- В логах kernel: `bpfAttach(12) failed (17)` — ошибка EEXIST, BPF-канал не освобождается
- MAC-адрес en0 меняется на случайный, вернуть оригинал через ifconfig не даёт
- Тогл Wi-Fi в меню-баре перестаёт реагировать
- `networksetup -setairportpower` пишет `On` но en0 остаётся inactive

**Что делать если уже сломал:**
```bash
# Перезагрузить Mac — только это фиксит
sudo shutdown -r now
```

**Почему так:** на Apple Silicon драйвер Wi-Fi использует IO80211SkywalkInterface. ifconfig down/up на нём не перезагружает firmware чипа, но сбрасывает internal state. BPF-attach сбивается и не восстанавливается без полной переинициализации драйвера (только ребут).

**Безопасные альтернативы:**
- `networksetup -setairportpower en0 off/on` — безопасно, не ломает драйвер
- `sudo launchctl unload /System/Library/LaunchDaemons/com.apple.airportd.plist` + load — мягкий перезапуск службы Wi-Fi
- `sudo ifconfig en0 down` — **ЗАПРЕЩЕНО** на Apple Silicon

## Battery health check summary

После сбора данных формат ответа пользователю:

```
**Батарея:** N циклов, X% ёмкости — [в порядке|пора менять].

**Главный виновник — `process-name`**
```
process-name args
— X% CPU, YMB RAM, Z минут CPU-времени
```

**Остальные подозреваемые:**
| Процесс | POWER | %CPU | RAM | Примечание |
```

Перечислять только процессы с POWER > 0.5. Если есть явный лидер (POWER вдвое больше второго) — выделить его отдельно как главного виновника.
