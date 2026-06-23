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

## Common Offenders on M1 8GB

| Process | Typical RSS | Notes |
|---------|-------------|-------|
| Yandex Helper (Renderer) | 180-590MB | Multiple renderers, biggest hog |
| opencode | 140-170MB | Can hang after cancel (31% CPU) |
| omlx-server | 18-284MB | Grows when model loaded |
| Hermes (python3) | 60-85MB | Normal |
| Brave Browser | 50-55MB | Per process |
| agy | 374MB | If running |
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
