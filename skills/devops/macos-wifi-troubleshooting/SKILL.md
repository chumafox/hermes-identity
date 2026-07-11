---
name: macos-wifi-troubleshooting
description: Диагностика и восстановление Wi-Fi на macOS, особенно Apple Silicon (M1+). BPF-ошибки, сброс драйвера, audit сети.
triggers:
  - "wi-fi не работает"
  - "wifi inactive"
  - "bpfAttach failed"
  - "en0 status inactive"
  - "не могу включить wifi"
  - "сетевой аудит"
---

# macOS Wi-Fi Troubleshooting (Apple Silicon)

## Правила безопасности (!!!)

**НИКОГДА не выполняй на Apple Silicon (M1/M2/M3/M4) — ЭТО КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ:**

```
sudo ifconfig en0 down         # ❌❌❌ ЛОМАЕТ драйвер Broadcom (BCM4378) на уровне IOKit
sudo ifconfig en0 up           # ❌❌❌ не восстанавливает после down
```

Последствия гарантированы и необратимы без ребута:
1. BPF-кэш зависает: `bpfAttach(12) failed (17)` (EEXIST)
2. MAC-адрес en0 меняется на рандомный, вернуть не удаётся
3. en0 навсегда `status: inactive` до ребута
4. Тогл Wi-Fi в GUI перестаёт реагировать полностью
5. Перезагрузка airportd, launchctl, kextstat — ничего не помогает
6. **Единственный выход — полный ребут macOS**

**Правильный способ:** только `networksetup -setairportpower en0 {on|off}`. Никаких `sudo ifconfig` на en0. Никогда.

На Apple Silicon драйвер Wi-Fi (IO80211 + AppleBCMWLANSkywalkInterface) не обрабатывает корректно цикл down/up на уровне IOKit. После такого:
- BPF-кэш зависает: `bpfAttach(12) failed (17)` — ошибка EEXIST
- MAC-адрес меняется на рандомный (spoofed), вернуть не даёт
- en0 навсегда остаётся `status: inactive`
- **Единственный выход — ребут**

## Что можно делать безопасно

### Включение/выключение питания (безопасно)
```bash
networksetup -setairportpower en0 off
networksetup -setairportpower en0 on
```

### Сброс airportd (безопасно)
```bash
sudo pkill -9 airportd
# launchd перезапустит автоматически
```

### Сброс DNS
```bash
sudo killall -HUP mDNSResponder
```

### Полный аудит сети
```bash
# Состояние интерфейсов
ifconfig -a | grep -E "^[a-z].*:" | sort

# Активный интерфейс и его IP
ifconfig en5 | grep 'inet '

# DNS resolvers
scutil --dns

# Proxy settings
scutil --proxy

# Routing table
netstat -rn -f inet | head -20

# Service order
networksetup -listnetworkserviceorder

# MAC-адреса устройств
networksetup -listallhardwareports

# Сохранённые Wi-Fi сети
networksetup -listpreferredwirelessnetworks en0
```

### Подключение к Wi-Fi
```bash
networksetup -setairportnetwork en0 "SSID" "password"
```

Если `Could not find network` — сеть не в зоне видимости. Не перебирай имена — спроси у пользователя.

## Приоритет сервисов

Приоритет интерфейсов влияет на маршрут default gateway:

```bash
# Изменить порядок (iPhone USB первый, Wi-Fi второй)
networksetup -ordernetworkservices "iPhone USB USB" "Wi-Fi"
```

**Типичная задача:** Wi-Fi для локальной сети, iPhone USB для интернета.
1. Оставляем `iPhone USB USB` первым (default route → iPhone)
2. Включаем Wi-Fi вторым (локальный доступ, но не default gateway)
3. Интернет продолжает идти через iPhone, даже когда Wi-Fi подключён

## Диагностика BPF-ошибки

Симптомы:
- `en0: status: inactive` после циклов включения
- В логах: `bpfAttach(12) failed (17)` — ошибка 17 = EEXIST
- MAC-адрес en0 изменился и не возвращается к оригиналу

**Решение:** ребут. Ничего софтового не помогает.

Проверка оригинального MAC:
```bash
networksetup -getmacaddress en0
```

## Сканирование сетей

В macOS 14+ команда `airport` не найдена. Сканировать можно через:
- `system_profiler SPAirPortDataType` (только подключённая сеть)
- GUI — Option+клик на Wi-Fi иконку в меню-баре

## Полезные проверки

```bash
# Кто держит сетевое устройство
lsof -nP +c 0 | grep -E "en0|en5"

# Логи Wi-Fi драйвера
log show --predicate 'process == "kernel" AND eventMessage contains "bpfAttach"' --last 5m

# Состояние процесса airportd
ps aux | grep airportd

# NVRAM параметры Wi-Fi
nvram -p | grep -i wifi
```

## VPN-on-demand и utun интерфейсы

Happ, Shadowrocket и другие VPN-клиенты создают utun интерфейсы при старте системы (даже в отключённом состоянии в Service Order). Эти utun могут перехватывать IPv6 default route и ломать интернет, особенно когда основной интернет идёт через iPhone USB (en5).

