# Post-Reboot VPN Recovery — Real Session

## Контекст
- MacBook Air M1 (dispo)
- Интернет через iPhone USB (en5, 172.20.10.4/28)
- Wi-Fi на SJYH (192.168.104.10/23) для локального доступа к Mac Pro
- Happ и Shadowrocket установлены, отключены в Service Order

## Проблема после ребута
1. Happ и Shadowrocket стартуют как VPN-on-demand (NC) — создают utun0-5, utun9
2. utun-интерфейсы перехватывают IPv6 default route
3. Интернет через en5 полностью пропадает
4. IPv4 default всё ещё через en5 (172.20.10.1), но IPv6 default через utun

## Диагностика
```bash
# IPv4 — выглядит нормально
netstat -rn -f inet | grep default
# default 172.20.10.1 UGScg en5

# IPv6 — utun перехватили
netstat -rn -f inet6 | grep default
# default fe80::%utun0 UGcIg utun0
# default fe80::%utun1 UGcIg utun1
# ...

# Интернет не работает
ping -c 2 bing.com
# Request timeout
```

## Решение
```bash
# 1. Остановить VPN
scutil --nc stop "Happ"
scutil --nc stop "Shadowrocket"

# 2. Погасить utun
sudo ifconfig utun0 down
sudo ifconfig utun1 down
sudo ifconfig utun2 down
sudo ifconfig utun3 down
sudo ifconfig utun4 down
sudo ifconfig utun5 down
sudo ifconfig utun9 down

# 3. Проверка
ping -c 2 bing.com
# 64 bytes from 150.171.28.10...
```

## Автоматизация
Создан launchd агент `com.user.fix-network`:
- Скрипт: `~/bin/fix-network-after-reboot.sh`
- Плист: `~/Library/LaunchAgents/com.user.fix-network.plist`
- Запускается: при загрузке (RunAtLoad) и каждые 30 секунд
- Установка: `launchctl load ~/Library/LaunchAgents/com.user.fix-network.plist`

## Mac Pro — своя конфигурация

На безголовом Mac (pro) другая схема:
- **Интернет** через ZTE Mobile Broadband (en8, 192.168.0.0/24)
- **Wi-Fi (SJYH)** — только для локальной сети
- Shadowrocket и Happ тоже установлены и создают utun

### Отличие от dispo

На pro ZTE даёт IPv6 адрес, но IPv4 DHCP выдаёт только link-local (169.254.x.x). При этом default route IPv4 уже идёт через ZTE (192.168.0.1), а IPv6 default route перехватывают utun.

**Проверка после ребута:**
```bash
networksetup -listnetworkserviceorder
# (1) ZTE Mobile Broadband
# (3) Wi-Fi

netstat -rn -f inet | grep default
# default 192.168.0.1 UGScg en8       ← правильно (ZTE)
# default 192.168.102.1 UGScIg en0    ← правильно (I = inferior, Wi-Fi)

# Интернет
ping -c 2 8.8.8.8
# 64 bytes from 8.8.8.8... (если работает)

ping -c 2 223.5.5.5
# 64 bytes from 223.5.5.5... (китайский DNS быстрее ~50ms)
```

### Скрипт восстановления для pro

```bash
#!/bin/bash
# На pro: ZTE первым, Wi-Fi локально, utun погашены
SSH_KEY=~/.ssh/id_ed25519_headless
PRO_IP=192.168.103.70

ssh -i $SSH_KEY admin@$PRO_IP "
  # Проверка порядка
  networksetup -listnetworkserviceorder | grep -q '(1) ZTE Mobile Broadband' || \\
    sudo networksetup -ordernetworkservices 'ZTE Mobile Broadband' Wi-Fi
  
  # Остановка VPN
  scutil --nc stop 'Shadowrocket' 2>/dev/null
  scutil --nc stop 'Happ' 2>/dev/null
  
  # Гашение utun
  for iface in utun0 utun1 utun2 utun3 utun4 utun5 utun9; do
    sudo ifconfig \$iface down 2>/dev/null
  done
"
```

### Декларативный подход YAML + скрипт

В `~/Network/` на обоих Mac:
- `desired_state.yaml` — YAML-описание желаемого состояния (порядок сервисов, default route, DNS, VPN)
- `apply_network_state.sh` — скрипт аудита + восстановления

Скрипт делает: проверяет каждое условие → если не совпадает → исправляет. Запуск по SSH с dispo или локально на pro.

## Важное наблюдение
Happ и Shadowrocket остаются в списке NC даже после `scutil --nc stop`:
```
scutil --nc list
# * (Disconnected) ... "Shadowrocket"
# * (Disconnected) ... "Happ"
```
`scutil --nc remove "Happ"` — НЕ СУЩЕСТВУЕТ в macOS. Удаление VPN профиля — только через GUI System Settings → Network, или `networksetup -removenetworkservice`.
