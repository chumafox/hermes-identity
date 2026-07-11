# Sing-box TUN Split-Default на macOS

**Проблема:** Sing-box в TUN-режиме (`auto_route: true`, `strict_route: true`, stack gvisor) не всегда перехватывает трафик для определённых IP. Go-бинарники (agy, gh, terraform) уходят через en0/Wi-Fi напрямую — `i/o timeout`.

**Диагностика:** `route -n get 172.217.216.95` показывает `interface: en0` вместо `utun9`.

## Split-default (решение)

0.0.0.0/1 + 128.0.0.0/1 покрывает все IPv4-адреса без трогания LAN.

### Временный (живёт пока TUN поднят)
```bash
sudo route -n add -net 0.0.0.0/1 -interface utun9
sudo route -n add -net 128.0.0.0/1 -interface utun9
```

Проверка: `route -n get 172.217.216.95` → `interface: utun9`

### Permanent (в конфиг sing-box)
```json
{
  "type": "tun",
  "interface_name": "utun9",
  "inet4_address": "172.19.0.1/30",
  "auto_route": true,
  "strict_route": true,
  "stack": "gvisor",
  "route_address": [
    "0.0.0.0/1",
    "128.0.0.0/1"
  ],
  "route_exclude_address": [
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "224.0.0.0/4",
    "240.0.0.0/4"
  ],
  "sniff": true,
  "sniff_override_destination": true
}
```

### Альтернатива: FakeIP (DNS-уровень)
```json
"dns": {
  "servers": [{ "tag": "dns_fakeip", "address": "fakeip" }],
  "rules": [{ "outbound": "any", "server": "dns_fakeip" }],
  "fakeip": { "enabled": true, "inet4_range": "198.18.0.0/15" },
  "strategy": "ipv4_only"
}
```

## Почему auto_route не срабатывает
- gvisor не создаёт правильные маршруты на Darwin
- Конкуренция с bridge0/en0
- `strict_route: true` может конфликтовать с системным firewall

## Верификация
```bash
# Проверить маршрут конкретного IP
route -n get 172.217.216.95
# → interface: utun9

# Проверить, что Google доступен
curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" https://oauth2.googleapis.com/token
# → 404 (не таймаут)

# Проверить через TUN нет SYN на Wi-Fi
sudo tcpdump -ni en0 'host 172.217.216.95 and tcp port 443'
# → тишина (пакетов нет)
```