### Симптом: после ребута интернет не работает через iPhone USB (en5)

После перезагрузки Happ и/или Shadowrocket создают utun-интерфейсы (даже будучи в статусе Disconnected в Service Order). Эти utun перехватывают IPv6 default route. Интернет через iPhone USB (en5) полностью пропадает. **Та же проблема на Mac Pro** — ZTE (en8) даёт IPv6, но utun перехватывают default IPv6, ломая интернет.

**Признак:** ping до 172.20.10.1 работает, ping до bing.com — таймаут.

**Проверка:**
```bash
netstat -rn -f inet | grep default
# default            172.20.10.1        UGScg                 en5        ← OK
# default            192.168.104.1      UGScIg                en0        ← OK (только локальный)
# default            link#17            UCSIg             bridge0      ← OK

netstat -rn -f inet6 | grep default
# default            fe80::%utun0       UGcIg               utun0      ← ПРОБЛЕМА
# default            fe80::%utun1       UGcIg               utun1      ← ПРОБЛЕМА
# ...
```

### Решение: остановить VPN и погасить utun

```bash
# Остановить VPN сервисы
scutil --nc stop "Happ"
scutil --nc stop "Shadowrocket"

# Погасить все висящие utun интерфейсы
for iface in utun0 utun1 utun2 utun3 utun4 utun5 utun9; do
  sudo ifconfig "$iface" down
done

# Проверить что интернет появился
ping -c 2 bing.com
```

### Автоматизация через launchd (чтобы не делать руками после каждого ребута)

Создать скрипт `~/bin/fix-network-after-reboot.sh`:

```bash
#!/bin/bash
# Останавливает Happ и Shadowrocket, гасит utun интерфейсы
/usr/sbin/scutil --nc stop "Happ" 2>/dev/null
/usr/sbin/scutil --nc stop "Shadowrocket" 2>/dev/null
sleep 2
for iface in utun0 utun1 utun2 utun3 utun4 utun5 utun9; do
  /sbin/ifconfig "$iface" down 2>/dev/null
done
# Проверить что default пошёл через en5
if /usr/sbin/netstat -rn -f inet | grep -q "^default.*en5"; then
  echo "OK: Internet via en5 (iPhone USB)"
else
  echo "WARN: default route not via en5"
fi
```

Launchd агент `~/Library/LaunchAgents/com.user.fix-network.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.fix-network</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/jenyanovak/bin/fix-network-after-reboot.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>30</integer>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/fix-network.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/fix-network.log</string>
</dict>
</plist>
```

Установка:
```bash
chmod +x ~/bin/fix-network-after-reboot.sh
launchctl load ~/Library/LaunchAgents/com.user.fix-network.plist
# Проверка
launchctl list | grep fix-network
```

И launchd агент `~/Library/LaunchAgents/com.user.fix-network.plist`:

```xml
...
<key>RunAtLoad</key><true/>
<key>StartInterval</key><integer>30</integer>
...
```

Установка:
```bash
launchctl load ~/Library/LaunchAgents/com.user.fix-network.plist
```

### Список VPN Network Connect сервисов

```bash
scutil --nc list
# * (Disconnected) ... "Shadowrocket"
# * (Disconnected) ... "Happ"
```

Удалить сервис из NC (не через `scutil --nc remove`, этой команды нет):
- Через System Settings → Network → выберить VPN профиль → удалить (-)
- Или через `networksetup -removenetworkservice "Shadowrocket"` (осторожно)

## Разные подсети — доступ к другому Mac

Если два Mac в разных Wi-Fi подсетях (например, SJYH 192.168.104.0/23 и pro 192.168.0.0/24), прямой L2-доступ невозможен.

Решение — добавить маршрут через шлюз SJYH:
```bash
sudo route add -net 192.168.0.0/24 192.168.104.1
```

Но если шлюз не форвардит между подсетями — Mac не будет виден, даже с правильным маршрутом. Проверка:
```bash
ping -c 2 192.168.0.95          # не ответит без форвардинга
arp -a | grep 192.168.0.95       # не появится в ARP
nc -z -G 3 -w 2 192.168.0.95 22 # SSH closed
```

В таком случае нужен альтернативный путь: Thunderbolt Bridge (прямое соединение), iPhone USB (если оба в одной USB-сети), или запись в `/etc/hosts`.

## Декларативное управление сетевым состоянием двух Mac

Для задачи «один Mac (dispo) управляет сетью второго Mac (pro) через SSH» используй подход.

**ВНИМАНИЕ:** Применяй паттерн только когда:
- Есть SSH-доступ к второму Mac
- Пользователь явно попросил декларативное управление
- Это именно настройка сети между двумя Mac в одной локальной сети

**НЕ используй этот паттерн для** одноразовой диагностики или когда достаточно одной команды через SSH.

### Реальная сетевая архитектура (2026-07-08, каюта)

```
dispo (M1 Air) ──WiFi SJYH── pro (M1 Pro)
    │ 192.168.104.10      192.168.103.70  │
    │                       │             │
    │                   ┌───┴───┐         │
    │                   │ ZTE   │ USB     │
    │                   │ модем │ моб.    │
    │                   └───┬───┘ интернет│
    │                       │             │
    │              Shadowrocket VPN       │
    │              Hysteria2 server:8889  │
    │                       │             │
    │  ┌────────────────────┘             │
    │  │ sing-box TUN                     │
    │  │ ← Hysteria2 клиент               │
    │  │ (в Shadowrocket на dispo)        │
    │  └────────── WAN ────→ Google/GitHub│
    │                                     │
    └──────── iPhone USB ───→ fallback    │
```

**Два режима работы dispo:**
1. **Основной:** интернет через Hysteria2 → Shadowrocket на pro → ZTE (sing-box TUN)
2. **Запасной:** интернет через iPhone USB (прямой доступ)

### Структура

```
~/Network/
├── desired_state.yaml          # YAML с желаемым состоянием сети
└── apply_network_state.sh      # Скрипт проверки и восстановления
```

Файлы живут на обоих Mac (создаются на dispo, копируются на pro через scp).

На pro запущен Hysteria2 сервер (как launchd-демон или вручную):
```bash
# Hysteria2 конфиг: ~/.config/hysteria/server.yaml
# Пароль совпадает с тем что в Shadowrocket на dispo
hysteria server --config ~/.config/hysteria/server.yaml
```

На dispo Shadowrocket настроен на Hysteria2 подключение (host: admin-admin.local, port: 8889, password: ...).

### desired_state.yaml — декларация (pro)

```yaml
desired_state:
  service_order:
    - "ZTE Mobile Broadband"       # 1-й — физический WAN
    - Wi-Fi                        # 2-й — только локальный доступ
    - "USB 10/100/1000 LAN"
    - "Thunderbolt Bridge"
    - "iPhone USB"
    - Shadowrocket                 # VPN поверх ZTE

  zte:
    interface: en8
    dhcp: true
    ipv6: automatic

  wifi:
    network: SJYH
    local_only: true               # default route inferior (флаг I)

  shadowrocket:
    state: enabled                 # включён в service order
    user_manages: true             # пользователь включает вручную

  internet:
    via: zte + shadowrocket        # ZTE → Shadowrocket VPN → WAN
    check_hosts:
      - 223.5.5.5
      - bing.com

  local:
    check_hosts:
      - 192.168.104.10             # MacBook Air (dispo)
```

### apply_network_state.sh — логика (pro)

Скрипт проверяет по порядку:
1. **Порядок сервисов** — ZTE первый (исправить `networksetup -ordernetworkservices`)
2. **Default route** — через en8 (если нет — `route add -net default <gw>`). Если Shadowrocket активен — через utun (VPN поверх ZTE) — это нормально
3. **Интернет** — ping до 223.5.5.5, bing.com
4. **Локальный доступ** — ping до Air (dispo) через Wi-Fi

**Не делает:**
- Не запускает Shadowrocket автоматически (пользователь сам включает)
- Не останавливает Happ (его нет на pro)

### Деплой на второй Mac

```bash
# Скопировать файлы
scp -i ~/.ssh/id_ed25519_headless \
  ~/Network/desired_state.yaml \
  ~/Network/apply_network_state.sh \
  admin@<pro-ip>:~/Network/

# Запустить удалённо
ssh -i ~/.ssh/id_ed25519_headless admin@<pro-ip> \
  "~/Network/apply_network_state.sh"
```

### Типовые метрики проверки (pro)

| Что проверять | Команда | Ожидание |
|--------------|---------|----------|
| Service Order | `networksetup -listnetworkserviceorder` | ZTE (1), Wi-Fi (3) |
| Default route | `netstat -rn -f inet \| grep default` | `en8` (ZTE) |
| VLAN | `netstat -rn -f inet \| grep default \| grep en0` | `UGScIg` (I = inferior) — это OK |
| VPN active | `scutil --nc list` | Disconnected |
| DNS | `scutil --dns \| grep nameserver` | 223.5.5.5, 119.29.29.29 |
| Интернет | `ping -c 1 -W 3 223.5.5.5` | OK |
| Интернет | `ping -c 1 -W 3 8.8.8.8` | OK (через Китай ~350ms) |

### Метка I (inferior) в routing

В `netstat -rn`:
- `UGScg` — основной default маршрут (без I)
- `UGScIg` — inferior маршрут (с I = менее предпочтительный)

Если Wi-Fi default route в таблице с флагом `I` — он не мешает ZTE default route, система использует ZTE.

## Cache
- 223.5.5.5 (AliDNS), 119.29.29.29 (DNSPod) — китайские DNS
- Apple Silicon BCM4378 не терпит `ifconfig down/up`
- Подмена MAC на M1 через `ifconfig ether` не работает (драйвер сбрасывает)
- Ребут — единственное полное восстановление после BPF-сбоя
- Happ и Shadowrocket после ребута создают utun и ломают IPv6 default — нужен launchd автофикс
- Между разными подсетями (192.168.104.0/23 и 192.168.0.0/24) прямой ping не работает без форвардинга на роутере
